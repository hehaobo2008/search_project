import hashlib
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUESTIONS = os.path.join(ROOT, "data", "task_b_eval30_questions.jsonl")
ARTICLES = os.path.join(ROOT, "corpus", "articles.jsonl")

rows = [json.loads(line) for line in open(QUESTIONS, encoding="utf-8")]
arts = {a["article_id"]: a for a in [json.loads(line) for line in open(ARTICLES, encoding="utf-8")]}
by_qid = {r["qid"]: r for r in rows}
problems = []

if len(rows) != 30:
    problems.append("question_count=%d" % len(rows))
for group, expected in {"vague_role": 10, "multi_requirement": 10, "no_answer": 10}.items():
    actual = sum(1 for r in rows if r.get("group") == group)
    if actual != expected:
        problems.append("group %s=%d expected=%d" % (group, actual, expected))
if len(by_qid) != len(rows):
    problems.append("duplicate qid")
if len({r["question"] for r in rows}) != len(rows):
    problems.append("duplicate question text")


def covers(combo, requirements):
    return all(set(combo) & set(req["acceptable"]) for req in requirements)


for row in rows:
    qid = row["qid"]
    if row.get("retrieval_results_consulted") is not False:
        problems.append("%s retrieval_results_consulted" % qid)
    if row.get("label_status") != "revised_after_independent_ai_review":
        problems.append("%s label_status" % qid)
    if row.get("review_status") != "independent_ai_review_step_no_human":
        problems.append("%s review_status" % qid)
    if row.get("human_review") is not False:
        problems.append("%s human_review" % qid)
    if "另一AI" not in str(row.get("reviewer", "")):
        problems.append("%s reviewer" % qid)
    oc = row.get("overlap_check", {})
    if oc.get("max_text_similarity", 0) >= 0.55:
        problems.append("%s text similarity %.3f" % (qid, oc["max_text_similarity"]))

    if row["answerable"]:
        reqs = row.get("requirements", [])
        if not reqs:
            problems.append("%s missing requirements" % qid)
        for req in reqs:
            if not req.get("acceptable"):
                problems.append("%s empty acceptable" % qid)
            for aid in req.get("acceptable", []):
                if aid not in arts:
                    problems.append("%s unknown article %s" % (qid, aid))
        sets = row.get("sufficient_sets", [])
        if not sets:
            problems.append("%s missing sufficient_sets" % qid)
        for combo in sets:
            if not covers(combo, reqs):
                problems.append("%s insufficient sufficient_set %s" % (qid, combo))
        for a in sets:
            for b in sets:
                if a is not b and set(a) < set(b):
                    problems.append("%s non-minimal set %s < %s" % (qid, a, b))
        for combo in row.get("insufficient_sets_examples", []):
            if covers(combo, reqs):
                problems.append("%s example marked insufficient but covers all: %s" % (qid, combo))
        related = row.get("related_insufficient_articles", [])
        for aid in related:
            if aid not in arts:
                problems.append("%s related unknown %s" % (qid, aid))
        evidence_ids = {e["article_id"] for e in row.get("evidence", [])}
        for req in reqs:
            for aid in req["acceptable"]:
                if aid not in evidence_ids:
                    problems.append("%s missing evidence %s" % (qid, aid))
        for aid in related:
            ev = next((e for e in row.get("evidence", []) if e["article_id"] == aid), None)
            if ev is None or ev.get("role") != "related_not_sufficient":
                problems.append("%s related evidence role %s" % (qid, aid))
        for ev in row.get("evidence", []):
            art = arts.get(ev["article_id"])
            if art is None:
                problems.append("%s evidence unknown %s" % (qid, ev["article_id"]))
                continue
            if ev.get("anchor") != art["anchor"]:
                problems.append("%s anchor mismatch %s" % (qid, ev["article_id"]))
            if ev.get("pdf_page_start") != art["pdf_page_start"]:
                problems.append("%s page mismatch %s" % (qid, ev["article_id"]))
            if ev.get("full_text_sha256") != art["sha256"]:
                problems.append("%s full_text hash mismatch %s" % (qid, ev["article_id"]))
            if ev.get("quote_sha256") != hashlib.sha256(ev["quote"].encode("utf-8")).hexdigest():
                problems.append("%s quote hash mismatch %s" % (qid, ev["article_id"]))
            if ev.get("full_text") != art["text"]:
                problems.append("%s full_text mismatch %s" % (qid, ev["article_id"]))
    else:
        if row.get("requirements"):
            problems.append("%s no_answer has requirements" % qid)
        if row.get("expected_decision") != "refuse":
            problems.append("%s no_answer expected_decision" % qid)
        for aid in row.get("near_miss_articles", []):
            if aid not in arts:
                problems.append("%s near_miss unknown %s" % (qid, aid))

