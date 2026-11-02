import json
import os
import sys
import time
import unittest

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TESTS = os.path.join(ROOT, "tests")
REPORTS = os.environ.get("HCS_REPORTS_DIR", os.path.join(ROOT, "reports"))
RESULT_NAME = os.environ.get("HCS_TEST_RESULT_NAME", "test_result.json")
os.makedirs(REPORTS, exist_ok=True)

loader = unittest.TestLoader()
suite = loader.discover(TESTS, pattern="test_*.py", top_level_dir=ROOT)

started = time.time()
runner = unittest.TextTestRunner(stream=sys.stdout, verbosity=2)
result = runner.run(suite)
duration = round(time.time() - started, 3)

failures = [{"test": test.id(), "traceback": tb} for test, tb in result.failures]
errors = [{"test": test.id(), "traceback": tb} for test, tb in result.errors]
skipped_classes = [{"test": test.id(), "reason": reason}
                   for test, reason in result.skipped if "setUpClass" in test.id()]
skipped_tests = [{"test": test.id(), "reason": reason}
                 for test, reason in result.skipped if "setUpClass" not in test.id()]

payload = {
    "generated_at": __import__("datetime").datetime.now().astimezone().isoformat(),
    "total": result.testsRun,
    "passed": result.testsRun - len(failures) - len(errors) - len(skipped_tests),
    "failures": failures,
    "errors": errors,
    "skipped_classes": skipped_classes,
    "skipped_tests": skipped_tests,
    "success": result.wasSuccessful(),
    "duration_sec": duration,
}
with open(os.path.join(REPORTS, RESULT_NAME), "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False, indent=2)

print("tests total=%d passed=%d failures=%d errors=%d skipped_classes=%d skipped_tests=%d success=%s" % (
    payload["total"], payload["passed"], len(failures), len(errors),
    len(skipped_classes), len(skipped_tests), payload["success"]))
sys.exit(0 if payload["success"] else 2)