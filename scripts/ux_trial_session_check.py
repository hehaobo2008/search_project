"""会话管理实测脚本：真实调用回环服务与真实检索，覆盖连续两轮/重复点击/刷新/中止。

不修改模型、语料、排序或拒绝规则；只对本机 127.0.0.1 的验证页接口发请求。
用法：python scripts/ux_trial_session_check.py
退出码：0 全部 PASS；1 存在 FAIL。
"""
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = 8766
BASE = "http://127.0.0.1:%d" % PORT
RUNS = os.path.join(ROOT, "logs", "ux_trial", "runs")
RESULTS = []


def record(name, ok, detail=""):
    RESULTS.append({"scenario": name, "pass": bool(ok), "detail": detail})
    print(("[PASS] " if ok else "[FAIL] ") + name + ("  " + detail if detail else ""))


def post(path, body):
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(BASE + path, data=data, method="POST",
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8")
        try:
            return e.code, json.loads(raw or "{}")
        except Exception:
            return e.code, {"raw": raw}


def get(path):
    with urllib.request.urlopen(BASE + path, timeout=60) as r:
        return r.status, json.loads(r.read().decode("utf-8"))


def events(run_id):
    p = os.path.join(RUNS, run_id, "events.jsonl")
    if not os.path.isfile(p):
        return []
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]


def run_json(run_id):
    p = os.path.join(RUNS, run_id, "run.json")
    return json.load(open(p, encoding="utf-8"))


def has_event(run_id, name):
    return any(e.get("event") == name for e in events(run_id))


def rejected_lines():
    p = os.path.join(ROOT, "logs", "ux_trial", "rejected_events.jsonl")
    if not os.path.isfile(p):
        return []
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]


def start(task_id):
    click = int(time.time() * 1000)
    code, body = post("/api/start", {"task_id": task_id, "client_click_epoch_ms": click})
    return code, body, click


def wait_ready(proc):
    line = ""
    t0 = time.time()
    while time.time() - t0 < 120:
        line = proc.stdout.readline()
        if not line:
            if proc.poll() is not None:
                raise RuntimeError("服务进程提前退出")
            continue
        if "http://127.0.0.1" in line:
            return
    raise RuntimeError("服务未就绪")


