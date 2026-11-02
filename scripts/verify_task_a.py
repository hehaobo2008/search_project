import json
import os
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORPUS = os.environ.get("HCS_CORPUS_DIR", os.path.join(ROOT, "corpus"))
REPORTS = os.environ.get("HCS_REPORTS_DIR", os.path.join(ROOT, "reports"))
os.makedirs(REPORTS, exist_ok=True)


def load_jsonl(name):
    return [json.loads(line) for line in open(os.path.join(CORPUS, name), encoding="utf-8")]


class ArticleIndex:
    def __init__(self, docs, articles):
        self.docs = {d["doc_id"]: d for d in docs}
        self.articles = articles

    def get(self, doc_id, version_id, number):
        doc = self.docs.get(doc_id)
        if doc is None:
            return "doc_not_found", None
        stored_version = doc.get("version_id")
        if not stored_version:
            return "version_unknown", None
        if version_id != stored_version:
            available = sorted({a["version_id"] for a in self.articles if a["doc_id"] == doc_id})
            return "version_pending", {"requested": version_id, "available": available}
        matches = [a for a in self.articles
                   if a["doc_id"] == doc_id and a["version_id"] == version_id
                   and a["article_num"] == number]
        if not matches:
            return "article_not_found", None
        if len(matches) > 1:
            return "ambiguous_article", {"count": len(matches)}
        art = matches[0]
        full_text = doc.get("full_text", "")
        if full_text[art["start"]:art["end"]] != art["text"]:
            return "locator_mismatch", art
        return "ok", art


