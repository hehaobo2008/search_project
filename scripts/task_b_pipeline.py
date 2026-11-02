import json
import os
import subprocess
import sys
import time
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS = os.environ.get("HCS_TASK_B_LOGS_DIR", os.path.join(ROOT, "logs", "task_b"))
os.makedirs(LOGS, exist_ok=True)
RUN_ID = os.environ.get("HCS_TASK_B_RUN_ID") or (
    "taskB-" + datetime.now().strftime("%Y%m%dT%H%M%S%z"))
RUN_LOG_DIR = os.path.join(LOGS, "runs", RUN_ID)
os.makedirs(RUN_LOG_DIR, exist_ok=True)

STEPS = [
    ("check_model", "scripts/check_model.py"),
    ("eval_dev", "scripts/task_b_eval.py"),
    ("run_tests", "scripts/run_task_b_tests.py"),
    ("check_freeze", "scripts/check_freeze.py"),
]

records = []
for name, rel in STEPS:
    started = datetime.now().astimezone()
    t0 = time.time()
    env = os.environ.copy()
    proc = subprocess.run([sys.executable, os.path.join(ROOT, rel)], cwd=ROOT, env=env,
                          capture_output=True, text=True, encoding="utf-8", errors="replace")
    duration = round(time.time() - t0, 3)
    ended = datetime.now().astimezone()
    log_name = "%s.log" % name
    text = proc.stdout + ("\n[stderr]\n" + proc.stderr if proc.stderr else "")
    run_log = os.path.join(RUN_LOG_DIR, log_name)
    latest_log = os.path.join(LOGS, log_name)
    with open(run_log, "w", encoding="utf-8") as f:
        f.write(text)
    with open(latest_log, "w", encoding="utf-8") as f:
        f.write(text)
    records.append({
        "step": name,
        "script": rel,
        "command": "%s %s" % (sys.executable, rel),
        "exit_code": proc.returncode,
        "started_at": started.isoformat(),
        "ended_at": ended.isoformat(),
        "duration_sec": duration,
        "log": os.path.relpath(run_log, ROOT).replace("\\", "/"),
        "log_abs": run_log,
        "latest_log": latest_log,
        "log_bytes": os.path.getsize(run_log),
        "stdout_tail": (proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else ""),
    })
    print("%-16s exit=%d %.3fs" % (name, proc.returncode, duration))

failed = [r for r in records if r["exit_code"] != 0]
payload = {
    "run_id": RUN_ID,
    "generated_at": datetime.now().astimezone().isoformat(),
    "task": "B dev exploration",
    "python": sys.version,
    "executable": sys.executable,
    "platform": sys.platform,
    "steps": records,
    "failed_steps": [r["step"] for r in failed],
    "all_passed": not failed,
}
for path in (os.path.join(LOGS, "run_manifest.json"),
             os.path.join(RUN_LOG_DIR, "run_manifest.json")):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
print("run_manifest written; all_passed=%s failed=%s" % (payload["all_passed"], payload["failed_steps"]))
sys.exit(0 if payload["all_passed"] else 1)