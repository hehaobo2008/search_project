import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORPUS = os.environ.get("HCS_CORPUS_DIR", os.path.join(ROOT, "corpus"))
VERSION_PINS = os.environ.get("HCS_VERSION_PINS", os.path.join(ROOT, "config", "version_pins.json"))

TITLE_TO_DOC = {
    "建设工程质量管理条例": "construction_quality",
    "铁路建设工程质量监督管理规定": "rail_quality",
}
CITATION_RE = re.compile(r"《([^》]{2,40})》\s*(?:第([一二三四五六七八九十百零]+)条)?")
MODIFY_RE = re.compile(r"将第([一二三四五六七八九十百零]+)条修改为")
INSERT_RE = re.compile(r"增加一条，作为第([一二三四五六七八九十百零]+)条")

sys.path.insert(0, os.path.join(ROOT, "scripts"))
from build_corpus import cn_to_int  # noqa: E402


def load_articles():
    return [json.loads(line) for line in open(os.path.join(CORPUS, "articles.jsonl"), encoding="utf-8")]


def load_docs():
    manifest = json.load(open(os.path.join(CORPUS, "docs_manifest.json"), encoding="utf-8"))
    return manifest["documents"]


def load_version_pins(path):
    """从独立配置读取版本锁定；缺失即返回空锁定，由解析层对多版本报歧义。"""
    if not os.path.exists(path):
        return {}, {"path": path, "status": "missing_config"}
    payload = json.load(open(path, encoding="utf-8"))
    pins = payload.get("pins", {})
    if not isinstance(pins, dict):
        return {}, {"path": path, "status": "invalid_config"}
    clean = {k: v for k, v in pins.items() if isinstance(k, str) and isinstance(v, str)}
    return clean, {"path": path, "status": "loaded", "schema_version": payload.get("schema_version")}


def resolve_target_version(doc_id, docs, pinned_versions):
    """显式锁定版本；未锁定且存在多版本时返回歧义，不自行选择。"""
    entries = [d for d in docs if d["doc_id"] == doc_id]
    versions = sorted({d.get("version_id") for d in entries if d.get("version_id")})
    if not versions:
        return None, "missing_version"
    wanted = pinned_versions.get(doc_id)
    if wanted:
        if wanted in versions:
            return wanted, "pinned"
        return None, "pinned_version_missing"
    if len(versions) == 1:
        return versions[0], "single_version"
    return None, "ambiguous_version"