def main():
    manifest = json.load(open(os.path.join(CORPUS, "docs_manifest.json"), encoding="utf-8"))
    articles = load_jsonl("articles.jsonl")
    relations = load_jsonl("relations.jsonl")
    docs = manifest["documents"]
    texts = {d["doc_id"]: open(os.path.join(CORPUS, "text_%s.txt" % d["doc_id"]), encoding="utf-8").read()
             for d in docs}
    for d in docs:
        d["full_text"] = texts[d["doc_id"]]
    index = ArticleIndex(docs, articles)

    cases = []

    def case(cid, name, ok, detail):
        cases.append({"id": cid, "name": name, "status": "PASS" if ok else "FAIL", "detail": detail})

    def get_art(doc_id, number):
        status, art = index.get(doc_id, {
            "rail_quality": "amended_2021_12_23",
            "construction_quality": "revised_2019_04_23",
        }[doc_id], number)
        return status, art

    # T01 文档身份
    ids = {d["doc_id"] for d in docs}
    shared = any(d.get("shared_source_file_with") for d in docs)
    distinct_files = len({d["file"] for d in docs})
    case("T01", "文档身份与共页分离", ids == {"rail_quality", "construction_quality", "rail_quality_amendment"}
         and shared and distinct_files == 2,
         "documents=%d distinct_source_files=%d shared_page=%s" % (len(docs), distinct_files, shared))

    # T02 条款切分连续性
    a_nums = sorted(a["article_num"] for a in articles if a["doc_id"] == "rail_quality")
    b_nums = sorted(a["article_num"] for a in articles if a["doc_id"] == "construction_quality")
    case("T02", "A/B 条号连续且边界完整", a_nums == list(range(1, 76)) and b_nums == list(range(1, 83)),
         "A=%d..%d(%d条) B=%d..%d(%d条)" % (a_nums[0], a_nums[-1], len(a_nums), b_nums[0], b_nums[-1], len(b_nums)))

    # T03 偏移回跳与锚点
    bad_span = [a["article_id"] for a in articles if not a["span_check"]]
    bad_hash = [a["article_id"] for a in articles
                if a["sha256"] != __import__("hashlib").sha256(a["text"].encode("utf-8")).hexdigest()]
    page_missing = [(a["article_id"], a["pdf_page_start"]) for a in articles
                    if a["doc_id"] in ("rail_quality", "construction_quality") and a["pdf_page_start"] is None]
    case("T03", "原文偏移回跳与哈希", not bad_span and not bad_hash,
         "span_fail=%d hash_fail=%d pdf_page_missing=%d" % (len(bad_span), len(bad_hash), len(page_missing)))

    # T04 A2
    status, a2 = get_art("rail_quality", 2)
    case("T04", "A第2条范围条款", status == "ok" and "适用本规定" in a2["text"],
         "%s pdf_page=%s" % (status, a2["pdf_page_start"] if a2 else None))

    # T05 A30
    status, a30 = get_art("rail_quality", 30)
    keywords = ["试块", "监督", "专人签字", "签认"]
    hit = [k for k in keywords if a30 and k in a30["text"]]
    case("T05", "A第30条检测/取样/签认", status == "ok" and set(hit) == set(keywords)
         and a30["para_count"] == 2 and a30["pdf_page_start"] == 9,
         "status=%s keywords=%s paras=%s pdf_page=%s" % (
             status, hit, a30["para_count"] if a30 else None, a30["pdf_page_start"] if a30 else None))

    # T06 A66 -> B65
    status, a66 = get_art("rail_quality", 66)
    a66_edges = [r for r in relations
                 if r["source"]["article_id"] == "rail_quality:art-66"
                 and r["relation_type"] == "explicit_article"]
    ok66 = (status == "ok" and len(a66_edges) == 1
            and a66_edges[0]["target"]["doc_id"] == "construction_quality"
            and a66_edges[0]["target"]["article_no"] == "第六十五条"
            and a66_edges[0]["target"]["version_id"] == "revised_2019_04_23")
    case("T06", "A66→B65 显式条款引用与正确版本", ok66,
         "status=%s edges=%d target=%s version=%s" % (
             status, len(a66_edges),
             a66_edges[0]["target"]["article_no"] if a66_edges else None,
             a66_edges[0]["target"]["version_id"] if a66_edges else None))

    # T07 B29/B31/B65 与 B31 页位
    status29, b29 = get_art("construction_quality", 29)
    status31, b31 = get_art("construction_quality", 31)
    status65, b65 = get_art("construction_quality", 65)
    ok_b = (status29 == "ok" and status31 == "ok" and status65 == "ok"
            and "专人签字" in b29["text"] and "监督下现场取样" in b31["text"]
            and "10万元以上20万元以下" in b65["text"]
            and b29["pdf_page_start"] == 7 and b31["pdf_page_start"] == 7
            and b31["pdf_cross_page"] is False and b65["pdf_page_start"] == 16)
    case("T07", "B29/B31/B65 原文与页锚点", ok_b,
         "B29 p%s B31 p%s B65 p%s" % (b29["pdf_page_start"], b31["pdf_page_start"], b65["pdf_page_start"]))

    # T07b B31 页位更正（按实际PDF第7页更正，保留旧记录与原因）
    b_doc = next(d for d in docs if d["doc_id"] == "construction_quality")
    legacy = [r for r in b_doc.get("legacy_records", []) if r["record_id"] == "B31-page"]
    correction = b31.get("page_record_correction", {})
    corrected_ok = (b31["pdf_page_start"] == 7 and b31["pdf_cross_page"] is False
                    and bool(legacy) and legacy[0]["status"] == "superseded"
                    and correction.get("status") == "corrected"
                    and "第7页" in correction.get("actual", ""))
    case("T07b", "B31按实际PDF第7页更正并保留旧记录", corrected_ok,
         "page=%s cross=%s legacy=%s correction=%s" % (
             b31["pdf_page_start"], b31["pdf_cross_page"],
             legacy[0]["status"] if legacy else None, correction.get("status")))

    # T08 C 修改关系
    amend = [r for r in relations if r["relation_type"] == "amendment"]
    amend_targets = {(r["target"]["article_no"] if r["target"] else None) for r in amend}
    c_articles = [a for a in articles if a["doc_id"] == "rail_quality_amendment"]
    ok_c = ({"第六十九条", "第七十条", None} <= amend_targets and len(amend) == 3 and not c_articles)
    case("T08", "C修改与重新公布关系", ok_c,
         "amendment=%d targets=%s C_articles=%d" % (len(amend), sorted(str(t) for t in amend_targets), len(c_articles)))

    # T09 负例：A30 不得产生显式边到 B29/B31
    a30_b_edges = [r for r in relations
                   if r["source"]["article_id"] == "rail_quality:art-30"
                   and r["relation_type"].startswith("explicit")
                   and r["target"] and r["target"]["doc_id"] == "construction_quality"]
    a30_topic = [r for r in relations
                 if r["source"]["article_id"] == "rail_quality:art-30"
                 and r["relation_type"] == "topic_related"
                 and r["target"] and r["target"]["article_no"] in ("第二十九条", "第三十一条")]
    case("T09", "负例：A30与B29/B31仅主题相关", not a30_b_edges and len(a30_topic) == 2
         and all(r["review_status"] == "pending_review" for r in a30_topic),
         "explicit_edges=%d topic_edges=%d" % (len(a30_b_edges), len(a30_topic)))

    # T10 负例：A1→B 文件级，不升级到条款
    a1_doc_edges = [r for r in relations
                    if r["source"]["article_id"] == "rail_quality:art-1"
                    and r["relation_type"] == "explicit_document"
                    and (r["target"] is None or r["target"]["doc_id"] == "construction_quality")]
    a1_article_edges = [r for r in relations
                        if r["source"]["article_id"] == "rail_quality:art-1"
                        and r["relation_type"] == "explicit_article"]
    b_doc_edges = [r for r in a1_doc_edges if r["target"] is None and "建设工程质量管理条例" in r["evidence_text"]]
    case("T10", "负例：A1→B 仅文件级不生成条款边", bool(b_doc_edges) and not a1_article_edges,
         "A1文件级B边=%d A1条款级边=%d" % (len(b_doc_edges), len(a1_article_edges)))

    # T11 关系目标完整性
    article_keys = {(a["doc_id"], a["version_id"], a["article_no"]) for a in articles}
    dangling = []
    for r in relations:
        if r["target_kind"] != "in_corpus_article":
            continue
        if r["target"] is None:
            dangling.append(r["relation_id"])
            continue
        key = (r["target"]["doc_id"], r["target"]["version_id"], r["target"]["article_no"])
        if key not in article_keys:
            dangling.append(r["relation_id"])
    case("T11", "显式关系目标无悬空边", not dangling, "dangling=%d %s" % (len(dangling), dangling))

    # T12 版本守卫：仅2017版时请求2019版
    synthetic_docs = json.loads(json.dumps(docs))
    synthetic_articles = json.loads(json.dumps(articles))
    for d in synthetic_docs:
        if d["doc_id"] == "construction_quality":
            d["version_id"] = "revised_2017_10_07"
    for a in synthetic_articles:
        if a["doc_id"] == "construction_quality":
            a["version_id"] = "revised_2017_10_07"
    guard_index = ArticleIndex(synthetic_docs, synthetic_articles)
    st_guard, payload = guard_index.get("construction_quality", "revised_2019_04_23", 65)
    case("T12", "版本守卫：2017副本不得静默替代2019", st_guard == "version_pending",
         "status=%s available=%s" % (st_guard, payload["available"] if payload else None))

    # T13 故障用例（合成，单独标记）
    st_missing, _ = index.get("construction_quality", "revised_2019_04_23", 99)
    dup_articles = json.loads(json.dumps(articles)) + [json.loads(json.dumps(b31))]
    st_dup, _ = ArticleIndex(docs, dup_articles).get("construction_quality", "revised_2019_04_23", 31)
    nover_docs = json.loads(json.dumps(docs))
    for d in nover_docs:
        if d["doc_id"] == "construction_quality":
            d["version_id"] = None
    st_nover, _ = ArticleIndex(nover_docs, articles).get("construction_quality", "revised_2019_04_23", 31)
    tampered_articles = json.loads(json.dumps(articles))
    for a in tampered_articles:
        if a["article_id"] == "construction_quality:art-65":
            a["text"] = a["text"] + "（篡改测试）"
    st_tamper, _ = ArticleIndex(docs, tampered_articles).get("construction_quality", "revised_2019_04_23", 65)
    fault_ok = (st_missing == "article_not_found" and st_dup == "ambiguous_article"
                and st_nover == "version_unknown" and st_tamper == "locator_mismatch")
    case("T13", "故障用例：缺条/重复/缺版本/错位", fault_ok,
         "missing=%s duplicate=%s no_version=%s tampered=%s" % (st_missing, st_dup, st_nover, st_tamper))

    # T14 主题相关不进入显式补证
    topic = [r for r in relations if r["relation_type"] == "topic_related"]
    case("T14", "主题相关与显式引用隔离", len(topic) == 2
         and all(not r["source_method"].startswith("rule_explicit") for r in topic)
         and all(r["review_status"] == "pending_review" for r in topic),
         "topic_related=%d" % len(topic))

    # T15 C 不重复导入实体规则
    c_in_index = [a for a in articles if a["doc_id"] == "rail_quality_amendment"]
    c_edge = [r for r in relations if r["source"]["doc_id"] == "rail_quality_amendment"]
    case("T15", "C与A共页去重", not c_in_index and len(c_edge) == 3,
         "C_indexed_articles=%d C_edges=%d" % (len(c_in_index), len(c_edge)))

    passed = sum(1 for c in cases if c["status"] == "PASS")
    failed = sum(1 for c in cases if c["status"] == "FAIL")
    observed = sum(1 for c in cases if c["status"] == "OBSERVED_MISMATCH")
    human_items = [
        ("H01", "A第2条与交通运输部规范PDF物理第1页的视觉一致性"),
        ("H02", "A第30条与规范PDF物理第9页的视觉一致性（两款完整、签字主体与签认对象不混同）"),
        ("H03", "A第66条与规范PDF物理第22页的视觉一致性（显式引用措辞）"),
        ("H04", "B第29条与中科院副本PDF物理第7页的视觉一致性"),
        ("H05", "B第31条位置：自动文本层仅第7页，清单记录为续至第8页，冲突待视觉确认"),
        ("H06", "B第65条与中科院副本PDF物理第16页的视觉一致性"),
        ("H07", "C修改决定全文：修改第69条、增设第70条、条文序号调整与重新公布"),
        ("H08", "引用四分法语义复核：A1→B文件级、A30与B29/B31主题相关、A66→B65显式、C→A修改"),
    ]

    result = {
        "run_id": "taskA-" + datetime.now().strftime("%Y%m%dT%H%M%S%z"),
        "generated_at": datetime.now().astimezone().isoformat(),
        "scope": "任务A：中文条款切分、原文定位、引用四分法与版本/故障校验",
        "cases": cases,
        "summary": {
            "auto_cases": len(cases),
            "passed": passed,
            "failed": failed,
            "observed_mismatch": 0,
            "corrected_records": 1 if corrected_ok else 0,
            "human_review_pending": len(human_items),
        },
        "human_review_items": [{"id": i, "item": t, "status": "pending"} for i, t in human_items],
        "gate": "NOT_PASSED_PENDING_HUMAN_REVIEW" if (failed == 0) else "NOT_PASSED_AUTO_FAILURES",
        "gate_note": "自动用例不等同人工复核；任务A闸门须由人工核对H01-H06后才可判定。",
    }

    with open(os.path.join(REPORTS, "task_a_result.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    lines = [
        "# 任务A 自动校验报告",
        "",
        "- run_id：%s" % result["run_id"],
        "- 生成时间：%s" % result["generated_at"],
        "- 范围：%s" % result["scope"],
        "- 自动用例：%d，通过：%d，失败：%d，已更正记录：%d" % (
            len(cases), passed, failed, 1 if corrected_ok else 0),
        "- 人工核验待办：%d 项" % len(human_items),
        "- 闸门：%s" % result["gate"],
        "",
        "| 用例 | 名称 | 状态 | 证据 |",
        "|---|---|---|---|",
    ]
    for c in cases:
        lines.append("| %s | %s | %s | %s |" % (c["id"], c["name"], c["status"], c["detail"]))
    lines += ["", "## 人工核验待办（不计入自动通过）", ""]
    for i, t in human_items:
        lines.append("- [ ] %s %s" % (i, t))
    lines += ["", "> 结论：自动链路通过不等于闸门通过；H01-H06 完成并由人工签字后，任务A才可判定通过。"]

    with open(os.path.join(REPORTS, "task_a_report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    for c in cases:
        print("%-4s %-8s %s | %s" % (c["id"], c["status"], c["name"], c["detail"]))
    print("=" * 60)
    print("auto=%d pass=%d fail=%d observed_mismatch=%d human_pending=%d" % (
        len(cases), passed, failed, observed, len(human_items)))
    print("GATE:", result["gate"])
    sys.exit(0 if failed == 0 else 2)


if __name__ == "__main__":
    main()