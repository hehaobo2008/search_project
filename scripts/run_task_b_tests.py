import json
import os
import sys
import time
import unittest

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
REPORTS = os.environ.get("HCS_REPORTS_DIR", os.path.join(ROOT, "reports"))
os.makedirs(REPORTS, exist_ok=True)

suite = unittest.TestLoader().loadTestsFromName("tests.test_task_b")
started = time.time()
runner = unittest.TextTestRunner(stream=sys.stdout, verbosity=2)
result = runner.run(suite)
duration = round(time.time() - started, 3)

payload = {
    "generated_at": __import__("datetime").datetime.now().astimezone().isoformat(),
    "module": "tests.test_task_b",
    "total": result.testsRun,
    "passed": result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped),
    "failures": [test.id() for test, _ in result.failures],
    "errors": [test.id() for test, _ in result.errors],
    "skipped": [test.id() for test, _ in result.skipped],
    "success": result.wasSuccessful(),
    "duration_sec": duration,
}
with open(os.path.join(REPORTS, "task_b_test_result.json"), "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False, indent=2)
print("task_b_tests total=%d passed=%d failures=%d errors=%d success=%s" % (
    payload["total"], payload["passed"], len(payload["failures"]), len(payload["errors"]),
    payload["success"]))
sys.exit(0 if payload["success"] else 2)