def extract_relations(articles, docs, c_text, pinned_versions):
    by_id = {(a["doc_id"], a["version_id"], a["article_num"]): a for a in articles}
    relations = []
    diagnostics = []

    def add(source_art, target_art, target_kind, relation_type, evidence, start, end,
            method, note, target_version_id=None, target_version_status="n/a",
            target_resolution=None):
        rid = "rel-%03d" % (len(relations) + 1)
        target = None
        if target_art is not None:
            target = {
                "doc_id": target_art["doc_id"],
                "version_id": target_art["version_id"],
                "article_id": target_art["article_id"],
                "article_no": target_art["article_no"],
            }
            target_version_id = target_art["version_id"]
            target_version_status = "resolved"
        source_scope = ("amendment_full_text_offset" if source_art["article_id"] is None
                        else ("article_absolute_offset" if start is not None else "article_identity_only"))
        source_article_span = ([source_art["start"], source_art["end"]]
                               if source_art["article_id"] is not None else None)
        relations.append({
            "relation_id": rid,
            "source": {
                "doc_id": source_art["doc_id"],
                "version_id": source_art["version_id"],
                "article_id": source_art["article_id"],
                "article_no": source_art["article_no"],
            },
            "source_article_span": source_article_span,
            "source_scope": source_scope,
            "target": target,
            "target_kind": target_kind,
            "target_version_id": target_version_id,
            "target_version_status": target_version_status,
            "target_resolution": target_resolution,
            "relation_type": relation_type,
            "evidence_text": evidence,
            "evidence_span": [start, end],
            "source_method": method,
            "review_status": "pending_review",
            "note": note,
        })
        if target_version_status in ("ambiguous_version", "pinned_version_missing", "missing_version"):
            diagnostics.append({
                "relation_id": rid,
                "source": source_art.get("article_id"),
                "target_doc": (target or {}).get("doc_id") or (
                    TITLE_TO_DOC.get(evidence) if evidence else None),
                "target_version_status": target_version_status,
                "note": "目标版本未唯一确定，未生成可用边，待人工确认",
            })
        return rid

    # 1) 显式引用
    for art in articles:
        if art["doc_id"] == "rail_quality_amendment":
            continue
        for m in CITATION_RE.finditer(art["text"]):
            title = m.group(1)
            cn_no = m.group(2)
            target_doc = TITLE_TO_DOC.get(title)
            evidence_start = art["start"] + m.start()
            evidence_end = art["start"] + m.end()
            evidence = m.group(0)
            if target_doc is None:
                add(art, None, "external_document", "explicit_document",
                    evidence, evidence_start, evidence_end, "rule_explicit_citation",
                    "书名号目标不在本批最小语料库内（%s），不生成库内边，不参与补证" % title,
                    target_version_status="external")
                continue
            version_id, version_status = resolve_target_version(target_doc, docs, pinned_versions)
            if version_id is None:
                add(art, None, "in_corpus_document", "explicit_document",
                    evidence, evidence_start, evidence_end, "rule_explicit_citation",
                    "目标文档版本状态为 %s，未生成可用边，待人工确认" % version_status,
                    target_version_id=None, target_version_status=version_status,
                    target_resolution="resolve_target_version:%s" % version_status)
                continue
            if cn_no is None:
                add(art, None, "in_corpus_document", "explicit_document",
                    evidence, evidence_start, evidence_end, "rule_explicit_citation",
                    "文件级依据引用；未自动展开为其下任何条款的边",
                    target_version_id=version_id, target_version_status="pinned",
                    target_resolution="resolve_target_version:%s" % version_status)
                continue
            number = cn_to_int(cn_no)
            target_art = by_id.get((target_doc, version_id, number))
            if target_art is None:
                add(art, None, "in_corpus_document", "explicit_article",
                    evidence, evidence_start, evidence_end, "rule_explicit_citation",
                    "显式条号引用但目标条在锁定版本中不存在，标待核验，不生成可用边",
                    target_version_id=version_id, target_version_status="target_article_missing",
                    target_resolution="resolve_target_version:%s" % version_status)
            else:
                add(art, target_art, "in_corpus_article", "explicit_article",
                    evidence, evidence_start, evidence_end, "rule_explicit_citation",
                    "原文明示条款引用；自动抽取结果仍须人工复核",
                    target_resolution="resolve_target_version:%s" % version_status)

    # 2) 修改/重新公布关系：C -> A
    c_doc = {
        "doc_id": "rail_quality_amendment",
        "version_id": "2021_order_35",
        "article_id": None,
        "article_no": None,
    }
    a_version, a_status = resolve_target_version("rail_quality", docs, pinned_versions)
    for pattern, label, note in [
        (MODIFY_RE, "将第%s条修改为", "修改关系；目标为2021修正后重新公布的A条文"),
        (INSERT_RE, "增加一条，作为第%s条", "新增条文关系；2021修正新增A条文"),
    ]:
        for m in pattern.finditer(c_text):
            number = cn_to_int(m.group(1))
            target_art = by_id.get(("rail_quality", a_version, number)) if a_version else None
            add(c_doc, target_art, "in_corpus_article", "amendment",
                label % m.group(1), m.start(), m.end(), "rule_amendment",
                note if target_art else "修改关系目标条或版本未确认，标待核验",
                target_version_id=a_version,
                target_version_status="resolved" if target_art else a_status)
    repub = "根据本决定作相应修改并对条文序号作相应调整，重新公布"
    repub_start = c_text.find(repub)
    add(c_doc, None, "in_corpus_document", "amendment",
        repub, repub_start, repub_start + len(repub) if repub_start >= 0 else None,
        "rule_amendment", "C与A的重新公布关系；不生成材料检测实体规则",
        target_version_id=a_version,
        target_version_status="pinned" if a_version else a_status,
        target_resolution="resolve_target_version:%s" % a_status)

    # 3) 主题相关：人工标注，不伪装成显式引用
    topic_pairs = [
        (("rail_quality", 30), ("construction_quality", 29)),
        (("rail_quality", 30), ("construction_quality", 31)),
    ]
    for (src_doc, src_num), (tgt_doc, tgt_num) in topic_pairs:
        src_version, src_status = resolve_target_version(src_doc, docs, pinned_versions)
        tgt_version, tgt_status = resolve_target_version(tgt_doc, docs, pinned_versions)
        src = by_id.get((src_doc, src_version, src_num)) if src_version else None
        tgt = by_id.get((tgt_doc, tgt_version, tgt_num)) if tgt_version else None
        if src is None or tgt is None:
            diagnostics.append({
                "relation_id": None,
                "source": "%s:art-%d" % (src_doc, src_num),
                "target_doc": tgt_doc,
                "target_version_status": tgt_status if tgt is None else src_status,
                "note": "主题相关标注的目标版本或条款未唯一确定，未生成边",
            })
            continue
        add(src, tgt, "in_corpus_article", "topic_related",
            "人工标注：试块送检、监督取样与资料签字主题相近，非原文明示引用",
            None, None, "curated_topic_match",
            "仅作主题相关候选，展示时须标待人工核对；不得计入显式引用补证组",
            target_resolution="resolve_target_version:%s" % tgt_status)

    return relations, diagnostics


