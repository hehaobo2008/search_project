import hashlib
import json
import os
import re
import sys
import time

import jieba
import numpy as np
from rank_bm25 import BM25Okapi

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from bge_embedder import BgeEmbedder  # noqa: E402

CORPUS = os.path.join(ROOT, "corpus")
CACHE = os.path.join(ROOT, "work", "cache")
os.makedirs(CACHE, exist_ok=True)

PROTECT_RE = re.compile(
    r"第[一二三四五六七八九十百零]+[条章节]|《[^》]+》|"
    r"[0-9]+(?:\.[0-9]+)?%?|[A-Za-z]+")
STOPWORDS = {
    "的", "了", "和", "是", "在", "有", "由", "对", "为", "与", "及", "等", "或",
    "应当", "必须", "规定", "如何", "什么", "哪里", "怎么", "是否", "可以", "需要",
    "多少", "谁", "哪些", "应该", "怎样", "这个", "那个", "进行", "相关", "问题",
    "依据", "原文", "内容", "具体", "时候", "情况", "单位", "提到", "上位", "条款",
    "能否", "提前", "直接", "引用", "关系", "是不是", "送检",
}


def tokenize(text):
    tokens = []
    pos = 0
    for m in PROTECT_RE.finditer(text):
        tokens.extend(jieba.lcut_for_search(text[pos:m.start()]))
        tokens.append(m.group(0))
        pos = m.end()
    tokens.extend(jieba.lcut_for_search(text[pos:]))
    cleaned = []
    for token in tokens:
        token = token.strip()
        if not token or token in STOPWORDS:
            continue
        if len(token) == 1 and not re.match(r"[0-9A-Za-z%]", token):
            continue
        cleaned.append(token.lower())
    return cleaned


