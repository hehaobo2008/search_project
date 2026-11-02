import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORPUS = os.path.join(ROOT, "corpus")
VERIFY = os.path.join(ROOT, "scripts", "verify_task_a.py")


class ExitCodeTest(unittest.TestCase):
    def test_failed_check_returns_nonzero(self):
        tmp = tempfile.mkdtemp(prefix="hcs-fail-")
        corpus_dir = os.path.join(tmp, "corpus")
        reports_dir = os.path.join(tmp, "reports")
        shutil.copytree(CORPUS, corpus_dir)
        articles_path = os.path.join(corpus_dir, "articles.jsonl")
        rows = [json.loads(line) for line in open(articles_path, encoding="utf-8")]
        rows[0]["span_check"] = False
        with open(articles_path, "w", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")

        env = os.environ.copy()
        env["HCS_CORPUS_DIR"] = corpus_dir
        env["HCS_REPORTS_DIR"] = reports_dir
        proc = subprocess.run([sys.executable, VERIFY], cwd=ROOT, env=env,
                              capture_output=True, text=True, encoding="utf-8", errors="replace")
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        result = json.load(open(os.path.join(reports_dir, "task_a_result.json"), encoding="utf-8"))
        self.assertGreaterEqual(result["summary"]["failed"], 1)
        self.assertEqual(result["gate"], "NOT_PASSED_AUTO_FAILURES")

    def test_healthy_corpus_returns_zero(self):
        tmp = tempfile.mkdtemp(prefix="hcs-pass-")
        env = os.environ.copy()
        env["HCS_CORPUS_DIR"] = CORPUS
        env["HCS_REPORTS_DIR"] = os.path.join(tmp, "reports")
        proc = subprocess.run([sys.executable, VERIFY], cwd=ROOT, env=env,
                              capture_output=True, text=True, encoding="utf-8", errors="replace")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()