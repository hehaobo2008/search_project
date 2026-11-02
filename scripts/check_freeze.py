import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
path = os.path.join(ROOT, "data", "task_b_freeze_candidates.jsonl")
rows = [json.loads(line) for line in open(path, encoding="utf-8")]

problems = []
if len(rows) < 20:
    problems.append("too_few_candidates=%d" % len(rows))
for row in rows:
    if row.get("status") != "unlabeled":
        problems.append("%s status=%s" % (row["qid"], row.get("status")))
    if row.get("required_groups"):
        problems.append("%s has_gold_required" % row["qid"])
    if row.get("split") != "freeze_candidate":
        problems.append("%s split=%s" % (row["qid"], row.get("split")))

groups = {}
for row in rows:
    groups[row["group"]] = groups.get(row["group"], 0) + 1

print("freeze_candidates=%d groups=%s" % (len(rows), groups))
print("unlabeled=%d" % sum(1 for r in rows if r.get("status") == "unlabeled"))
for p in problems:
    print("PROBLEM", p)
print("freeze_check failures=%d" % len(problems))
sys.exit(0 if not problems else 2)