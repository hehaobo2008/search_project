"""结束竞态实测：慢搜索时结束、并发重复结束、结束后迟到响应。

真实调用回环服务与真实检索；用 --search-delay-ms 在检索前注入固定延时以稳定复现竞态窗口
（该延时只用于测试，不改变检索方法；日志里记为 test_search_delay_applied）。

用法：python scripts/ux_trial_race_check.py
退出码：0 全部 PASS；1 存在 FAIL。
"""
import json
import os
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = 8767
BASE = "http://127.0.0.1:%d" % PORT
RUNS = os.path.join(ROOT, "logs", "ux_trial", "runs")
DELAY_MS = 1200
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


def events(run_id):
    p = os.path.join(RUNS, run_id, "events.jsonl")
    if not os.path.isfile(p):
        return []
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]


def run_json(run_id):
    return json.load(open(os.path.join(RUNS, run_id, "run.json"), encoding="utf-8"))


def names(run_id):
    return [e.get("event") for e in events(run_id)]


def start(task_id):
    click = int(time.time() * 1000)
    return post("/api/start", {"task_id": task_id, "client_click_epoch_ms": click})


def wait_ready(proc):
    t0 = time.time()
    while time.time() - t0 < 180:
        line = proc.stdout.readline()
        if not line:
            if proc.poll() is not None:
                raise RuntimeError("服务进程提前退出")
            continue
        if "http://127.0.0.1" in line:
            return line
    raise RuntimeError("服务未就绪")


