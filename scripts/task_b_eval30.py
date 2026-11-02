import hashlib
import json
import os
import sys
import time
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from task_b_system import TaskBSystem  # noqa: E402

QUESTIONS = os.path.join(ROOT, "data", "task_b_eval30_questions.jsonl")
FREEZE = os.path.join(ROOT, "reports", "task_b_eval30_freeze_manifest.json")
RESULTS = os.path.join(ROOT, "reports", "task_b_eval30_results.json")
REPORT = os.path.join(ROOT, "reports", "task_b_eval30_report.md")
LOG_ROOT = os.path.join(ROOT, "logs", "task_b_eval30")

METHODS = ["bm25_top7", "dense_top7", "hybrid_top7", "hybrid_top5_supplement"]
AUX = ["hybrid_top5"]
LABELS = {
    "bm25_top7": "纯BM25 Top7",
    "dense_top7": "纯语义 Top7",
    "hybrid_top7": "混合 Top7",
    "hybrid_top5_supplement": "混合 Top5+≤2补证",
    "hybrid_top5": "混合 Top5（补证基线）",
}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def requirement_result(units, req):
    acceptable = req["acceptable"]
    candidates = [u for u in units if u["article_id"] in acceptable]
    terms = req.get("display_terms", [])
    display_hits = [u for u in candidates if all(t in u["text"] for t in terms)]
    missing_terms = []
    if candidates and not display_hits:
        missing_terms = [t for t in terms if not any(t in u["text"] for u in candidates)]
    return {
        "aspect": req["aspect"],
        "acceptable": acceptable,
        "display_terms": terms,
        "id_hit": bool(candidates),
        "display_hit": bool(display_hits),
        "candidate_ids": [u["article_id"] for u in candidates],
        "display_ids": [u["article_id"] for u in display_hits],
        "missing_terms_in_returned_acceptable": missing_terms,
        "truncated_candidates": [u["article_id"] for u in candidates if u.get("truncated")],
    }


def evaluate_units(units, reqs):
    details = [requirement_result(units, req) for req in reqs]
    return {
        "requirements": details,
        "full_id": all(d["id_hit"] for d in details),
        "full_display": all(d["display_hit"] for d in details),
        "aspects_display": sum(1 for d in details if d["display_hit"]),
        "aspects_total": len(details),
        "missing_display": [d["aspect"] for d in details if not d["display_hit"]],
        "id_display_gap": any(d["id_hit"] and not d["display_hit"] for d in details),
    }


