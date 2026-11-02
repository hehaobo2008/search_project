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
METHODS = ("bm25_top7", "dense_top7", "hybrid_top7", "hybrid_top5_supplement", "hybrid_top5")


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
        self.last_supplement_ms = 0.0

    def _cache_key(self):
        model_path = os.path.join(ROOT, "work", "models", "bge-small-zh-v1.5", "onnx", "model.onnx")
        model_hash = hashlib.sha256(open(model_path, "rb").read()).hexdigest()
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

    def _item(self, idx, rank, score, lex_scores, sem_scores, lex_order, sem_order, rrf):
        art = self.articles[idx]
        return {
            "rank": rank,
            "article_id": art["article_id"],
            "doc_id": art["doc_id"],
            "version_id": art["version_id"],
            "article_no": art["article_no"],
            "chapter": art["chapter"],
            "text": art["text"],
            "score": round(float(score), 6),
            "lex_score": round(float(lex_scores[idx]), 4),
            "sem_score": round(float(sem_scores[idx]), 4),
            "rrf_score": round(float(rrf.get(idx, 0.0)), 6),
            "lex_rank": lex_order[idx] + 1,
            "sem_rank": sem_order[idx] + 1,
            "anchor": art["anchor"],
            "source_url": art["source_url"],
            "sha256": art["sha256"],
        }

    def retrieve(self, question):
        """只接收自然语言问题，返回四路排序与共享耗时分解。"""
        started = time.time()
        t = {}
        normalized = normalize_query(question)
        t0 = time.time()
        q_tokens = tokenize(normalized)
        t["tokenize_ms"] = round((time.time() - t0) * 1000, 3)

        t0 = time.time()
        lex_scores = self.bm25.get_scores(q_tokens)
        t["bm25_ms"] = round((time.time() - t0) * 1000, 3)
        lex_order = sorted(range(len(self.articles)),
                           key=lambda i: (-lex_scores[i], self.articles[i]["article_id"]))
        lex_rank_map = {idx: rank for rank, idx in enumerate(lex_order)}

        t0 = time.time()
        qv = self.embedder.encode([normalized], is_query=True)[0]
        t["embed_ms"] = round((time.time() - t0) * 1000, 3)

        t0 = time.time()
        sem_scores = self.doc_vectors @ qv
        t["dense_ms"] = round((time.time() - t0) * 1000, 3)
        sem_order = sorted(range(len(self.articles)),
                           key=lambda i: (-sem_scores[i], self.articles[i]["article_id"]))
        sem_rank_map = {idx: rank for rank, idx in enumerate(sem_order)}

        t0 = time.time()
        rrf = {}
        for rank, idx in enumerate(lex_order[:self.top_candidates], start=1):
            rrf[idx] = rrf.get(idx, 0.0) + 1.0 / (self.rrf_k + rank)
        for rank, idx in enumerate(sem_order[:self.top_candidates], start=1):
            rrf[idx] = rrf.get(idx, 0.0) + 1.0 / (self.rrf_k + rank)
        hybrid_order = sorted(rrf, key=lambda i: (-rrf[i], self.articles[i]["article_id"]))
        t["fusion_ms"] = round((time.time() - t0) * 1000, 3)

        def build(order, score_getter):
            return [self._item(idx, rank, score_getter(idx), lex_scores, sem_scores,
                               lex_rank_map, sem_rank_map, rrf)
                    for rank, idx in enumerate(order, start=1)]

        retrieval = {
            "question": question,
            "normalized_question": normalized,
            "bm25": build(lex_order, lambda i: lex_scores[i]),
            "dense": build(sem_order, lambda i: sem_scores[i]),
            "hybrid": build(hybrid_order, lambda i: rrf.get(i, 0.0)),
            "timings": t,
            "max_sem": float(sem_scores.max()),
        }
        t["total_search_ms"] = round((time.time() - started) * 1000, 3)
        self.last_max_sem = retrieval["max_sem"]
        self.last_search_ms = t["total_search_ms"]
        self.last_normalized_query = normalized
        self.last_timings = t
        return retrieval

    def _display(self, item):
        text = item["text"][:self.unit_char_budget]
        unit = dict(item)
        unit["full_chars"] = len(item["text"])
        unit["text"] = text
        unit["chars"] = len(text)
        unit["truncated"] = len(text) < len(item["text"])
        unit["relation"] = None
        return unit

    def _supplements(self, retrieval, max_extra=2):
        started = time.time()
        hybrid = retrieval["hybrid"]
        base5 = hybrid[:5]
        base_ids = {item["article_id"] for item in base5}
        seed_ids = {item["article_id"] for item in hybrid[:2]}
        ranked_ids = [item["article_id"] for item in hybrid]
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
            if target in base_ids or target not in ranked_ids or target not in candidate_limit:
                continue
            candidates.append((ranked_ids.index(target), rel))
        candidates.sort(key=lambda x: (x[0], x[1]["relation_id"]))
        extras = []
        seen = set()
        for idx, rel in candidates:
            if len(extras) >= max_extra:
                break
            item = hybrid[idx]
            if item["article_id"] in seen:
                continue
            seen.add(item["article_id"])
            unit = self._display(item)
            unit["relation"] = {
                "relation_type": rel["relation_type"],
                "source_article_id": rel["source"]["article_id"],
                "relation_id": rel["relation_id"],
                "evidence_text": rel["evidence_text"],
            }
            extras.append(unit)
        self.last_supplement_ms = round((time.time() - started) * 1000, 3)
        retrieval["timings"]["supplement_ms"] = self.last_supplement_ms
        return extras

    def method_units(self, retrieval, method):
        if method not in METHODS:
            raise ValueError("unknown method: %s" % method)
        if method == "bm25_top7":
            return [self._display(x) for x in retrieval["bm25"][:7]]
        if method == "dense_top7":
            return [self._display(x) for x in retrieval["dense"][:7]]
        if method == "hybrid_top7":
            return [self._display(x) for x in retrieval["hybrid"][:7]]
        if method == "hybrid_top5":
            return [self._display(x) for x in retrieval["hybrid"][:5]]
        if method == "hybrid_top5_supplement":
            base = [self._display(x) for x in retrieval["hybrid"][:5]]
            return base + self._supplements(retrieval)

    def assess_answerability(self, question):
        import jieba.posseg as pseg
        normalized = normalize_query(question)
        corpus_text = "".join(self.doc_texts)
        unknown = []
        for word, flag in pseg.cut(normalized):
            if len(word) < 2 or word in STOPWORDS:
                continue
            if not flag or flag[0] not in "nvg":
                continue
            if word not in corpus_text:
                unknown.append(word)
        unknown = sorted(set(unknown))
        max_sem = getattr(self, "last_max_sem", 0.0)
        decision = "refuse" if (len(unknown) >= 3 or (len(unknown) >= 1 and max_sem < 0.62)) else "answer"
        return {
            "unknown_terms": unknown,
            "unknown_count": len(unknown),
            "max_sem": round(max_sem, 4),
            "semantic_floor": 0.62,
            "decision": decision,
        }

    def version_check(self, question):
        years = re.findall(r"(20\d{2})\s*年?", question)
        if not years:
            return {"state": "not_applicable"}
        if "2015" in years and "铁路" in question:
            return {
                "state": "version_pending",
                "message": "当前索引锁定2021修正版；2015版第70条与2021版第70条内容不同，须人工核对旧版",
                "locked_versions": ["amended_2021_12_23"],
                "requested": "published_2015_03_12",
            }
        if "2017" in years and "条例" in question:
            return {
                "state": "version_pending",
                "message": "当前索引锁定2019第二次修订版；2017版未入索引，须人工核对旧版",
                "locked_versions": ["revised_2019_04_23"],
                "requested": "revised_2017_10_07",
            }
        return {"state": "unverified"}

    def inspect_relation(self, pair):
        src, tgt = pair
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
        if doc_level:
            return {"state": "explicit_document",
                    "message": "文件级依据引用，不自动指向目标文件的具体条款",
                    "relation_ids": [r["relation_id"] for r in doc_level]}
        return {"state": "no_relation", "message": "未找到已登记关系，不得硬连",
                "relation_ids": []}

    # 兼容旧调用
    def search(self, question):
        return self.retrieve(question)["hybrid"]

    def methods(self, question_or_retrieval):
        retrieval = question_or_retrieval if isinstance(question_or_retrieval, dict) \
            else self.retrieve(question_or_retrieval)
        return {method: self.method_units(retrieval, method) for method in METHODS}

    def supplemented(self, retrieval):
        if not isinstance(retrieval, dict):
            retrieval = self.retrieve(retrieval)
        return self.method_units(retrieval, "hybrid_top5_supplement")