def main():
    proc = subprocess.Popen([sys.executable, os.path.join(ROOT, "scripts", "ux_trial_server.py"),
                             "--port", str(PORT)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, encoding="utf-8", bufsize=1)
    try:
        wait_ready(proc)

        # 场景 1：连续两轮，run 独立
        code1, r1, click1 = start("task1")
        record("S1 第一轮开始", code1 == 200, "run_id=%s" % r1.get("run_id"))
        code, q1 = post("/api/search", {"run_id": r1["run_id"], "question": r1["question"]})
        record("S1 第一轮检索", code == 200 and q1.get("decision") == "answer",
               "decision=%s n=%d" % (q1.get("decision"), len(q1.get("evidence") or [])))
        code, e1 = post("/api/end", {"run_id": r1["run_id"], "outcome": "found",
                                     "selected_evidence": ["rail_quality:art-8"],
                                     "note": "会话检查：第一轮"})
        record("S1 第一轮结束", code == 200 and e1.get("outcome") == "found",
               "duration_ms=%s" % e1.get("duration_ms"))

        code2, r2, click2 = start("task2")
        record("S1 第二轮开始（新 run）", code2 == 200 and r2["run_id"] != r1["run_id"],
               "%s -> %s" % (r1["run_id"], r2["run_id"]))
        code, q2 = post("/api/search", {"run_id": r2["run_id"], "question": r2["question"]})
        record("S1 第二轮检索", code == 200 and q2.get("decision") == "answer",
               "first=%s" % (q2.get("evidence") or [{}])[0].get("article_id"))
        code, e2 = post("/api/end", {"run_id": r2["run_id"], "outcome": "found",
                                     "selected_evidence": ["rail_quality:art-61"],
                                     "note": "会话检查：第二轮"})
        record("S1 第二轮结束", code == 200, "duration_ms=%s" % e2.get("duration_ms"))

        ev1 = {e["run_id"] for e in events(r1["run_id"])}
        ev2 = {e["run_id"] for e in events(r2["run_id"])}
        record("S1 两轮日志不串", ev1 == {r1["run_id"]} and ev2 == {r2["run_id"]},
               "run1 事件数=%d, run2 事件数=%d" % (len(events(r1["run_id"])), len(events(r2["run_id"]))))

        # 场景 2：进行中不能开始新任务
        code3, r3, _ = start("task3")
        record("S2 第三轮开始", code3 == 200, "run_id=%s" % r3.get("run_id"))
        code, again = post("/api/start", {"task_id": "task1", "client_click_epoch_ms": int(time.time() * 1000)})
        record("S2 进行中重复开始被拒", code == 409 and again.get("error") == "session_active",
               "code=%s error=%s" % (code, again.get("error")))
        record("S2 拒绝事件已落盘", has_event(r3["run_id"], "start_rejected"), "start_rejected")

        # 场景 3：重复结束
        code, q3 = post("/api/search", {"run_id": r3["run_id"], "question": r3["question"]})
        record("S3 第三轮检索", code == 200 and q3.get("decision") == "refuse",
               "decision=%s" % q3.get("decision"))
        code, end_ok = post("/api/end", {"run_id": r3["run_id"], "outcome": "not_found", "selected_evidence": []})
        record("S3 第三轮结束", code == 200 and end_ok.get("outcome") == "not_found", "duration_ms=%s" % end_ok.get("duration_ms"))
        before = run_json(r3["run_id"])
        code, dup = post("/api/end", {"run_id": r3["run_id"], "outcome": "found",
                                      "selected_evidence": []})
        after = run_json(r3["run_id"])
        record("S3 重复结束被拒", code == 409 and dup.get("error") == "run_already_ended",
               "code=%s error=%s" % (code, dup.get("error")))
        record("S3 原结束状态未被改写",
               before["outcome"] == after["outcome"] == "not_found"
               and before["duration_ms"] == after["duration_ms"]
               and before["ended_at"] == after["ended_at"],
               "outcome=%s duration=%s" % (after["outcome"], after["duration_ms"]))
        record("S3 重复结束留痕", has_event(r3["run_id"], "end_rejected"), "end_rejected")

        # 场景 4：未开始就操作
        code, s404 = post("/api/search", {"run_id": "ux-does-not-exist", "question": "任意"})
        record("S4 未开始检索被拒", code == 404, "code=%s" % code)
        code, e404 = post("/api/end", {"run_id": "ux-does-not-exist", "outcome": "found"})
        record("S4 未开始结束被拒", code == 404, "code=%s" % code)
        kinds = [x.get("event") for x in rejected_lines()]
        record("S4 拒绝记录保留", "search_rejected" in kinds and "end_rejected" in kinds,
               "rejected_events 共 %d 条" % len(kinds))

        # 场景 5：不属于展示结果的证据
        code4, r4, _ = start("task1")
        post("/api/search", {"run_id": r4["run_id"], "question": r4["question"]})
        code, bad = post("/api/end", {"run_id": r4["run_id"], "outcome": "found",
                                      "selected_evidence": ["rail_quality:art-999"]})
        record("S5 非法证据 ID 被拒", code == 400 and bad.get("error") == "evidence_not_in_displayed_results",
               "code=%s ids=%s" % (code, bad.get("ids")))
        record("S5 拒绝后任务仍为 active", run_json(r4["run_id"])["status"] == "active",
               "status=%s" % run_json(r4["run_id"])["status"])
        code, ok = post("/api/end", {"run_id": r4["run_id"], "outcome": "found",
                                     "selected_evidence": ["rail_quality:art-8"]})
        record("S5 合法证据可结束", code == 200, "outcome=%s" % ok.get("outcome"))

        # 场景 6：中止
        code5, r5, _ = start("task2")
        code, ab = post("/api/end", {"run_id": r5["run_id"], "outcome": "aborted",
                                     "selected_evidence": [], "note": "会话检查：中止"})
        record("S6 中止被记录", code == 200 and ab.get("outcome") == "aborted",
               "outcome=%s" % ab.get("outcome"))
        j5 = run_json(r5["run_id"])
        record("S6 中止后状态", j5["status"] == "ended" and j5["outcome"] == "aborted",
               "status=%s outcome=%s" % (j5["status"], j5["outcome"]))

        # 场景 7：刷新（服务端侧恢复）
        code6, r6, click6 = start("task1")
        _, sess = get("/api/session")
        record("S7 刷新后会话可发现", sess.get("active") is True and sess["run"]["run_id"] == r6["run_id"],
               "active=%s run=%s" % (sess.get("active"), (sess.get("run") or {}).get("run_id")))
        record("S7 会话带已进行时长", isinstance(sess["run"].get("elapsed_ms"), (int, float))
               and sess["run"]["elapsed_ms"] > 0, "elapsed_ms=%s" % sess["run"].get("elapsed_ms"))
        post("/api/event", {"run_id": r6["run_id"], "type": "page_reloaded"})
        record("S7 刷新事件写入原 run", has_event(r6["run_id"], "page_reloaded"), "page_reloaded")
        post("/api/end", {"run_id": r6["run_id"], "outcome": "aborted", "selected_evidence": [],
                          "note": "会话检查：刷新后清理"})

        # 场景 8：计时时间戳
        j1 = run_json(r1["run_id"])
        click_ms = j1.get("client_click_epoch_ms")
        recv_ms = j1.get("start_request_received_epoch_ms")
        record("S8 记录点击与服务端收到时刻",
               isinstance(click_ms, (int, float)) and isinstance(recv_ms, (int, float)),
               "click=%s recv=%s delta=%s ms" % (click_ms, recv_ms,
                                                 None if not (click_ms and recv_ms) else recv_ms - click_ms))
        record("S8 duration 起点为点击时刻",
               j1.get("duration_ms") >= j1.get("duration_server_ms"), "duration=%s server=%s"
               % (j1.get("duration_ms"), j1.get("duration_server_ms")))
        record("S8 计时基础与说明已写入", j1.get("timer_basis") == "client_click" and bool(j1.get("clock_note")),
               "timer_basis=%s" % j1.get("timer_basis"))

        failed = [r for r in RESULTS if not r["pass"]]
        print("\n汇总：%d 项，PASS %d，FAIL %d" % (len(RESULTS), len(RESULTS) - len(failed), len(failed)))
        print("本次运行编号：%s" % ", ".join([r1["run_id"], r2["run_id"], r3["run_id"], r4["run_id"],
                                              r5["run_id"], r6["run_id"]]))
        out = os.path.join(ROOT, "logs", "ux_trial", "session_check_result.json")
        json.dump({"results": RESULTS, "runs": [r1["run_id"], r2["run_id"], r3["run_id"],
                                                r4["run_id"], r5["run_id"], r6["run_id"]]},
                  open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print("结果文件：%s" % os.path.relpath(out, ROOT).replace("\\", "/"))
        return 0 if not failed else 1
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except Exception:
            proc.kill()


if __name__ == "__main__":
    sys.exit(main())
