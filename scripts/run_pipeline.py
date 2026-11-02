import json
import os
import subprocess
import sys
import time
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS = os.environ.get("HCS_LOGS_DIR", os.path.join(ROOT, "logs"))
os.makedirs(LOGS, exist_ok=True)
RUN_ID = os.environ.get("HCS_PIPELINE_RUN_ID") or (
    "pipeline-" + datetime.now().strftime("%Y%m%dT%H%M%S%z"))
RUN_LOG_DIR = os.path.join(LOGS, "runs", RUN_ID)
os.makedirs(RUN_LOG_DIR, exist_ok=True)

STEPS = [
    ("env_check", "scripts/env_check.py"),
    ("build_corpus", "scripts/build_corpus.py"),
    ("build_locators", "scripts/build_locators.py"),
    ("build_relations", "scripts/build_relations.py"),
    ("verify_task_a", "scripts/verify_task_a.py"),
    ("verify_counterexamples", "scripts/verify_counterexamples.py"),
    ("verify_locators", "scripts/verify_locators.py"),
    ("run_tests", "scripts/run_tests.py"),
    ("generate_review_checklist", "scripts/generate_review_checklist.py"),
]

if os.environ.get("HCS_EXTRA_FAILING_STEP") == "1":
    STEPS.append(("negative_control", "__NEGATIVE_CONTROL__"))

records = []
for name, rel in STEPS:
    started = datetime.now().astimezone()
    t0 = time.time()
    if rel == "__NEGATIVE_CONTROL__":
        command = [sys.executable, "-c", "import sys; print('intentional failure'); sys.exit(7)"]
        command_text = "%s -c \"intentional failing step\"" % sys.executable
    else:
        command = [sys.executable, os.path.join(ROOT, rel)]
        command_text = "%s %s" % (sys.executable, rel)
    env = os.environ.copy()
    if name == "run_tests":
        env["HCS_SKIP_NESTED_PIPELINE"] = "1"
    proc = subprocess.run(command, cwd=ROOT, env=env,
                          capture_output=True, text=True, encoding="utf-8", errors="replace")
    duration = round(time.time() - t0, 3)
    ended = datetime.now().astimezone()
    log_name = "%s.log" % name
    payload_text = proc.stdout + ("\n[stderr]\n" + proc.stderr if proc.stderr else "")
    run_log_path = os.path.join(RUN_LOG_DIR, log_name)
    latest_log_path = os.path.join(LOGS, log_name)
    with open(run_log_path, "w", encoding="utf-8") as f:
        f.write(payload_text)
    with open(latest_log_path, "w", encoding="utf-8") as f:
        f.write(payload_text)
    records.append({
        "step": name,
        "script": rel,
        "command": command_text,
        "exit_code": proc.returncode,
        "started_at": started.isoformat(),
        "ended_at": ended.isoformat(),
        "duration_sec": duration,
        "log": (os.path.relpath(run_log_path, ROOT).replace("\\", "/")
                if os.path.abspath(run_log_path).startswith(os.path.abspath(ROOT)) else run_log_path),
        "log_abs": run_log_path,
        "latest_log": latest_log_path,
        "log_bytes": os.path.getsize(run_log_path),
        "stdout_tail": (proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else ""),
    })
    print("%-28s exit=%d %.3fs" % (name, proc.returncode, duration))

failed = [r for r in records if r["exit_code"] != 0]
payload = {
    "run_id": RUN_ID,
    "generated_at": datetime.now().astimezone().isoformat(),
    "python": sys.version,
    "executable": sys.executable,
    "platform": sys.platform,
    "steps": records,
    "failed_steps": [r["step"] for r in failed],
    "all_passed": not failed,
}
with open(os.path.join(LOGS, "run_manifest.json"), "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False, indent=2)
with open(os.path.join(RUN_LOG_DIR, "run_manifest.json"), "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False, indent=2)
print("run_manifest written; all_passed=%s failed=%s" % (payload["all_passed"], payload["failed_steps"]))
sys.exit(0 if payload["all_passed"] else 1)