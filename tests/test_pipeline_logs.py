import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PIPELINE = os.path.join(ROOT, "scripts", "run_pipeline.py")


def run_pipeline(logs_dir, reports_dir, run_id, extra_failure=False):
    env = os.environ.copy()
    env["HCS_LOGS_DIR"] = logs_dir
    env["HCS_REPORTS_DIR"] = reports_dir
    env["HCS_PIPELINE_RUN_ID"] = run_id
    if extra_failure:
        env["HCS_EXTRA_FAILING_STEP"] = "1"
    return subprocess.run([sys.executable, PIPELINE], cwd=ROOT, env=env,
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


class PipelineLogTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.environ.get("HCS_SKIP_NESTED_PIPELINE") == "1":
            raise unittest.SkipTest("nested pipeline disabled during run_tests step")

    def test_each_run_gets_its_own_nonempty_logs(self):
        tmp = tempfile.mkdtemp(prefix="hcs-logs-")
        logs_dir = os.path.join(tmp, "logs")
        reports_dir = os.path.join(tmp, "reports")
        proc = run_pipeline(logs_dir, reports_dir, "pipeline-test-normal")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        manifest = json.load(open(os.path.join(logs_dir, "run_manifest.json"), encoding="utf-8"))
        self.assertEqual(manifest["run_id"], "pipeline-test-normal")
        self.assertTrue(manifest["all_passed"])
        self.assertEqual(manifest["failed_steps"], [])
        self.assertEqual(len(manifest["steps"]), 9)
        run_dir = os.path.join(logs_dir, "runs", "pipeline-test-normal")
        for step in manifest["steps"]:
            self.assertTrue(os.path.exists(step["log_abs"]), step["step"])
            self.assertGreater(step["log_bytes"], 0, step["step"])
            self.assertTrue(os.path.exists(os.path.join(run_dir, step["step"] + ".log")), step["step"])
        self.assertTrue(os.path.exists(os.path.join(run_dir, "run_manifest.json")))

    def test_intentional_failure_makes_pipeline_fail(self):
        tmp = tempfile.mkdtemp(prefix="hcs-negative-")
        logs_dir = os.path.join(tmp, "logs")
        reports_dir = os.path.join(tmp, "reports")
        proc = run_pipeline(logs_dir, reports_dir, "pipeline-test-negative", extra_failure=True)
        self.assertNotEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        manifest = json.load(open(os.path.join(logs_dir, "run_manifest.json"), encoding="utf-8"))
        self.assertFalse(manifest["all_passed"])
        self.assertEqual(manifest["failed_steps"], ["negative_control"])
        negative_log = os.path.join(logs_dir, "runs", "pipeline-test-negative", "negative_control.log")
        self.assertTrue(os.path.exists(negative_log))
        self.assertIn("intentional failure", open(negative_log, encoding="utf-8").read())
        for step in manifest["steps"]:
            self.assertTrue(os.path.exists(step["log_abs"]), step["step"])


if __name__ == "__main__":
    unittest.main()