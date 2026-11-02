import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUESTIONS = os.path.join(ROOT, "data", "task_b_eval30_questions.jsonl")
ARTICLES = os.path.join(ROOT, "corpus", "articles.jsonl")

rows = [json.loads(line) for line in open(QUESTIONS, encoding="utf-8")]
arts = {a["article_id"]: a for a in [json.loads(line) for line in open(ARTICLES, encoding="utf-8")]}
problems = []

if len(rows) != 30:
    problems.append("question_count=%d" % len(rows))
groups = {"vague_role": 10, "multi_requirement": 10, "no_answer": 10}
for group, expected in groups.items():
    actual = sum(1 for r in rows if r.get("group") == group)
    if actual != expected:
        problems.append("group %s=%d expected=%d" % (group, actual, expected))
if len({r["qid"] for r in rows}) != len(rows):
    problems.append("duplicate qid")
if len({r["question"] for r in rows}) != len(rows):
    problems.append("duplicate question text")

for row in rows:
    qid = row["qid"]
    if row.get("retrieval_results_consulted") is not False:
        problems.append("%s retrieval_results_consulted" % qid)
    if row.get("label_status") != "ai_draft_pending_independent_review":
        problems.append("%s label_status" % qid)
    if row.get("review_status") != "ai_self_check_only_no_human_review":
        problems.append("%s review_status" % qid)
    oc = row.get("overlap_check", {})
    if oc.get("overlap_with_dev"):
        problems.append("%s shares dev gold: %s" % (qid, oc["overlap_with_dev"]))
    if oc.get("overlap_with_rewrite_candidates"):
        problems.append("%s shares rewrite gold: %s" % (qid, oc["overlap_with_rewrite_candidates"]))
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
            for req in reqs:
                if not (set(combo) & set(req["acceptable"])):
                    problems.append("%s insufficient set %s missing %s" % (qid, combo, req["aspect"]))
        evidence_ids = {e["article_id"] for e in row.get("evidence", [])}
        for req in reqs:
            for aid in req["acceptable"]:
                if aid not in evidence_ids:
                    problems.append("%s missing evidence %s" % (qid, aid))
        for ev in row.get("evidence", []):
            art = arts.get(ev["article_id"])
            if art is None:
                problems.append("%s evidence unknown %s" % (qid, ev["article_id"]))
            else:
                if ev.get("anchor") != art["anchor"]:
                    problems.append("%s anchor mismatch %s" % (qid, ev["article_id"]))
                if ev.get("pdf_page_start") != art["pdf_page_start"]:
                    problems.append("%s page mismatch %s" % (qid, ev["article_id"]))
    else:
        if row.get("requirements"):
            problems.append("%s no_answer has requirements" % qid)
        if row.get("expected_decision") != "refuse":
            problems.append("%s no_answer expected_decision" % qid)
        for aid in row.get("near_miss_articles", []):
            if aid not in arts:
                problems.append("%s near_miss unknown %s" % (qid, aid))

print("eval30_questions=%d groups=%s answerable=%d no_answer=%d" % (
    len(rows), {g: sum(1 for r in rows if r["group"] == g) for g in groups},
    sum(1 for r in rows if r["answerable"]), sum(1 for r in rows if not r["answerable"])))
print("max_text_similarity=%.4f" % max(r["overlap_check"]["max_text_similarity"] for r in rows))
for p in problems:
    print("PROBLEM", p)
print("annotation_check failures=%d" % len(problems))
sys.exit(0 if not problems else 2)