def main():
    if not os.path.exists(FREEZE):
        print("REFUSE: freeze manifest missing")
        return 2
    freeze = json.load(open(FREEZE, encoding="utf-8"))
    if freeze.get("status") != "frozen_no_retrieval" or freeze.get("retrieval_run"):
        print("REFUSE: freeze manifest is not in frozen_no_retrieval state")
        return 2
    if sha256(QUESTIONS) != freeze["question_gold_file"]["sha256"]:
        print("REFUSE: question file changed after freeze")
        return 2
    rerun = "--rerun" in sys.argv
    reason = ""
    if "--reason" in sys.argv:
        reason = sys.argv[sys.argv.index("--reason") + 1]
    if os.path.exists(RESULTS) and not rerun:
        print("REFUSE: first-round results already exist; use --rerun --reason if fixing a run error")
        return 2
    if rerun and not reason:
        print("REFUSE: --rerun requires --reason")
        return 2

    run_id = os.environ.get("HCS_EVAL30_RUN_ID") or (
        "eval30-" + datetime.now().strftime("%Y%m%dT%H%M%S%z"))
    run_dir = os.path.join(LOG_ROOT, "runs", run_id)
    os.makedirs(run_dir, exist_ok=True)

    rows = [json.loads(line) for line in open(QUESTIONS, encoding="utf-8")]
    system = TaskBSystem()
    started = time.time()
    answerable_rows = []
    no_answer_rows = []
    failures = []

    for q in rows:
        if q["answerable"]:
            row = {"qid": q["qid"], "group": q["group"], "question": q["question"],
                   "requirements": q["requirements"], "methods": {}}
            for method in METHODS + AUX:
                result = system.answer(q["question"], method)
                units = result["evidence"]
                ev = evaluate_units(units, q["requirements"])
                supplements = units[5:] if method == "hybrid_top5_supplement" else []
                allowed = {aid for req in q["requirements"] for aid in req["acceptable"]}
                wrong_supp = [u["article_id"] for u in supplements
                              if u["article_id"] not in allowed]
                row["methods"][method] = {
                    "decision": result["decision"],
                    "full_id": ev["full_id"],
                    "full_display": ev["full_display"],
                    "aspects_display": ev["aspects_display"],
                    "aspects_total": ev["aspects_total"],
                    "missing_display": ev["missing_display"],
                    "id_display_gap": ev["id_display_gap"],
                    "requirements": ev["requirements"],
                    "ids": [u["article_id"] for u in units],
                    "units": len(units),
                    "chars": sum(u["chars"] for u in units),
                    "truncated_ids": [u["article_id"] for u in units if u.get("truncated")],
                    "supplement_ids": [u["article_id"] for u in supplements],
                    "supplement_count": len(supplements),
                    "wrong_supplement_ids": wrong_supp,
                    "timings": result["timings"],
                }
                if result["decision"] == "refuse":
                    failures.append({"qid": q["qid"], "method": method,
                                     "failure": "answerable_refused"})
                elif not ev["full_display"]:
                    failures.append({"qid": q["qid"], "method": method,
                                     "failure": "missing_requirements",
                                     "detail": ev["missing_display"]})
                if ev["id_display_gap"]:
                    failures.append({"qid": q["qid"], "method": method,
                                     "failure": "id_hit_but_display_insufficient",
                                     "detail": [d["aspect"] for d in ev["requirements"]
                                                if d["id_hit"] and not d["display_hit"]]})
                if wrong_supp:
                    failures.append({"qid": q["qid"], "method": method,
                                     "failure": "wrong_supplement",
                                     "detail": wrong_supp})
            # supplement gain vs top5/top7
            supp = row["methods"]["hybrid_top5_supplement"]
            top5 = row["methods"]["hybrid_top5"]
            top7 = row["methods"]["hybrid_top7"]
            base_units = system.answer(q["question"], "hybrid_top5")["evidence"]
            new_cov = 0
            for req in q["requirements"]:
                base_ok = requirement_result(base_units, req)["display_hit"]
                supp_ok = next(d for d in supp["requirements"] if d["aspect"] == req["aspect"])["display_hit"]
                if supp_ok and not base_ok:
                    new_cov += 1
            supp["supplement_covered_new_aspects"] = new_cov
            supp["gain_vs_top5"] = supp["full_display"] and not top5["full_display"]
            supp["loss_vs_top5"] = top5["full_display"] and not supp["full_display"]
            supp["gain_vs_top7"] = supp["full_display"] and not top7["full_display"]
            supp["loss_vs_top7"] = top7["full_display"] and not supp["full_display"]
            answerable_rows.append(row)
        else:
            row = {"qid": q["qid"], "group": q["group"], "question": q["question"],
                   "methods": {}}
            for method in METHODS + AUX:
                result = system.answer(q["question"], method)
                row["methods"][method] = {
                    "decision": result["decision"],
                    "evidence_ids": [u["article_id"] for u in result["evidence"]],
                }
                if result["decision"] != "refuse":
           
                    failures.append({"qid": q["qid"], "method": method,
                                     "failure": "no_answer_wrong_evidence",
                                     "detail": [u["article_id"] for u in result["evidence"]]})
            no_answer_rows.append(row)

    summary = {}
    for method in METHODS + AUX:
        full_display = sum(1 for r in answerable_rows if r["methods"][method]["full_display"])
        full_id = sum(1 for r in answerable_rows if r["methods"][method]["full_id"])
        refused = sum(1 for r in answerable_rows if r["methods"][method]["decision"] == "refuse")
        gaps = sum(1 for r in answerable_rows if r["methods"][method]["id_display_gap"])
        missed = sum(len(r["methods"][method]["missing_display"]) for r in answerable_rows)
        aspects_hit = sum(r["methods"][method]["aspects_display"] for r in answerable_rows)
        aspects_total = sum(r["methods"][method]["aspects_total"] for r in answerable_rows)
        no_answer_wrong = sum(1 for r in no_answer_rows
                              if r["methods"][method]["decision"] != "refuse")
        summary[method] = {
            "answerable_n": len(answerable_rows),
            "full_display": full_display,
            "full_id": full_id,
            "answerable_refused": refused,
            "id_display_gap": gaps,
            "missed_requirements": missed,
            "aspects_display": aspects_hit,
            "aspects_total": aspects_total,
            "no_answer_n": len(no_answer_rows),
            "no_answer_wrong_evidence": no_answer_wrong,
        }
        if method == "hybrid_top5_supplement":
            summary[method].update({
                "supplement_units": sum(r["methods"][method]["supplement_count"] for r in answerable_rows),
                "wrong_supplement_units": sum(len(r["methods"][method]["wrong_supplement_ids"])
                                              for r in answerable_rows),
                "supplement_gain_vs_top5": sum(1 for r in answerable_rows
                                                if r["methods"][method]["gain_vs_top5"]),
                "supplement_loss_vs_top5": sum(1 for r in answerable_rows
                                                if r["methods"][method]["loss_vs_top5"]),
                "supplement_gain_vs_top7": sum(1 for r in answerable_rows
                                                if r["methods"][method]["gain_vs_top7"]),
                "supplement_loss_vs_top7": sum(1 for r in answerable_rows
                                                if r["methods"][method]["loss_vs_top7"]),
                "supplement_new_aspects": sum(r["methods"][method]["supplement_covered_new_aspects"]
                                              for r in answerable_rows),
                "supplement_triggered_questions": sum(1 for r in answerable_rows
                                                      if r["methods"][method]["supplement_count"] > 0),
            })

    result = {
        "run_id": run_id,
        "generated_at": datetime.now().astimezone().isoformat(),
        "freeze_batch": freeze["batch"],
        "freeze_questions_only_sha256": freeze["questions_only_sha256"],
        "freeze_gold_sha256": freeze["gold_sha256"],
        "question_file_sha256": sha256(QUESTIONS),
        "retrieval_run": True,
        "rerun": rerun,
        "rerun_reason": reason,
        "disclaimer": "首轮四方法对照；不得用本轮结果调参覆盖首轮。新题均为同语料，不是产品准确率。",
        "summary": summary,
        "failures": failures,
        "answerable_rows": answerable_rows,
        "no_answer_rows": no_answer_rows,
    }

    if os.path.exists(RESULTS) and rerun:
        first = os.path.join(ROOT, "reports", "task_b_eval30_results_first.json")
        if not os.path.exists(first):
            import shutil
            shutil.copy2(RESULTS, first)
    open(RESULTS, "w", encoding="utf-8", newline="\n").write(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    open(os.path.join(run_dir, "raw.json"), "w", encoding="utf-8", newline="\n").write(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n")

    lines = [
        "# Eval30 首轮四方法对照结果",
        "",
        "> **同语料、非产品准确率、非独立跨主题测试。** 本轮为冻结后首轮运行，gold 只交给评分器，系统只接收问题和方法名。",
        "> 证据覆盖同时报告“条款 ID 命中”和“展示文字实际覆盖”；展示文字未包含校验词时，即使 ID 命中也不算充分。",
        "",
        "- run_id：`%s`" % run_id,
        "- 冻结 questions_only：`%s`" % freeze["questions_only_sha256"],
        "- 冻结 gold：`%s`" % freeze["gold_sha256"],
        "- 运行时长（共享模型/索引加载，不作为算法速度）：%.2f s" % (time.time() - started),
        "",
        "## 汇总",
        "",
        "| 方法 | 可回答N | 展示全证据 | ID全命中 | 漏项数 | 有答案被误拒 | ID命中但展示不足题数 | 无答案N | 无答案误出证据 |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for method in METHODS + AUX:
        s = summary[method]
        lines.append("| %s | %d | %d | %d | %d | %d | %d | %d | %d |" % (
            LABELS[method], s["answerable_n"], s["full_display"], s["full_id"],
            s["missed_requirements"], s["answerable_refused"], s["id_display_gap"],
            s["no_answer_n"], s["no_answer_wrong_evidence"]))
    lines += ["", "## 补证统计", ""]
    s = summary["hybrid_top5_supplement"]
    lines += [
        "- 触发补证的题数：%d/20；补证单元总数：%d；错误补证单元：%d。" % (
            s["supplement_triggered_questions"], s["supplement_units"], s["wrong_supplement_units"]),
        "- 相对混合 Top5：补证组独有覆盖 %d 题，丢失覆盖 %d 题，新增覆盖需求 %d 项。" % (
            s["supplement_gain_vs_top5"], s["supplement_loss_vs_top5"], s["supplement_new_aspects"]),
        "- 相对混合 Top7：补证组独有覆盖 %d 题，丢失覆盖 %d 题。" % (
            s["supplement_gain_vs_top7"], s["supplement_loss_vs_top7"]),
        "",
        "## 20 道可回答题逐题",
        "",
        "| qid | 需求组 | BM25 展示全/漏项/误拒 | 语义 展示全/漏项/误拒 | 混合 展示全/漏项/误拒 | 补证 展示全/漏项/误拒 |",
        "|---|---|---|---|---|---|",
    ]
    for r in answerable_rows:
        cells = []
        for method in METHODS:
            m = r["methods"][method]
            cells.append("%s/%d/%s" % (m["full_display"], len(m["missing_display"]),
                                       m["decision"] == "refuse"))
        lines.append("| %s | %d | %s |" % (r["qid"], len(r["requirements"]), " | ".join(cells)))
    lines += ["", "## 10 道无答案题", "",
              "| qid | BM25 | 语义 | 混合 | 补证 |", "|---|---|---|---|---|"]
    for r in no_answer_rows:
        cells = [r["methods"][m]["decision"] for m in METHODS]
        lines.append("| %s | %s |" % (r["qid"], " | ".join(cells)))
    lines += ["", "## 失败明细", ""]
    if failures:
        for f in failures:
            lines.append("- `%s` / %s：%s %s" % (
                f["qid"], f["method"], f["failure"], f.get("detail", "")))
    else:
        lines.append("- 无失败项。")

    open(REPORT, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
    latest = os.path.join(LOG_ROOT, "run_manifest.json")
    os.makedirs(LOG_ROOT, exist_ok=True)
    run_manifest = {
        "run_id": run_id,
        "generated_at": result["generated_at"],
        "freeze": freeze,
        "result_file": "reports/task_b_eval30_results.json",
        "report_file": "reports/task_b_eval30_report.md",
        "run_dir": os.path.relpath(run_dir, ROOT).replace("\\", "/"),
        "rerun": rerun,
        "rerun_reason": reason,
        "no_tuning": True,
        "shared_refusal_rule": True,
    }
    open(latest, "w", encoding="utf-8", newline="\n").write(
        json.dumps(run_manifest, ensure_ascii=False, indent=2) + "\n")
    open(os.path.join(run_dir, "run_manifest.json"), "w", encoding="utf-8", newline="\n").write(
        json.dumps(run_manifest, ensure_ascii=False, indent=2) + "\n")

    print("run_id=%s" % run_id)
    for method in METHODS:
        s = summary[method]
        print("%-24s full_display=%d/%d full_id=%d/%d missed=%d refused=%d gaps=%d no_answer_wrong=%d" % (
            method, s["full_display"], s["answerable_n"], s["full_id"], s["answerable_n"],
            s["missed_requirements"], s["answerable_refused"], s["id_display_gap"],
            s["no_answer_wrong_evidence"]))
    print("supplement", {k: summary["hybrid_top5_supplement"][k] for k in (
        "supplement_units", "wrong_supplement_units", "supplement_gain_vs_top5",
        "supplement_loss_vs_top5", "supplement_gain_vs_top7", "supplement_loss_vs_top7")})
    print("failures=%d" % len(failures))
    return 0


if __name__ == "__main__":
    sys.exit(main())
