import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rows = [json.loads(line) for line in open(
    os.path.join(ROOT, "data", "task_b_rewrite_candidates.jsonl"), encoding="utf-8")]
config = json.load(open(os.path.join(ROOT, "config", "task_b_config.json"), encoding="utf-8"))

problems = []
if len(rows) != 20:
    problems.append("candidate_count=%d" % len(rows))
for row in rows:
    if row.get("status") != "unlabeled":
        problems.append("%s status=%s" % (row["qid"], row.get("status")))
    if row.get("split") != "same_corpus_rewrite_candidate":
        problems.append("%s split=%s" % (row["qid"], row.get("split")))
    if row.get("required_groups"):
        problems.append("%s has_gold" % row["qid"])
if config.get("rewrite_candidates", {}).get("is_independent_test") is not False:
    problems.append("config marks rewrite candidates as independent test")

overlap = {r["qid"]: r.get("overlap_with_dev", []) for r in rows if r.get("overlap_with_dev")}
for qid in ("F05", "F07", "F08", "F10"):
    if not overlap.get(qid):
        problems.append("%s missing_required_overlap" % qid)

print("rewrite_candidates=%d unlabeled=%d" % (
    len(rows), sum(1 for r in rows if r.get("status") == "unlabeled")))
print("independent_test=%s" % config.get("rewrite_candidates", {}).get("is_independent_test"))
print("overlap_families=%s" % overlap)
for p in problems:
    print("PROBLEM", p)
print("rewrite_check failures=%d" % len(problems))
sys.exit(0 if not problems else 2)