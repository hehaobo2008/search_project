import inspect
import json
import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from task_b_eval import score_units  # noqa: E402
from task_b_system import TaskBSystem  # noqa: E402

DEV = {json.loads(line)["qid"]: json.loads(line) for line in open(
    os.path.join(ROOT, "data", "task_b_dev_questions.jsonl"), encoding="utf-8")}
MODULE = {json.loads(line)["qid"]: json.loads(line) for line in open(
    os.path.join(ROOT, "data", "task_b_module_questions.jsonl"), encoding="utf-8")}


class TaskBTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.system = TaskBSystem()

    def test_entry_only_accepts_question_and_method(self):
        params = list(inspect.signature(TaskBSystem.answer).parameters)
        self.assertEqual(params, ["self", "question", "method"])
        source = open(os.path.join(ROOT, "scripts", "task_b_system.py"), encoding="utf-8").read()
        for forbidden in ("task_b_dev_questions", "required_groups", "qid"):
            self.assertNotIn(forbidden, source)
        self.system.answer("铁路工地试块送检要谁在场？", "hybrid_top7")

    def test_methods_share_budget(self):
        q = DEV["D03"]["question"]
        for method in ("bm25_top7", "dense_top7", "hybrid_top7", "hybrid_top5_supplement"):
            result = self.system.answer(q, method)
            units = result["evidence"]
            self.assertLessEqual(len(units), 7, method)
            self.assertLessEqual(sum(u["chars"] for u in units), 2800, method)
            for unit in units:
                self.assertLessEqual(unit["chars"], 400, method)

    def test_pure_bm25_dense_hybrid_and_supplement_differ_on_d03(self):
        q = DEV["D03"]["question"]
        self.assertIn("construction_quality:art-65",
                      [u["article_id"] for u in self.system.answer(q, "bm25_top7")["evidence"]])
        self.assertNotIn("construction_quality:art-65",
                         [u["article_id"] for u in self.system.answer(q, "dense_top7")["evidence"]])
        self.assertIn("construction_quality:art-65",
                      [u["article_id"] for u in self.system.answer(q, "hybrid_top7")["evidence"]])
        supp = self.system.answer(q, "hybrid_top5_supplement")["evidence"]
        self.assertNotIn("construction_quality:art-65", [u["article_id"] for u in supp[:5]])
        self.assertIn("construction_quality:art-65", [u["article_id"] for u in supp[5:]])

    def test_supplement_keeps_base5(self):
        q = DEV["D03"]["question"]
        base = [u["article_id"] for u in self.system.answer(q, "hybrid_top5")["evidence"]]
        supp = [u["article_id"] for u in self.system.answer(q, "hybrid_top5_supplement")["evidence"]]
        self.assertEqual(base, supp[:5])
        self.assertLessEqual(len(supp), 7)

    def test_requirements_allow_alternative_sufficient_sets(self):
        d01 = DEV["D01"]["requirements"]
        d16 = DEV["D16"]["requirements"]
        a30 = [{"article_id": "rail_quality:art-30"}]
        b31 = [{"article_id": "construction_quality:art-31"}]
        b29 = [{"article_id": "construction_quality:art-29"}]
        self.assertTrue(score_units(a30, d01)["full"])
        self.assertTrue(score_units(a30, d16)["full"])
        self.assertFalse(score_units(b31, d16)["full"])
        self.assertTrue(score_units(b31 + b29, d16)["full"])
        self.assertTrue(score_units([{"article_id": "construction_quality:art-29"}], d01)["full"] is False)

    def test_answerability_refuses_out_of_scope_but_not_paraphrase(self):
        for qid in ("D11", "D12"):
            result = self.system.answer(DEV[qid]["question"], "hybrid_top7")
            self.assertEqual(result["decision"], "refuse", qid)
        self.assertEqual(self.system.answer(DEV["D16"]["question"], "hybrid_top7")["decision"], "answer")

    def test_version_and_citation_are_module_tests_only(self):
        self.assertEqual(self.system.module_version_check(MODULE["D13"]["question"])["state"],
                         "version_pending")
        self.assertEqual(self.system.module_relation_check(MODULE["D14"]["pair"])["state"],
                         "topic_related")
        self.assertEqual(self.system.module_relation_check(MODULE["D15"]["pair"])["state"],
                         "explicit_document")
        source = open(os.path.join(ROOT, "scripts", "task_b_system.py"), encoding="utf-8").read()
        self.assertNotIn("version_pending", source)

    def test_rewrite_candidates_are_not_independent_freeze(self):
        rows = [json.loads(line) for line in open(
            os.path.join(ROOT, "data", "task_b_rewrite_candidates.jsonl"), encoding="utf-8")]
        self.assertEqual(len(rows), 20)
        for row in rows:
            self.assertEqual(row["status"], "unlabeled")
            self.assertEqual(row["split"], "same_corpus_rewrite_candidate")
            self.assertNotIn("required_groups", row)
        for qid in ("F05", "F07", "F08", "F10"):
            row = next(r for r in rows if r["qid"] == qid)
            self.assertTrue(row["overlap_with_dev"], qid)
        config = json.load(open(os.path.join(ROOT, "config", "task_b_config.json"), encoding="utf-8"))
        self.assertFalse(config["rewrite_candidates"]["is_independent_test"])

    def test_model_hash_matches_manifest(self):
        proc = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "check_model.py")],
                              cwd=ROOT, capture_output=True, text=True,
                              encoding="utf-8", errors="replace")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()