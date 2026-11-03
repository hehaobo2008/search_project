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

CLOCK_NOTE = (
    "duration_ms 起点取页面点击「开始任务」时的客户端毫秒时间戳，终点取服务端收到结束请求的时刻，"
    "包含请求/响应的网络与页面延迟；duration_server_ms 只算服务端收到开始/结束请求之间；"
    "duration_client_reported_ms 是页面 performance.now() 差值，仅作对照。"
)


class App:
    def __init__(self):
        t0 = time.perf_counter()
        self.system = TaskBSystem()
        self.init_ms = round((time.perf_counter() - t0) * 1000, 1)
        self.ready_at = datetime.now().astimezone().isoformat()
        self.session_id = "s-" + datetime.now().strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:6]
        self.runs = {}
        self.current_run_id = None
        self.lock = threading.RLock()
        self.log_root = os.path.join(ROOT, "logs", "ux_trial")
        self.page_events = os.path.join(self.log_root, "page_events.jsonl")
        self.rejected_events = os.path.join(self.log_root, "rejected_events.jsonl")
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

    # ---- 会话状态 ----

    def active_run(self):
        run = self.runs.get(self.current_run_id)
        return run if run and run["status"] == "active" else None

    def phase(self):
        run = self.runs.get(self.current_run_id)
        if run is None:
            return "idle"
        return "active" if run["status"] == "active" else "ended"

    def reject(self, run, kind, payload):
        """记录一次被拒绝的请求；有 run 时追加到该 run 的事件，同时写全局拒绝索引。"""
        event = {"ts": datetime.now().astimezone().isoformat(), "event": kind,
                 "run_id": run["run_id"] if run else None, "rejected": True,
                 "phase": self.phase(), "session_id": self.session_id}
        event.update(payload or {})
        with self.lock:
            with open(self.rejected_events, "a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
        if run is not None:
            self.event(run, kind, dict(payload or {}, rejected=True, phase=self.phase()))
        else:
            with open(self.page_events, "a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
        return event

    def new_run(self, task_id, recv_epoch_ms, client_click_epoch_ms):
        if task_id not in TASKS:
            self.reject(None, "start_rejected", {"reason": "unknown_task", "requested_task_id": task_id})
            return None, "unknown_task"
        with self.lock:
            busy = self.active_run()
            if busy is not None:
                self.reject(busy, "start_rejected", {
                    "reason": "session_active", "active_run_id": busy["run_id"],
                    "requested_task_id": task_id,
                })
                return None, "session_active"
            run_id = "ux-" + datetime.now().strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:4]
            run_dir = os.path.join(self.log_root, "runs", run_id)
            os.makedirs(run_dir, exist_ok=True)
            run = {
                "run_id": run_id,
                "session_id": self.session_id,
                "task_id": task_id,
                "question": TASKS[task_id],
                "status": "active",
                "phase": "active",
                "started_at": datetime.now().astimezone().isoformat(),
                "started_ts": time.time(),
                "client_click_epoch_ms": client_click_epoch_ms,
                "start_request_received_at": datetime.now().astimezone().isoformat(),
                "start_request_received_epoch_ms": recv_epoch_ms,
                "start_response_sent_at": None,
                "timer_basis": "client_click",
                "clock_note": CLOCK_NOTE,
                "ended_at": None,
                "duration_ms": None,
                "duration_server_ms": None,
                "duration_client_reported_ms": None,
                "init_ms": self.init_ms,
                "ready_at": self.ready_at,
                "method": METHOD,
                "auto_supplement": AUTO_SUPPLEMENT,
                "config_id": self.config_id,
                "model_onnx_sha256": self.model_hash,
                "corpus_docs_manifest_sha256": self.corpus_hash,
                "corpus_articles_sha256": self.articles_hash,
                "queries": [],
                "displayed_evidence": [],
                "events": [],
                "selected_evidence": [],
                "outcome": None,
                "rejections": [],
                "events_file": os.path.join("logs", "ux_trial", "runs", run_id, "events.jsonl").replace("\\", "/"),
                "run_file": os.path.join("logs", "ux_trial", "runs", run_id, "run.json").replace("\\", "/"),
            }
            self.runs[run_id] = run
            self.current_run_id = run_id
        self.event(run, "task_started", {
            "task_id": task_id, "question": run["question"],
            "init_ms": self.init_ms, "method": METHOD, "config_id": self.config_id,
            "client_click_epoch_ms": client_click_epoch_ms,
            "start_request_received_epoch_ms": recv_epoch_ms,
            "clock_note": CLOCK_NOTE,
        })
        return run, None

    def event(self, run, event_type, payload=None):
        with self.lock:
            event = {
                "ts": datetime.now().astimezone().isoformat(),
                "event": event_type,
                "run_id": run["run_id"] if run else None,
            }
            if payload:
                event.update(payload)
            if run is None:
                with open(self.page_events, "a", encoding="utf-8") as f:
                    f.write(json.dumps(event, ensure_ascii=False) + "\n")
                return event
            if run["status"] != "active":
                event.setdefault("after_run_end", True)
            run_dir = os.path.join(self.log_root, "runs", run["run_id"])
            os.makedirs(run_dir, exist_ok=True)
            with open(os.path.join(run_dir, "events.jsonl"), "a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
            run["events"].append(event)
            if event.get("rejected"):
                run["rejections"].append(event)
            self._write_run(run)
            return event

    def _write_run(self, run):
        run_dir = os.path.join(self.log_root, "runs", run["run_id"])
        with open(os.path.join(run_dir, "run.json"), "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(run, ensure_ascii=False, indent=2) + "\n")

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

    def session_payload(self):
        run = self.runs.get(self.current_run_id)
        if run is None:
            return {"session_id": self.session_id, "phase": "idle", "active": False, "run": None}
        base = run.get("client_click_epoch_ms") or run.get("start_request_received_epoch_ms")
        elapsed = None
        if run["status"] == "active" and base:
            elapsed = round(time.time() * 1000 - base, 1)
        last = run["queries"][-1] if run["queries"] else None
        return {
            "session_id": self.session_id,
            "phase": "active" if run["status"] == "active" else "ended",
            "active": run["status"] == "active",
            "run": {
                "run_id": run["run_id"], "task_id": run["task_id"], "question": run["question"],
                "status": run["status"], "outcome": run["outcome"],
                "started_at": run["started_at"], "elapsed_ms": elapsed,
                "init_ms": run["init_ms"], "config_id": run["config_id"],
                "query_count": len(run["queries"]),
                "selected_evidence": run["selected_evidence"],
                "last_result": None if last is None else {
                    "decision": last["decision"], "message": last["message"],
                    "search_ms": last["search_ms"], "evidence": last["evidence"],
                },
            },
        }


APP = None


class Handler(BaseHTTPRequestHandler):
    server_version = "HCS-UX/1.1"

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
        if path == "/api/session":
            self.send_json(200, APP.session_payload())
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
        path = urlparse(self.path).path
        body = self.read_json()
        recv_epoch_ms = int(time.time() * 1000)
        if path == "/api/start":
            task_id = body.get("task_id")
            run, err = APP.new_run(task_id, recv_epoch_ms, body.get("client_click_epoch_ms"))
            if err == "session_active":
                self.send_json(409, {"error": "session_active",
                                     "active_run_id": APP.current_run_id,
                                     "message": "已有进行中的任务；请先结束或中止，再开始新任务。"})
                return
            if err:
                self.send_json(400, {"error": err})
                return
            with APP.lock:
                run["start_response_sent_at"] = datetime.now().astimezone().isoformat()
            APP.event(run, "start_response_sent", {
                "server_received_epoch_ms": recv_epoch_ms,
                "sent_at": run["start_response_sent_at"],
            })
            self.send_json(200, {
                "run_id": run["run_id"], "question": run["question"],
                "init_ms": APP.init_ms, "ready_at": APP.ready_at,
                "method": METHOD, "auto_supplement": AUTO_SUPPLEMENT,
                "config_id": APP.config_id,
                "server_received_epoch_ms": recv_epoch_ms,
                "clock_note": CLOCK_NOTE,
            })
            return
        if path == "/api/event":
            run_id = body.get("run_id")
            run = APP.runs.get(run_id) if run_id else None
            if run_id and run is None:
                APP.reject(None, "event_rejected", {"reason": "run_not_found", "run_id": run_id,
                                                    "type": body.get("type")})
                self.send_json(404, {"error": "run_not_found"})
                return
            APP.event(run, body.get("type") or "client_event", {
                k: v for k, v in body.items() if k not in ("run_id", "type")})
            self.send_json(200, {"ok": True})
            return
        if path == "/api/search":
            run_id = body.get("run_id")
            run = APP.runs.get(run_id) if run_id else None
            if run is None:
                APP.reject(None, "search_rejected", {"reason": "run_not_found", "run_id": run_id,
                                                     "phase": APP.phase()})
                self.send_json(404, {"error": "run_not_found", "message": "未开始任务，或运行编号不存在。"})
                return
            if run["status"] != "active":
                APP.reject(run, "search_rejected", {"reason": "run_not_active", "run_id": run["run_id"]})
                self.send_json(409, {"error": "run_not_active"})
                return
            q = (body.get("question") or "").strip()
            if q != run["question"]:
                APP.reject(run, "question_mismatch", {"submitted": q})
                self.send_json(400, {"error": "本页只验证已见任务，问题必须与题面一致"})
                return
            now = time.time()
            if run.get("last_search_ts") and now - run["last_search_ts"] < 1.2:
                APP.reject(run, "duplicate_query", {"question": q})
                self.send_json(409, {"error": "重复提交已记录；请稍后再查或使用再次查询"})
                return
            run["last_search_ts"] = now
            APP.event(run, "query_submitted", {"question": q,
                                               "request_received_epoch_ms": recv_epoch_ms})
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
            with APP.lock:
                run["queries"].append({
                    "question": q, "decision": decision, "search_ms": search_ms,
                    "evidence": evidence, "message": message,
                })
                for e in evidence:
                    if e["article_id"] not in run["displayed_evidence"]:
                        run["displayed_evidence"].append(e["article_id"])
                APP._write_run(run)
            self.send_json(200, {
                "run_id": run["run_id"], "decision": decision, "message": message,
                "search_ms": search_ms, "evidence": evidence,
                "truncation_note": "每个证据最多展示 400 字符；truncated=true 表示有截断。",
            })
            return
        if path == "/api/end":
            run_id = body.get("run_id")
            run = APP.runs.get(run_id) if run_id else None
            if run is None:
                APP.reject(None, "end_rejected", {"reason": "run_not_found", "run_id": run_id,
                                                  "phase": APP.phase()})
                self.send_json(404, {"error": "run_not_found"})
                return
            if run["status"] != "active":
                APP.reject(run, "end_rejected", {"reason": "already_ended",
                                                 "existing_outcome": run["outcome"],
                                                 "attempted_outcome": body.get("outcome")})
                self.send_json(409, {"error": "run_already_ended",
                                     "outcome": run["outcome"],
                                     "ended_at": run["ended_at"]})
                return
            outcome = body.get("outcome")
            if outcome not in ("found", "not_found", "aborted"):
                APP.reject(run, "end_rejected", {"reason": "invalid_outcome",
                                                 "attempted_outcome": outcome})
                self.send_json(400, {"error": "invalid_outcome"})
                return
            selected = body.get("selected_evidence") or []
            if not isinstance(selected, list):
                selected = []
            displayed = set(run.get("displayed_evidence") or [])
            unknown = [x for x in selected if x not in displayed]
            if unknown:
                APP.reject(run, "end_rejected", {"reason": "evidence_not_in_displayed_results",
                                                 "ids": unknown,
                                                 "displayed_evidence": sorted(displayed)})
                self.send_json(400, {"error": "evidence_not_in_displayed_results", "ids": unknown,
                                     "message": "所选证据不在本任务实际展示的结果中；已记录，未结束任务。"})
                return
            with APP.lock:
                clock_base = run.get("client_click_epoch_ms") or run["start_request_received_epoch_ms"]
                run["status"] = "ended"
                run["phase"] = "ended"
                run["outcome"] = outcome
                run["selected_evidence"] = selected
                run["ended_at"] = datetime.now().astimezone().isoformat()
                run["end_request_received_epoch_ms"] = recv_epoch_ms
                run["duration_ms"] = round(recv_epoch_ms - clock_base, 1)
                run["duration_server_ms"] = round(recv_epoch_ms - run["start_request_received_epoch_ms"], 1)
                run["duration_client_reported_ms"] = body.get("client_elapsed_ms")
                run["end_click_epoch_ms"] = body.get("end_click_epoch_ms")
                APP.current_run_id = None
            APP.event(run, "task_ended", {
                "outcome": outcome, "selected_evidence": selected,
                "note": body.get("note", ""), "duration_ms": run["duration_ms"],
                "duration_server_ms": run["duration_server_ms"],
                "duration_client_reported_ms": run["duration_client_reported_ms"],
                "timer_basis": run["timer_basis"],
                "end_request_received_epoch_ms": recv_epoch_ms,
                "clock_note": CLOCK_NOTE,
                "after_run_end": False,
            })
            self.send_json(200, {
                "run_id": run["run_id"], "outcome": outcome,
                "selected_evidence": selected, "duration_ms": run["duration_ms"],
                "duration_server_ms": run["duration_server_ms"],
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
    print("ready=%s init_ms=%.1f config_id=%s session_id=%s"
          % (APP.ready_at, APP.init_ms, APP.config_id, APP.session_id))
    print("http://127.0.0.1:%d/" % args.port, flush=True)
    ThreadingHTTPServer((args.host, args.port), Handler).serve_forever()


if __name__ == "__main__":
    sys.exit(main() or 0)
