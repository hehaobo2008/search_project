import argparse
import hashlib
import json
import os
import sys
import threading
import time
import uuid
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from task_b_system import TaskBSystem  # noqa: E402

METHOD = "hybrid_top5"
AUTO_SUPPLEMENT = False

# 只保存三个已见任务的题面；不包含 gold、条号或页码。
TASKS = {
    "task1": "建设单位需要配备什么质量管理人员、谁留存检查记录？",
    "task2": "竣工验收后多久备案，逾期备案罚则在哪？",
    "task3": "环保验收需要监测哪些因子、频次多少？",
}


class App:
    def __init__(self):
        t0 = time.perf_counter()
        self.system = TaskBSystem()
        self.init_ms = round((time.perf_counter() - t0) * 1000, 1)
        self.ready_at = datetime.now().astimezone().isoformat()
        self.runs = {}
        self.lock = threading.Lock()
        self.log_root = os.path.join(ROOT, "logs", "ux_trial")
        self.page_events = os.path.join(self.log_root, "page_events.jsonl")
        os.makedirs(self.log_root, exist_ok=True)

        manifest = json.load(open(os.path.join(ROOT, "corpus", "docs_manifest.json"), encoding="utf-8"))
        self.docs = {d["doc_id"]: d for d in manifest["documents"]}
        self.arts = {a["article_id"]: a for a in [
            json.loads(l) for l in open(os.path.join(ROOT, "corpus", "articles.jsonl"), encoding="utf-8")]}
        self.config_id = "cfg-" + hashlib.sha256(open(
            os.path.join(ROOT, "config", "task_b_config.json"), "rb").read()).hexdigest()[:12] + "-" + METHOD
        model = json.load(open(os.path.join(ROOT, "docs", "bge-small-zh-v1.5-MODEL_MANIFEST.json"), encoding="utf-8"))
        onnx = next(f for f in model["files"] if f["file"] == "onnx/model.onnx")
        self.model_hash = onnx["sha256"]
        self.corpus_hash = hashlib.sha256(open(
            os.path.join(ROOT, "corpus", "docs_manifest.json"), "rb").read()).hexdigest()
        self.articles_hash = hashlib.sha256(open(
            os.path.join(ROOT, "corpus", "articles.jsonl"), "rb").read()).hexdigest()

    def new_run(self, task_id):
        if task_id not in TASKS:
            return None, "unknown_task"
        run_id = "ux-" + datetime.now().strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:4]
        run_dir = os.path.join(self.log_root, "runs", run_id)
        os.makedirs(run_dir, exist_ok=True)
        run = {
            "run_id": run_id,
            "task_id": task_id,
            "question": TASKS[task_id],
            "status": "active",
            "started_at": datetime.now().astimezone().isoformat(),
            "started_ts": time.time(),
            "ended_at": None,
            "duration_ms": None,
            "init_ms": self.init_ms,
            "ready_at": self.ready_at,
            "method": METHOD,
            "auto_supplement": AUTO_SUPPLEMENT,
            "config_id": self.config_id,
            "model_onnx_sha256": self.model_hash,
            "corpus_docs_manifest_sha256": self.corpus_hash,
            "corpus_articles_sha256": self.articles_hash,
            "queries": [],
            "events": [],
            "selected_evidence": [],
            "outcome": None,
            "events_file": os.path.join("logs", "ux_trial", "runs", run_id, "events.jsonl").replace("\\", "/"),
            "run_file": os.path.join("logs", "ux_trial", "runs", run_id, "run.json").replace("\\", "/"),
        }
        with self.lock:
            self.runs[run_id] = run
        self.event(run, "task_started", {
            "task_id": task_id, "question": run["question"],
            "init_ms": self.init_ms, "method": METHOD, "config_id": self.config_id,
        })
        return run, None

    def event(self, run, event_type, payload=None):
        event = {
            "ts": datetime.now().astimezone().isoformat(),
            "event": event_type,
            "run_id": run["run_id"] if run else None,
        }
        if payload:
            event.update(payload)
        run_dir = os.path.join(self.log_root, "runs", run["run_id"]) if run else None
        if run_dir:
            os.makedirs(run_dir, exist_ok=True)
            with open(os.path.join(run_dir, "events.jsonl"), "a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
            run["events"].append(event)
            with open(os.path.join(run_dir, "run.json"), "w", encoding="utf-8", newline="\n") as f:
                f.write(json.dumps(run, ensure_ascii=False, indent=2) + "\n")
        else:
            with open(self.page_events, "a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
        return event

    def answer(self, run, question):
        t0 = time.perf_counter()
        res = self.system.answer(question, METHOD)
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)
        evidence = []
        for rank, u in enumerate(res.get("evidence", []), 1):
            art = self.arts.get(u["article_id"], {})
            doc = self.docs.get(u["doc_id"], {})
            evidence.append({
                "rank": rank,
                "article_id": u["article_id"],
                "article_no": u["article_no"],
                "doc_id": u["doc_id"],
                "doc_title": doc.get("title", u["doc_id"]),
                "version_id": u["version_id"],
                "text": u["text"],
                "chars": u["chars"],
                "full_chars": u["full_chars"],
                "truncated": u["truncated"],
                "source_url": u["source_url"],
                "source_sha256": u["sha256"],
                "locator_route": "/locator/%s#%s" % (u["doc_id"], u["anchor"]),
                "pdf_route": "/pdf/%s#page=%s" % (u["doc_id"], art.get("pdf_page_start")),
                "pdf_page": art.get("pdf_page_start"),
            })
        return res, evidence, elapsed_ms


APP = None


class Handler(BaseHTTPRequestHandler):
    server_version = "HCS-UX/1.0"

    def log_message(self, fmt, *args):
        pass

    def send_json(self, code, payload):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def read_json(self):
        n = int(self.headers.get("Content-Length", "0"))
        if not n:
            return {}
        try:
            return json.loads(self.rfile.read(n).decode("utf-8"))
        except Exception:
            return {}

    def serve_bytes(self, path, content_type):
        if not os.path.isfile(path):
            self.send_json(404, {"error": "not_found"})
            return
        data = open(path, "rb").read()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/":
            self.serve_bytes(os.path.join(ROOT, "scripts", "ux_trial_page.html"),
                             "text/html; charset=utf-8")
            return
        if path.startswith("/locator/"):
            doc_id = path.split("/", 2)[2]
            name = "rail_quality.locator.html" if doc_id == "rail_quality" else (
                "construction_quality.locator.html" if doc_id == "construction_quality" else None)
            if not name:
                self.send_json(404, {"error": "unknown_doc"})
                return
            self.serve_bytes(os.path.join(ROOT, "locators", name), "text/html; charset=utf-8")
            return
        if path.startswith("/pdf/"):
            doc_id = path.split("/", 2)[2]
            doc = APP.docs.get(doc_id)
            if not doc or not doc.get("rendering"):
                self.send_json(404, {"error": "unknown_doc"})
                return
            self.serve_bytes(os.path.join(ROOT, doc["rendering"]["file"]), "application/pdf")
            return
        self.send_json(404, {"error": "not_found"})

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        body = self.read_json()
        if path == "/api/start":
            run, err = APP.new_run(body.get("task_id"))
            if err:
                self.send_json(400, {"error": err})
                return
            self.send_json(200, {
                "run_id": run["run_id"], "question": run["question"],
                "init_ms": APP.init_ms, "ready_at": APP.ready_at,
                "method": METHOD, "auto_supplement": AUTO_SUPPLEMENT,
                "config_id": APP.config_id,
            })
            return
        if path == "/api/event":
            run = APP.runs.get(body.get("run_id")) if body.get("run_id") else None
            APP.event(run, body.get("type") or "client_event", {k: v for k, v in body.items()
                                                                    if k not in ("run_id", "type")})
            self.send_json(200, {"ok": True})
            return
        if path == "/api/search":
            run = APP.runs.get(body.get("run_id"))
            if run is None:
                self.send_json(404, {"error": "run_not_found"})
                return
            if run["status"] != "active":
                self.send_json(409, {"error": "run_not_active"})
                return
            q = (body.get("question") or "").strip()
            if q != run["question"]:
                APP.event(run, "question_mismatch", {"submitted": q})
                self.send_json(400, {"error": "本页只验证已见任务，问题必须与题面一致"})
                return
            now = time.time()
            if run.get("last_search_ts") and now - run["last_search_ts"] < 1.2:
                APP.event(run, "duplicate_query", {"question": q})
                self.send_json(409, {"error": "重复提交已记录；请稍后再查或使用再次查询"})
                return
            run["last_search_ts"] = now
            APP.event(run, "query_submitted", {"question": q})
            try:
                res, evidence, search_ms = APP.answer(run, q)
            except Exception as exc:
                APP.event(run, "search_error", {"error": repr(exc)})
                self.send_json(500, {"error": "search_failed"})
                return
            decision = res.get("decision")
            message = "本次未提供充分依据" if decision == "refuse" else ""
            APP.event(run, "results_ready", {
                "decision": decision, "evidence_ids": [e["article_id"] for e in evidence],
                "result_count": len(evidence), "search_ms": search_ms, "message": message,
            })
            run["queries"].append({
                "question": q, "decision": decision, "search_ms": search_ms,
                "evidence": evidence, "message": message,
            })
            with open(os.path.join(APP.log_root, "runs", run["run_id"], "run.json"),
                      "w", encoding="utf-8", newline="\n") as f:
                f.write(json.dumps(run, ensure_ascii=False, indent=2) + "\n")
            self.send_json(200, {
                "run_id": run["run_id"], "decision": decision, "message": message,
                "search_ms": search_ms, "evidence": evidence,
                "truncation_note": "每个证据最多展示 400 字符；truncated=true 表示有截断。",
            })
            return
        if path == "/api/end":
            run = APP.runs.get(body.get("run_id"))
            if run is None:
                self.send_json(404, {"error": "run_not_found"})
                return
            outcome = body.get("outcome")
            if outcome not in ("found", "not_found", "aborted"):
                self.send_json(400, {"error": "invalid_outcome"})
                return
            selected = body.get("selected_evidence") or []
            run["status"] = "ended"
            run["outcome"] = outcome
            run["selected_evidence"] = selected
            run["ended_at"] = datetime.now().astimezone().isoformat()
            run["duration_ms"] = round((time.time() - run["started_ts"]) * 1000, 1)
            APP.event(run, "task_ended", {
                "outcome": outcome, "selected_evidence": selected,
                "note": body.get("note", ""), "duration_ms": run["duration_ms"],
            })
            with open(os.path.join(APP.log_root, "runs", run["run_id"], "run.json"),
                      "w", encoding="utf-8", newline="\n") as f:
                f.write(json.dumps(run, ensure_ascii=False, indent=2) + "\n")
            self.send_json(200, {
                "run_id": run["run_id"], "outcome": outcome,
                "selected_evidence": selected, "duration_ms": run["duration_ms"],
                "message": "任务已结束；本页不判定答对或证据充分，等待独立评分。",
            })
            return
        self.send_json(404, {"error": "not_found"})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    if args.host != "127.0.0.1":
        print("REFUSE: this page is loopback-only; host must be 127.0.0.1", file=sys.stderr)
        return 2
    global APP
    APP = App()
    print("ready=%s init_ms=%.1f config_id=%s" % (APP.ready_at, APP.init_ms, APP.config_id))
    print("http://127.0.0.1:%d/" % args.port, flush=True)
    ThreadingHTTPServer((args.host, args.port), Handler).serve_forever()


if __name__ == "__main__":
    sys.exit(main())