def int_to_cn(n):
    digits = "零一二三四五六七八九"
    if n < 10:
        return digits[n]
    if n < 20:
        return "十" + (digits[n % 10] if n % 10 else "")
    if n < 100:
        return digits[n // 10] + "十" + (digits[n % 10] if n % 10 else "")
    return str(n)


def normalize_query(text):
    text = re.sub(r"第(\d+)条", lambda m: "第%s条" % int_to_cn(int(m.group(1))), text)
    text = re.sub(r"第(\d+)章", lambda m: "第%s章" % int_to_cn(int(m.group(1))), text)
    return text


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class TaskBRetriever:
    def __init__(self, top_candidates=50, rrf_k=60, unit_char_budget=400):
        self.top_candidates = top_candidates
        self.rrf_k = rrf_k
        self.unit_char_budget = unit_char_budget
        all_articles = [json.loads(line) for line in open(
            os.path.join(CORPUS, "articles.jsonl"), encoding="utf-8")]
        self.articles = [a for a in all_articles
                         if a["doc_id"] in ("rail_quality", "construction_quality")]
        self.relations = [json.loads(line) for line in open(
            os.path.join(CORPUS, "relations.jsonl"), encoding="utf-8")]
        self.by_id = {a["article_id"]: a for a in self.articles}
        titles = {"rail_quality": "铁路建设工程质量监督管理规定",
                  "construction_quality": "建设工程质量管理条例"}
        self.doc_texts = []
        for art in self.articles:
            self.doc_texts.append("%s %s %s %s" % (
                titles[art["doc_id"]], art["chapter"], art["article_no"], art["text"]))
        self.tokens = [tokenize(t) for t in self.doc_texts]
        self.bm25 = BM25Okapi(self.tokens)
        self.embedder = BgeEmbedder()
        self.doc_vectors = self._load_or_build_vectors()
        self.embed_ms = 0.0

    def _cache_key(self):
        model_hash = hashlib.sha256(
            open(os.path.join(ROOT, "work", "models", "bge-small-zh-v1.5", "onnx", "model.onnx"),
                 "rb").read()).hexdigest()
        corpus_hash = sha256_text("".join(a["sha256"] for a in self.articles))
        return "%s_%s" % (model_hash[:16], corpus_hash[:16])

    def _load_or_build_vectors(self):
        path = os.path.join(CACHE, "bge_docs_%s.npz" % self._cache_key())
        if os.path.exists(path):
            data = np.load(path)
            if list(data["ids"]) == [a["article_id"] for a in self.articles]:
                self.vector_cache_hit = True
                return data["vectors"].astype(np.float32)
        started = time.time()
        vectors = self.embedder.encode(self.doc_texts)
        self.embed_ms = round((time.time() - started) * 1000, 1)
        np.savez_compressed(path, ids=np.array([a["article_id"] for a in self.articles]),
                            vectors=vectors)
        self.vector_cache_hit = False
        return vectors

    def embed_query(self, query):
        started = time.time()
        vector = self.embedder.encode([query], is_query=True)[0]
        self.query_embed_ms = round((time.time() - started) * 1000, 1)
        return vector

    def search(self, query):
        started = time.time()
        normalized = normalize_query(query)
        self.last_normalized_query = normalized
        q_tokens = tokenize(normalized)
        lex_scores = self.bm25.get_scores(q_tokens)
        lex_order = sorted(range(len(self.articles)), key=lambda i: (-lex_scores[i],
                                                                    self.articles[i]["article_id"]))
        qv = self.embed_query(query)
        sem_scores = self.doc_vectors @ qv
        sem_order = sorted(range(len(self.articles)), key=lambda i: (-sem_scores[i],
                                                                    self.articles[i]["article_id"]))
        rrf = {}
        for rank, idx in enumerate(lex_order[:self.top_candidates], start=1):
            rrf[idx] = rrf.get(idx, 0.0) + 1.0 / (self.rrf_k + rank)
        for rank, idx in enumerate(sem_order[:self.top_candidates], start=1):
            rrf[idx] = rrf.get(idx, 0.0) + 1.0 / (self.rrf_k + rank)
        ranked = sorted(rrf, key=lambda i: (-rrf[i], self.articles[i]["article_id"]))
        lex_rank_map = {idx: i + 1 for i, idx in enumerate(lex_order)}
        sem_rank_map = {idx: i + 1 for i, idx in enumerate(sem_order)}
        items = []
        for rank, idx in enumerate(ranked, start=1):
            art = self.articles[idx]
            items.append({
                "rank": rank,
                "article_id": art["article_id"],
                "doc_id": art["doc_id"],
                "version_id": art["version_id"],
                "article_no": art["article_no"],
                "chapter": art["chapter"],
                "text": art["text"],
                "score": round(rrf[idx], 6),
                "lex_score": round(float(lex_scores[idx]), 4),
                "sem_score": round(float(sem_scores[idx]), 4),
                "lex_rank": (lex_rank_map[idx] if idx in lex_order[:self.top_candidates] else None),
                "sem_rank": (sem_rank_map[idx] if idx in sem_order[:self.top_candidates] else None),
                "anchor": art["anchor"],
                "source_url": art["source_url"],
                "sha256": art["sha256"],
            })
        self.last_search_ms = round((time.time() - started) * 1000, 1)
        self.last_max_sem = float(sem_scores.max())
        return items

    def _display(self, text):
        clipped = text[:self.unit_char_budget]
        return clipped, len(clipped)

    def _unit(self, item, relation=None):
        display, chars = self._display(item["text"])
        return {
            "article_id": item["article_id"],
            "doc_id": item["doc_id"],
            "version_id": item["version_id"],
            "article_no": item["article_no"],
            "rank": item["rank"],
            "score": item["score"],
            "text": display,
            "chars": chars,
            "full_chars": len(item["text"]),
            "truncated": chars < len(item["text"]),
            "anchor": item["anchor"],
            "source_url": item["source_url"],
            "sha256": item["sha256"],
            "relation": relation,
        }

    def normal_top(self, ranked, k):
        return [self._unit(item) for item in ranked[:k]]

    def supplemented(self, ranked, max_extra=2):
        base5 = ranked[:5]
        base_ids = {item["article_id"] for item in base5}
        units = [self._unit(item) for item in base5]
        seed_ids = {item["article_id"] for item in ranked[:2]}
        ranked_ids = [item["article_id"] for item in ranked]
        candidate_limit = set(ranked_ids[:10])
        candidates = []
        for rel in self.relations:
            source = rel["source"]["article_id"]
            target = rel["target"]["article_id"] if rel.get("target") else None
            if source not in seed_ids or target is None:
                continue
            if rel["relation_type"] not in ("explicit_article", "amendment"):
                continue
            if rel["target_version_status"] != "resolved":
                continue
            if target in base_ids or target not in ranked_ids:
                continue
            if target not in candidate_limit:
                continue
            idx = ranked_ids.index(target)
            candidates.append((idx, rel))
        candidates.sort(key=lambda x: (x[0], x[1]["relation_id"]))
        seen = set()
        for idx, rel in candidates:
            if len(units) >= 5 + max_extra:
                break
            item = ranked[idx]
            if item["article_id"] in seen:
                continue
            seen.add(item["article_id"])
            units.append(self._unit(item, {
                "relation_type": rel["relation_type"],
                "source_article_id": rel["source"]["article_id"],
                "relation_id": rel["relation_id"],
                "evidence_text": rel["evidence_text"],
            }))
        return units

    def methods(self, ranked):
        return {
            "top5": self.normal_top(ranked, 5),
            "top7": self.normal_top(ranked, 7),
            "top5_supplement": self.supplemented(ranked),
        }

    def unknown_terms(self, query):
        import jieba.posseg as pseg
        normalized = normalize_query(query)
        corpus_text = "".join(self.doc_texts)
        words = []
        for word, flag in pseg.cut(normalized):
            if len(word) < 2 or word in STOPWORDS:
                continue
            if not flag or flag[0] not in "nvg":
                continue
            if word not in corpus_text:
                words.append(word)
        return sorted(set(words))

    def assess_answerability(self, query, min_unknown=2):
        unknown = self.unknown_terms(query)
        q_tokens = set(tokenize(query))
        doc_token_set = set()
        for tokens in self.tokens:
            doc_token_set.update(tokens)
        covered = len(q_tokens & doc_token_set) / max(1, len(q_tokens))
        max_sem = getattr(self, "last_max_sem", 0.0)
        decision = "refuse" if (len(unknown) >= 3 or (len(unknown) >= 1 and max_sem < 0.62)) else "answer"
        return {"unknown_terms": unknown, "unknown_count": len(unknown),
                "min_unknown": min_unknown, "semantic_floor": 0.62,
                "term_coverage": round(covered, 4),
                "max_sem": round(getattr(self, "last_max_sem", 0.0), 4),
                "decision": decision}

    def version_check(self, query):
        years = re.findall(r"(20\d{2})\s*年?", query)
        if not years:
            return {"state": "not_applicable"}
        if "2015" in years and "铁路" in query:
            return {
                "state": "version_pending",
                "message": "当前索引锁定2021修正版；2015版第70条与2021版第70条内容不同，须人工核对旧版",
                "locked_versions": ["amended_2021_12_23"],
                "requested": "published_2015_03_12",
            }
        if "2017" in years and "条例" in query:
            return {
                "state": "version_pending",
                "message": "当前索引锁定2019第二次修订版；2017版未入索引，须人工核对旧版",
                "locked_versions": ["revised_2019_04_23"],
                "requested": "revised_2017_10_07",
            }
        return {"state": "unverified"}

    def inspect_relation(self, pair):
        src, tgt = pair
        src_doc = src.split(":")[0]
        tgt_doc = tgt.split(":")[0]
        explicit = [r for r in self.relations
                    if r["source"]["article_id"] == src and r.get("target")
                    and r["target"]["article_id"] == tgt
                    and r["relation_type"] == "explicit_article"]
        if explicit:
            return {"state": "explicit_article", "message": "原文明示的条款级引用",
                    "relation_ids": [r["relation_id"] for r in explicit]}
        topic = [r for r in self.relations
                 if r["source"]["article_id"] == src and r.get("target")
                 and r["target"]["article_id"] == tgt
                 and r["relation_type"] == "topic_related"]
        if topic:
            return {"state": "topic_related", "message": "主题相关，不是原文明示引用，须人工核对",
                    "relation_ids": [r["relation_id"] for r in topic]}
        doc_level = [r for r in self.relations
                     if r["source"]["article_id"] == src
                     and r["relation_type"] == "explicit_document"
                     and r.get("target") is None and r.get("target_version_id")]
        if doc_level and src_doc == "rail_quality":
            return {"state": "explicit_document",
                    "message": "文件级依据引用，不自动指向目标文件的具体条款",
                    "relation_ids": [r["relation_id"] for r in doc_level]}
        return {"state": "no_relation", "message": "未找到已登记关系，不得硬连",
                "relation_ids": []}