# 本轮指定修订点
n08 = by_qid["N08"]
if [r["acceptable"] for r in n08["requirements"]] != [["rail_quality:art-54"]]:
    problems.append("N08 acceptable must be A54 only")
if "construction_quality:art-53" not in n08.get("related_insufficient_articles", []):
    problems.append("N08 B53 must be related-insufficient")

n09 = by_qid["N09"]
if "铁路监管部门" not in n09["question"] or "建设单位想委托" in n09["question"]:
    problems.append("N09 subject wording")
if {"rail_quality:art-5", "rail_quality:art-47"} - {a for r in n09["requirements"] for a in r["acceptable"]}:
    problems.append("N09 missing A5/A47")

n18 = by_qid["N18"]
if ["construction_quality:art-17", "construction_quality:art-59"] not in n18["sufficient_sets"]:
    problems.append("N18 B17+B59 must be sufficient")
if ["rail_quality:art-18", "construction_quality:art-59"] not in n18.get("insufficient_sets_examples", []):
    problems.append("N18 A18+B59 must be insufficient")

n19 = by_qid["N19"]
comp = [r for r in n19["requirements"] if r["aspect"] == "赔偿责任"]
if not comp or "rail_quality:art-33" in comp[0]["acceptable"]:
    problems.append("N19 A33 must not satisfy compensation")
if not any("B66" in r.get("rationale", "") and "不履行" in r.get("rationale", "") for r in n19["requirements"]):
    problems.append("N19 B66 conditional rationale missing")

expected_sets = {
    "N04": [["rail_quality:art-39"], ["construction_quality:art-37", "construction_quality:art-38"]],
    "N05": [["rail_quality:art-33"], ["construction_quality:art-39", "construction_quality:art-40"]],
    "N10": [["construction_quality:art-22"], ["rail_quality:art-21"]],
}
for qid, expected in expected_sets.items():
    actual = sorted([sorted(s) for s in by_qid[qid]["sufficient_sets"]])
    if actual != sorted([sorted(s) for s in expected]):
        problems.append("%s sufficient_sets mismatch: %s" % (qid, actual))

for qid, expected in {
    "N11": {"rail_quality:art-19", "construction_quality:art-18", "rail_quality:art-34", "construction_quality:art-34"},
    "N13": {"rail_quality:art-50", "construction_quality:art-48", "rail_quality:art-51", "construction_quality:art-50"},
}.items():
    actual = {a for r in by_qid[qid]["requirements"] for a in r["acceptable"]}
    if actual != expected:
        problems.append("%s acceptable set mismatch: %s" % (qid, actual))

if "《建设工程质量管理条例》" not in by_qid["N14"]["question"] or "铁路规定" not in by_qid["N14"]["question"]:
    problems.append("N14 question scope")

for qid in ("N15", "N16"):
    for ev in by_qid[qid]["evidence"]:
        if not ev.get("full_text") or not ev.get("full_text_sha256") or not ev.get("quote_sha256"):
            problems.append("%s missing full text/hash %s" % (qid, ev["article_id"]))

print("eval30_questions=%d groups=%s answerable=%d no_answer=%d" % (
    len(rows), {g: sum(1 for r in rows if r["group"] == g)
                for g in ("vague_role", "multi_requirement", "no_answer")},
    sum(1 for r in rows if r["answerable"]), sum(1 for r in rows if not r["answerable"])))
print("max_text_similarity=%.4f" % max(r["overlap_check"]["max_text_similarity"] for r in rows))
print("shared_dev_gold=%d shared_rewrite_gold=%d（共享条款作为正确答案保留，不作为失败）" % (
    sum(1 for r in rows if r["overlap_check"].get("overlap_with_dev")),
    sum(1 for r in rows if r["overlap_check"].get("overlap_with_rewrite_candidates"))))
for p in problems:
    print("PROBLEM", p)
print("annotation_check failures=%d" % len(problems))
sys.exit(0 if not problems else 2)
