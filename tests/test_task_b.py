import json
import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from task_b_eval import eval_method, groups_hit  # noqa: E402
from task_b_retriever import TaskBRetriever  # noqa: E402

QUESTIONS = {json.loads(line)["qid"]: json.loads(line) for line in open(
    os.path.join(ROOT, "data", "task_b_dev_questions.jsonl"), encoding="utf-8")}


class TaskBTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.retriever = TaskBRetriever()

    def test_search_is_deterministic(self):
        q = QUESTIONS["D01"]["question"]
        first = [x["article_id"] for x in self.retriever.search(q)[:10]]
        second = [x["article_id"] for x in self.retriever.search(q)[:10]]
        self.assertEqual(first, second)
        self.assertIn("rail_quality:art-30", first)

    def test_method_budgets_and_base5_invariant(self):
        q = QUESTIONS["D03"]["question"]
        ranked = self.retriever.search(q)
        methods = self.retriever.methods(ranked)
        self.assertEqual(len(methods["top5"]), 5)
        self.assertEqual(len(methods["top7"]), 7)
        supp = methods["top5_supplement"]
        self.assertLessEqual(len(supp), 7)
        self.assertGreaterEqual(len(supp), 5)
        self.assertEqual([u["article_id"] for u in supp[:5]],
                         [u["article_id"] for u in methods["top5"]])
        for units in (methods["top7"], supp):
            self.assertLessEqual(sum(u["chars"] for u in units), 2800)
            for unit in units:
                self.assertLessEqual(unit["chars"], 400)
        for unit in supp[5:]:
            self.assertIsNotNone(unit["relation"])
            self.assertIn(unit["relation"]["relation_type"], ("explicit_article", "amendment"))
        ids = [u["article_id"] for u in supp]
        self.assertEqual(len(ids), len(set(ids)))

    def test_supplement_reaches_b65_for_d03(self):
        ranked = self.retriever.search(QUESTIONS["D03"]["question"])
        supp = self.retriever.supplemented(ranked)
        self.assertLessEqual(len(supp), 7)
        self.assertNotIn("construction_quality:art-65", [u["article_id"] for u in supp[:5]])
        self.assertIn("construction_quality:art-65", [u["article_id"] for u in supp[5:]])

    def test_answerability_refuses_out_of_scope_but_not_paraphrase(self):
        for qid in ("D11", "D12"):
            self.retriever.search(QUESTIONS[qid]["question"])
            result = self.retriever.assess_answerability(QUESTIONS[qid]["question"])
            self.assertEqual(result["decision"], "refuse", qid)
            self.assertGreaterEqual(result["unknown_count"], 1, qid)
        self.retriever.search(QUESTIONS["D16"]["question"])
        result = self.retriever.assess_answerability(QUESTIONS["D16"]["question"])
        self.assertEqual(result["decision"], "answer", result)

    def test_version_and_citation_shutdowns(self):
        self.assertEqual(self.retriever.version_check(QUESTIONS["D13"]["question"])["state"],
                         "version_pending")
        self.assertEqual(self.retriever.inspect_relation(QUESTIONS["D14"]["pair"])["state"],
                         "topic_related")
        self.assertEqual(self.retriever.inspect_relation(QUESTIONS["D15"]["pair"])["state"],
                         "explicit_document")

    def test_metric_functions(self):
        hits = groups_hit(["a|b", "c"], [{"article_id": "b"}, {"article_id": "c"}])
        self.assertEqual(hits, [True, True])
        q = {"required_groups": ["a|b", "c"]}
        units = [{"article_id": "b", "chars": 10, "truncated": False, "relation": None}]
        metric = eval_method(units, q)
        self.assertTrue(metric["hit"])
        self.assertFalse(metric["all_covered"])
        self.assertEqual(metric["groups_hit"], 1)
        self.assertEqual(metric["recall"], 0.5)

    def test_model_hash_matches_manifest(self):
        proc = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "check_model.py")],
                              cwd=ROOT, capture_output=True, text=True,
                              encoding="utf-8", errors="replace")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_freeze_candidates_are_unlabeled(self):
        rows = [json.loads(line) for line in open(
            os.path.join(ROOT, "data", "task_b_freeze_candidates.jsonl"), encoding="utf-8")]
        self.assertEqual(len(rows), 20)
        for row in rows:
            self.assertEqual(row["status"], "unlabeled")
            self.assertNotIn("required_groups", row)
            self.assertEqual(row["split"], "freeze_candidate")


if __name__ == "__main__":
    unittest.main()