def main():
    proc = subprocess.Popen([sys.executable, os.path.join(ROOT, "scripts", "ux_trial_server.py"),
                             "--port", str(PORT), "--search-delay-ms", str(DELAY_MS)],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, encoding="utf-8", bufsize=1)
    try:
        wait_ready(proc)
        runs = []

        # S1：慢搜索中点击结束（不取消）→ 拒绝，等搜索完成后可正常结束
        code, r1 = start("task1")
        runs.append(r1["run_id"])
        box = {}

        def s1_search():
            box["search"] = post("/api/search", {"run_id": r1["run_id"], "question": r1["question"]})

        t = threading.Thread(target=s1_search)
        t.start()
        time.sleep(0.35)
        code_end, end1 = post("/api/end", {"run_id": r1["run_id"], "outcome": "found",
                                           "selected_evidence": []})
        record("S1 慢搜索中结束被拒", code_end == 409 and end1.get("error") == "search_in_progress",
               "code=%s error=%s" % (code_end, end1.get("error")))
        record("S1 拒绝后任务仍 active", run_json(r1["run_id"])["status"] == "active",
               "status=%s" % run_json(r1["run_id"])["status"])
        t.join(60)
        sc, sb = box.get("search", (0, {}))
        record("S1 搜索本身正常返回", sc == 200 and sb.get("decision") == "answer",
               "code=%s decision=%s" % (sc, sb.get("decision")))
        record("S1 结果已写入", len(run_json(r1["run_id"])["queries"]) == 1,
               "queries=%d" % len(run_json(r1["run_id"])["queries"]))
        code, end2 = post("/api/end", {"run_id": r1["run_id"], "outcome": "found",
                                       "selected_evidence": ["rail_quality:art-8"]})
        record("S1 搜索结束后可正常结束", code == 200 and end2.get("outcome") == "found",
               "duration_ms=%s" % end2.get("duration_ms"))
        record("S1 拒绝事件已落盘", "end_rejected" in names(r1["run_id"]), "end_rejected")

        # S2：慢搜索中显式取消并结束 → 迟到结果被丢弃，不写入、不返回
        code, r2 = start("task2")
        runs.append(r2["run_id"])
        box2 = {}

        def s2_search():
            box2["search"] = post("/api/search", {"run_id": r2["run_id"], "question": r2["question"]})

        t = threading.Thread(target=s2_search)
        t.start()
        time.sleep(0.35)
        code_cancel, end3 = post("/api/end", {"run_id": r2["run_id"], "outcome": "aborted",
                                              "selected_evidence": [], "cancel_search": True})
        record("S2 取消搜索并结束成功", code_cancel == 200 and end3.get("outcome") == "aborted",
               "code=%s cancelled_token=%s" % (code_cancel, end3.get("cancelled_search_token")))
        t.join(60)
        sc2, sb2 = box2.get("search", (0, {}))
        record("S2 迟到响应被丢弃", sc2 == 409 and sb2.get("error") == "search_discarded",
               "code=%s error=%s" % (sc2, sb2.get("error")))
        j2 = run_json(r2["run_id"])
        record("S2 结束后的结果未写入", len(j2["queries"]) == 0 and len(j2["displayed_evidence"]) == 0,
               "queries=%d displayed=%d" % (len(j2["queries"]), len(j2["displayed_evidence"])))
        n2 = names(r2["run_id"])
        record("S2 取消与丢弃均有留痕", "search_cancelled" in n2 and "search_result_discarded" in n2,
               "events=%s" % ",".join(x for x in n2 if "search" in x))

        # S3：并发重复结束，只有一个成功
        code, r3 = start("task1")
        runs.append(r3["run_id"])
        post("/api/search", {"run_id": r3["run_id"], "question": r3["question"]})
        outs = []

        def fire():
            outs.append(post("/api/end", {"run_id": r3["run_id"], "outcome": "found",
                                          "selected_evidence": ["rail_quality:art-8"]}))

        threads = [threading.Thread(target=fire) for _ in range(4)]
        for th in threads:
            th.start()
        for th in threads:
            th.join(30)
        ok200 = [o for o in outs if o[0] == 200]
        rejected = [o for o in outs if o[0] == 409]
        record("S3 并发结束只有一个成功", len(ok200) == 1 and len(rejected) == 3,
               "200=%d 409=%d" % (len(ok200), len(rejected)))
        j3 = run_json(r3["run_id"])
        n3 = names(r3["run_id"])
        record("S3 只写入一次结束状态",
               j3["status"] == "ended" and n3.count("task_ended") == 1,
               "task_ended=%d end_rejected=%d" % (n3.count("task_ended"), n3.count("end_rejected")))
        c3, r3b = start("task3")
        record("S3 并发后可继续开始新任务", c3 == 200, "run=%s" % r3b.get("run_id"))
        runs.append(r3b["run_id"])
        post("/api/end", {"run_id": r3b["run_id"], "outcome": "aborted", "selected_evidence": []})

        # S4：结束后再发搜索（迟到请求）
        r4_code, r4 = start("task2")
        runs.append(r4["run_id"])
        post("/api/search", {"run_id": r4["run_id"], "question": r4["question"]})
        post("/api/end", {"run_id": r4["run_id"], "outcome": "found",
                          "selected_evidence": ["rail_quality:art-61"]})
        before = len(run_json(r4["run_id"])["queries"])
        code_late, late = post("/api/search", {"run_id": r4["run_id"], "question": r4["question"]})
        after = len(run_json(r4["run_id"])["queries"])
        record("S4 结束后的搜索被拒", code_late == 409 and late.get("error") == "run_not_active",
               "code=%s" % code_late)
        record("S4 结束后未新增查询记录", before == after == 1, "before=%d after=%d" % (before, after))

        # S5：并发重复搜索，只接受一个
        code, r5 = start("task1")
        runs.append(r5["run_id"])
        outs5 = []

        def fire_search():
            outs5.append(post("/api/search", {"run_id": r5["run_id"], "question": r5["question"]}))

        threads = [threading.Thread(target=fire_search) for _ in range(3)]
        for th in threads:
            th.start()
        for th in threads:
            th.join(60)
        ok5 = [o for o in outs5 if o[0] == 200]
        rej5 = [o for o in outs5 if o[0] == 409]
        record("S5 并发搜索只接受一个", len(ok5) == 1 and len(rej5) == 2,
               "200=%d 409=%d" % (len(ok5), len(rej5)))
        record("S5 只写入一条查询", len(run_json(r5["run_id"])["queries"]) == 1,
               "queries=%d" % len(run_json(r5["run_id"])["queries"]))
        post("/api/end", {"run_id": r5["run_id"], "outcome": "found", "selected_evidence": []})

        # S6：计时口径
        j1 = run_json(r1["run_id"])
        record("S6 duration 含往返且不小于服务端值",
               j1["duration_ms"] >= j1["duration_server_ms"] > 0,
               "duration=%s server=%s" % (j1["duration_ms"], j1["duration_server_ms"]))
        record("S6 注入延时已标注", "test_search_delay_applied" in names(r1["run_id"]),
               "delay_ms=%d" % DELAY_MS)
        rr = [e for e in events(r1["run_id"]) if e.get("event") == "results_ready"]
        record("S6 结果事件标注未经核对", bool(rr) and rr[0].get("displayed_is_not_reviewed") is True,
               "displayed_is_not_reviewed=%s" % (rr[0].get("displayed_is_not_reviewed") if rr else None))

        failed = [x for x in RESULTS if not x["pass"]]
        print("\n汇总：%d 项，PASS %d，FAIL %d" % (len(RESULTS), len(RESULTS) - len(failed), len(failed)))
        print("运行编号：%s" % ", ".join([r for r in runs if r]))
        out = os.path.join(ROOT, "logs", "ux_trial", "race_check_result.json")
        json.dump({"results": RESULTS, "runs": [r for r in runs if r], "search_delay_ms": DELAY_MS},
                  open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print("结果文件：logs/ux_trial/race_check_result.json")
        return 0 if not failed else 1
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except Exception:
            proc.kill()


if __name__ == "__main__":
    sys.exit(main())
