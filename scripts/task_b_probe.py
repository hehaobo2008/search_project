import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from task_b_retriever import TaskBRetriever  # noqa: E402

questions = {json.loads(line)["qid"]: json.loads(line) for line in open(
    os.path.join(ROOT, "data", "task_b_dev_questions.jsonl"), encoding="utf-8")}
retriever = TaskBRetriever()
print("vector_cache_hit=%s embed_docs_ms=%s" % (retriever.vector_cache_hit, retriever.embed_ms))

for qid in ["D01", "D02", "D03", "D04", "D05", "D06", "D07", "D08", "D09", "D10", "D11", "D12", "D13", "D14", "D15", "D16", "D17", "D18"]:
    q = questions[qid]
    print("\n== %s %s" % (qid, q["question"]))
    vc = retriever.version_check(q["question"])
    print("version:", vc.get("state"), vc.get("message", ""))
    if vc.get("state") == "version_pending":
        continue
    ranked = retriever.search(q["question"])
    print("max_sem=%.4f search_ms=%s" % (retriever.last_max_sem, retriever.last_search_ms))
    print("assess:", retriever.assess_answerability(q["question"]))
    print("top5:", [(x["article_id"], x["score"], x["lex_rank"], x["sem_rank"]) for x in ranked[:5]])
    print("top7:", [x["article_id"] for x in ranked[:7]])
    methods = retriever.methods(ranked)
    for name in ("top5", "top7", "top5_supplement"):
        units = methods[name]
        print("%s units=%d chars=%d ids=%s" % (
            name, len(units), sum(u["chars"] for u in units), [u["article_id"] for u in units]))
        for u in units:
            if u.get("relation"):
                print("   supplement:", u["article_id"], u["relation"]["relation_type"],
                      "from", u["relation"]["source_article_id"])
    if q.get("pair"):
        print("relation:", retriever.inspect_relation(q["pair"]))