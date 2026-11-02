import hashlib
import json
import os
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.join(ROOT, ".upload_repo")
QUESTIONS = os.path.join(ROOT, "data", "task_b_eval30_questions.jsonl")
FREEZE = os.path.join(ROOT, "reports", "task_b_eval30_freeze_manifest.json")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


if os.path.exists(os.path.join(ROOT, "reports", "task_b_eval30_results.json")):
    print("REFUSE: results already exist; freeze must precede retrieval")
    sys.exit(2)

rows = [json.loads(line) for line in open(QUESTIONS, encoding="utf-8")]
if len(rows) != 30:
    print("REFUSE: expected 30 questions, got %d" % len(rows))
    sys.exit(2)
if any(r.get("retrieval_results_consulted") for r in rows):
    print("REFUSE: annotation records mention retrieval results")
    sys.exit(2)

question_only = [{"qid": r["qid"], "question": r["question"]} for r in rows]
gold = [{
    "qid": r["qid"],
    "answerable": r["answerable"],
    "requirements": r.get("requirements", []),
    "sufficient_sets": r.get("sufficient_sets", []),
    "insufficient_sets_examples": r.get("insufficient_sets_examples", []),
    "near_miss_articles": r.get("near_miss_articles", []),
} for r in rows]
question_hash = hashlib.sha256(
    json.dumps(question_only, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
gold_hash = hashlib.sha256(
    json.dumps(gold, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()

model = json.load(open(os.path.join(REPO, "docs", "bge-small-zh-v1.5-MODEL_MANIFEST.json"),
                       encoding="utf-8"))
onnx = next(f for f in model["files"] if f["file"] == "onnx/model.onnx")

payload = {
    "batch": "eval30_frozen_v1",
    "status": "frozen_no_retrieval",
    "frozen_at": datetime.now().astimezone().isoformat(),
    "question_count": len(rows),
    "answerable_count": sum(1 for r in rows if r["answerable"]),
    "no_answer_count": sum(1 for r in rows if not r["answerable"]),
    "questions_only_sha256": question_hash,
    "gold_sha256": gold_hash,
    "question_gold_file": {"path": "data/task_b_eval30_questions.jsonl",
                           "sha256": sha256(QUESTIONS),
                           "bytes": os.path.getsize(QUESTIONS)},
    "annotation_package": {
        "annotations": sha256(os.path.join(ROOT, "reports", "task_b_eval30_annotations.md")),
        "overlap": sha256(os.path.join(ROOT, "reports", "task_b_eval30_overlap.md")),
        "protocol": sha256(os.path.join(ROOT, "reports", "task_b_eval30_review_protocol.md")),
    },
    "config_task_b": sha256(os.path.join(REPO, "config", "task_b_config.json")),
    "model_onnx": onnx["sha256"],
    "corpus": {
        "docs_manifest": sha256(os.path.join(REPO, "corpus", "docs_manifest.json")),
        "relations": sha256(os.path.join(REPO, "corpus", "relations.jsonl")),
        "articles_annotation_session": sha256(os.path.join(ROOT, "corpus", "articles.jsonl")),
    },
    "review": {
        "reviewer": "另一AI（依据锁定原文的独立复核步骤）",
        "review_type": "ai_only_independent_review_step",
        "human_review": False,
        "review_status": "independent_ai_review_step_no_human",
        "note": "不是人工签字、专家审核或真人盲测。",
    },
    "retrieval_run": False,
    "retrieval_results_consulted": False,
    "note": "冻结发生在首次检索之前；后续运行不得用结果调参覆盖首轮。",
}
open(FREEZE, "w", encoding="utf-8", newline="\n").write(
    json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
print("frozen questions=%d answerable=%d no_answer=%d" % (
    payload["question_count"], payload["answerable_count"], payload["no_answer_count"]))
print("questions_only_sha256=%s" % question_hash)
print("gold_sha256=%s" % gold_hash)
print("freeze_manifest=%s" % FREEZE)