def main():
    articles = load_articles()
    docs = load_docs()
    c_text = open(os.path.join(CORPUS, "text_rail_quality_amendment.txt"), encoding="utf-8").read()
    pinned_versions, pins_meta = load_version_pins(VERSION_PINS)
    relations, diagnostics = extract_relations(articles, docs, c_text, pinned_versions)

    with open(os.path.join(CORPUS, "relations.jsonl"), "w", encoding="utf-8") as f:
        for rel in relations:
            f.write(json.dumps(rel, ensure_ascii=False) + "\n")
    with open(os.path.join(CORPUS, "relation_diagnostics.json"), "w", encoding="utf-8") as f:
        json.dump({
            "version_pins_source": pins_meta,
            "pinned_versions": pinned_versions,
            "diagnostics": diagnostics,
        }, f, ensure_ascii=False, indent=2)

    counts = {}
    for rel in relations:
        counts[rel["relation_type"]] = counts.get(rel["relation_type"], 0) + 1
    print("version_pins=%s source=%s" % (pins_meta["status"], pins_meta["path"]))
    print("relations=%d diagnostics=%d" % (len(relations), len(diagnostics)))
    for k in sorted(counts):
        print("  %s=%d" % (k, counts[k]))
    print("explicit_article_edges:")
    for rel in relations:
        if rel["relation_type"] == "explicit_article" and rel["target"]:
            print("  %s %s -> %s %s [%s]" % (
                rel["source"]["article_id"], rel["source"]["article_no"],
                rel["target"]["doc_id"], rel["target"]["article_no"],
                rel["evidence_text"]))
    print("version_status_counts:")
    status_counts = {}
    for rel in relations:
        status_counts[rel["target_version_status"]] = status_counts.get(rel["target_version_status"], 0) + 1
    for k in sorted(status_counts):
        print("  %s=%d" % (k, status_counts[k]))
    if diagnostics:
        for d in diagnostics:
            print("  PENDING", d["target_version_status"], d["note"])
    # 正式单版本语料不应出现版本歧义；出现则停止，等待人工确认
    blocking = [d for d in diagnostics if d["target_version_status"] == "ambiguous_version"]
    sys.exit(2 if blocking else 0)


if __name__ == "__main__":
    main()