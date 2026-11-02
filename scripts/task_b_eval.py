import json
import os
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from task_b_system import TaskBSystem  # noqa: E402

REPORTS = os.path.join(ROOT, "reports")
os.makedirs(REPORTS, exist_ok=True)

METHODS = ["bm25_top7", "dense_top7", "hybrid_top7", "hybrid_top5_supplement"]
AUX = ["hybrid_top5"]
LABELS = {
    "bm25_top7": "纯BM25 Top7",
    "dense_top7": "纯语义 Top7",
    "hybrid_top7": "混合 Top7",
    "hybrid_top5_supplement": "混合 Top5+≤2补证",
    "hybrid_top5": "混合 Top5（辅助）",
}


def percentile(values, p):
    if not values:
        return 0.0
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(round((len(ordered) - 1) * p)))]


def score_units(units, requirements):
    ids = {u["article_id"] for u in units}
    aspects = [any(candidate in ids for candidate in req["acceptable"]) for req in requirements]
    return {
        "hit": any(aspects),
        "full": all(aspects),
        "aspects_hit": sum(aspects),
        "aspects_total": len(aspects),
        "recall": (sum(aspects) / len(aspects)) if aspects else 0.0,
        "aspect_detail": [{
            "aspect": req["aspect"],
            "hit": hit,
            "acceptable": req["acceptable"],
        } for req, hit in zip(requirements, aspects)],
    }


def allowed_ids(requirements):
    allowed = set()
    for req in requirements:
        allowed.update(req["acceptable"])
    return allowed


def main():
    config = json.load(open(os.path.join(ROOT, "config", "task_b_config.json"), encoding="utf-8"))
    dev = [json.loads(line) for line in open(
        os.path.join(ROOT, "data", "task_b_dev_questions.jsonl"), encoding="utf-8")]
    module = [json.loads(line) for line in open(
        os.path.join(ROOT, "data", "task_b_module_questions.jsonl"), encoding="utf-8")]

    system = TaskBSystem()
    retrieval_rows = []
    no_answer_rows = []
    module_rows = []
    failure_rows = []

    for q in dev:
        if q["group"] == "retrieval":
            row = {"qid": q["qid"], "question": q["question"],
                   "requirements": q["requirements"], "methods": {}}
            for method in METHODS + AUX:
                started = time.perf_counter()
                result = system.answer(q["question"], method)
                elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
                units = result["evidence"]
                metric = score_units(units, q["requirements"])
                supplements = units[5:] if method == "hybrid_top5_supplement" else []
                wrong_supp = []
                if method == "hybrid_top5_supplement":
                    allowed = allowed_ids(q["requirements"])
                    wrong_supp = [u["article_id"] for u in supplements
                                  if u["article_id"] not in allowed]
                row["methods"][method] = {
                    "decision": result["decision"],
                    "hit": metric["hit"],
                    "full": metric["full"],
                    "aspects_hit": metric["aspects_hit"],
                    "aspects_total": metric["aspects_total"],
                    "recall": metric["recall"],
                    "aspect_detail": metric["aspect_detail"],
                    "ids": [u["article_id"] for u in units],
                    "units": len(units),
                    "chars": sum(u["chars"] for u in units),
                    "supplements": len(supplements),
                    "supplement_ids": [u["article_id"] for u in supplements],
                    "wrong_supplement_ids": wrong_supp,
                    "answer_ms": elapsed_ms,
                    "timings": result["timings"],
                }
                if result["decision"] == "refuse":
                    failure_rows.append({"qid": q["qid"], "method": method,
                                         "failure": "answerable_refused"})
                elif not metric["hit"]:
                    failure_rows.append({"qid": q["qid"], "method": method,
                                         "failure": "all_aspects_missed",
                                         "detail": [d["aspect"] for d in metric["aspect_detail"]]})
                elif not metric["full"]:
                    failure_rows.append({"qid": q["qid"], "method": method,
                                         "failure": "missing_required_aspect",
                                         "detail": [d["aspect"] for d in metric["aspect_detail"]
                                                    if not d["hit"]]})
                if wrong_supp:
                    failure_rows.append({"qid": q["qid"], "method": method,
                                         "failure": "wrong_supplement",
                                         "detail": wrong_supp})
            retrieval_rows.append(row)
        elif q["group"] == "no_answer":
            row = {"qid": q["qid"], "question": q["question"],
                   "expected": "refuse", "methods": {}}
            for method in METHODS + AUX:
                started = time.perf_counter()
                result = system.answer(q["question"], method)
                elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
                row["methods"][method] = {
                    "decision": result["decision"],
                    "evidence_ids": [u["article_id"] for u in result["evidence"]],
                    "answer_ms": elapsed_ms,
                    "diagnostics": result["diagnostics"],
                }
                if result["decision"] != "refuse":
                    failure_rows.append({"qid": q["qid"], "method": method,
                                         "failure": "no_answer_answered",
                                         "detail": [u["article_id"] for u in result["evidence"]]})
            no_answer_rows.append(row)

    for q in module:
        if q["group"] == "version_conflict":
            check = system.module_version_check(q["question"])
            module_rows.append({"qid": q["qid"], "group": "version_conflict",
                                "question": q["question"], "state": check.get("state"),
                                "expected": q["expected_version_state"],
                                "correct": check.get("state") == q["expected_version_state"]})
        elif q["group"] == "citation_ambiguity":
            check = system.module_relation_check(q["pair"])
            module_rows.append({"qid": q["qid"], "group": "citation_ambiguity",
                                "question": q["question"], "pair": q["pair"],
                                "state": check["state"], "expected": q["expected_relation"],
                                "correct": check["state"] == q["expected_relation"]})

    N = len(retrieval_rows)
    summary = {}
    for method in METHODS + AUX:
        hit = sum(1 for r in retrieval_rows if r["methods"][method]["hit"])
        full = sum(1 for r in retrieval_rows if r["methods"][method]["full"])
        aspects_hit = sum(r["methods"][method]["aspects_hit"] for r in retrieval_rows)
        aspects_total = sum(r["methods"][method]["aspects_total"] for r in retrieval_rows)
        macro = sum(r["methods"][method]["recall"] for r in retrieval_rows) / N if N else 0.0
        units = [r["methods"][method]["units"] for r in retrieval_rows]
        chars = [r["methods"][method]["chars"] for r in retrieval_rows]
        times = [r["methods"][method]["answer_ms"] for r in retrieval_rows]
        refused = sum(1 for r in retrieval_rows if r["methods"][method]["decision"] == "refuse")
        supp_total = sum(r["methods"][method]["supplements"] for r in retrieval_rows)
        wrong_supp = sum(len(r["methods"][method]["wrong_supplement_ids"]) for r in retrieval_rows)
        summary[method] = {
            "n": N,
            "hit": hit,
            "full": full,
            "aspects_hit": aspects_hit,
            "aspects_total": aspects_total,
            "macro_recall": round(macro, 4),
            "micro_recall": round(aspects_hit / aspects_total, 4) if aspects_total else None,
            "units_mean": round(sum(units) / N, 2) if N else 0,
            "chars_mean": round(sum(chars) / N, 2) if N else 0,
            "answer_ms_p50": round(percentile(times, 0.5), 2),
            "answer_ms_p95": round(percentile(times, 0.95), 2),
            "answerable_refused": refused,
            "hit_fail": N - hit,
            "full_fail": N - full,
            "supplements_total": supp_total,
            "wrong_supplements": wrong_supp,
        }

    def compare(a, b):
        sa = [r["methods"][a]["hit"] for r in retrieval_rows]
        sb = [r["methods"][b]["hit"] for r in retrieval_rows]
        return {
            "a_only": sum(1 for x, y in zip(sa, sb) if x and not y),
            "b_only": sum(1 for x, y in zip(sa, sb) if y and not x),
            "both": sum(1 for x, y in zip(sa, sb) if x and y),
            "neither": sum(1 for x, y in zip(sa, sb) if not x and not y),
        }

    no_answer_summary = {}
    for method in METHODS + AUX:
        correct = sum(1 for r in no_answer_rows if r["methods"][method]["decision"] == "refuse")
        no_answer_summary[method] = {
            "n": len(no_answer_rows),
            "correct_refuse": correct,
            "wrong_evidence": len(no_answer_rows) - correct,
        }

    module_summary = {
        "n": len(module_rows),
        "correct": sum(1 for r in module_rows if r["correct"]),
        "wrong": sum(1 for r in module_rows if not r["correct"]),
        "rows": module_rows,
    }

    result = {
        "generated_at": __import__("datetime").datetime.now().astimezone().isoformat(),
        "scope": "dev_end_to_end",
        "disclaimer": "开发集13道检索题不是产品准确率，也不是独立冻结测试；gold为dev_gold_v2，待人工复核。",
        "config": config,
        "N": N,
        "summary": summary,
        "comparisons": {
            "hybrid_top7_vs_supplement": compare("hybrid_top7", "hybrid_top5_supplement"),
            "bm25_vs_hybrid": compare("bm25_top7", "hybrid_top7"),
            "dense_vs_hybrid": compare("dense_top7", "hybrid_top7"),
        },
        "no_answer": no_answer_summary,
        "module_tests": module_summary,
        "failures": failure_rows,
        "retrieval_rows": retrieval_rows,
        "no_answer_rows": no_answer_rows,
    }
    with open(os.path.join(REPORTS, "task_b_dev_results.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    lines = [
        "# 任务B 开发集端到端评测（dev_gold_v2）",
        "",
        "> **不是产品准确率，也不是独立冻结测试。** 开发集 13 道检索题、2 道无答案题；gold 为 `dev_gold_v2`，由本次会话按信息需求重标，仍待人工复核。",
        "> 冻结测试尚未建立；同语料改写候选 20 题未标注、未运行，不能宣称跨主题泛化。",
        "",
        "## 统一入口与隔离",
        "",
        "- 被测系统入口：`TaskBSystem.answer(question, method)`，只接收自然语言问题与方法名。",
        "- 题型、标准答案、预标条款对只在评分器 `task_b_eval.py` 中读取，不传给被测系统。",
        "- 版本/引用歧义检查保留为模块测试，单独统计，不进入端到端成绩。",
        "",
        "## 证据标注 v2",
        "",
        "按每个问题的信息需求标注，每个需求允许多个可接受证据；多需求题按需求逐项覆盖，不再把能独立覆盖问题的单条与其它条款强行设为同时必需。",
        "",
        "## 同预算对照（N=%d）" % N,
        "",
        "| 方法 | Hit | 全证据 | 需求命中/总需求 | 宏Recall | 微Recall | 单元均值 | 字符均值 | 查询p50/p95 ms |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for method in METHODS + AUX:
        s = summary[method]
        lines.append("| %s | %d/%d | %d/%d | %d/%d | %.4f | %.4f | %.2f | %.2f | %.2f/%.2f |" % (
            LABELS[method], s["hit"], N, s["full"], N, s["aspects_hit"], s["aspects_total"],
            s["macro_recall"], s["micro_recall"], s["units_mean"], s["chars_mean"],
            s["answer_ms_p50"], s["answer_ms_p95"]))

    lines += [
        "",
        "> 耗时说明：模型与文档向量只加载一次，各方法各自调用 `answer()` 独立查询；表中查询耗时是每方法独立查询的 p50/p95，不把同一轮共享检索耗时复制成多个方法的“独立速度成绩”。",
        "",
        "## 配对变化",
        "",
        "| 比较 | A独有成功 | B独有成功 | 均成功 | 均失败 |",
        "|---|---|---|---|---|",
    ]
    for key, label in [("hybrid_top7_vs_supplement", "混合Top7 vs 补证"),
                       ("bm25_vs_hybrid", "纯BM25 vs 混合Top7"),
                       ("dense_vs_hybrid", "纯语义 vs 混合Top7")]:
        c = result["comparisons"][key]
        lines.append("| %s | %d | %d | %d | %d |" % (label, c["a_only"], c["b_only"],
                                                    c["both"], c["neither"]))

    lines += [
        "",
        "## 失败统计（保留全部）",
        "",
        "| 方法 | Hit失败 | 全证据失败 | 有答案却被拒绝 | 无答案却出结果 | 错误补证单元 | 补证单元总数 |",
        "|---|---|---|---|---|---|---|",
    ]
    for method in METHODS + AUX:
        s = summary[method]
        na = no_answer_summary[method]
        lines.append("| %s | %d | %d | %d/%d | %d/%d | %d | %d |" % (
            LABELS[method], s["hit_fail"], s["full_fail"],
            s["answerable_refused"], N, na["wrong_evidence"], na["n"],
            s["wrong_supplements"], s["supplements_total"]))

    lines += ["", "## 模块测试（不计端到端）", "",
              "| 用例 | 类型 | 期望 | 实际 | 结论 |", "|---|---|---|---|---|"]
    for r in module_rows:
        lines.append("| %s | %s | %s | %s | %s |" % (
            r["qid"], r["group"], r["expected"], r["state"],
            "通过" if r["correct"] else "失败"))

    lines += ["", "## 逐题逐方法", "",
              "| qid | 需求组 | 方法 | 决策 | Hit | 全证据 | 单元/字符 | 补证 | 错误补证 |",
              "|---|---|---|---|---|---|---|---|---|"]
    for r in retrieval_rows:
        for method in METHODS + AUX:
            m = r["methods"][method]
            lines.append("| %s | %d | %s | %s | %s | %s | %d/%d | %d | %s |" % (
                r["qid"], m["aspects_total"], LABELS[method], m["decision"], m["hit"], m["full"],
                m["units"], m["chars"], m["supplements"],
                ",".join(m["wrong_supplement_ids"]) or "-"))
    for r in no_answer_rows:
        for method in METHODS + AUX:
            m = r["methods"][method]
            lines.append("| %s | no_answer | %s | %s | - | - | - | - | - |" % (
                r["qid"], LABELS[method], m["decision"]))

    lines += [
        "",
        "## 失败明细",
        "",
    ]
    if failure_rows:
        for f in failure_rows:
            lines.append("- `%s` / %s：%s %s" % (
                f["qid"], f["method"], f["failure"], f.get("detail", "")))
    else:
        lines.append("- 本轮无失败项；不人为制造失败。")

    lines += [
        "",
        "## 结论边界",
        "",
        "- 纯BM25、纯语义、混合、混合+补证在同一输出预算下对照；补证没有收益就如实记录，不把它写成已证明有效。",
        "- 开发集结果只能说明这 13 道题上的工程链路表现，不能写成产品准确率或跨主题泛化成绩。",
        "- 同一轮共享模型/索引加载，查询按方法独立调用；不把共享成本包装成各方法独立速度。",
    ]
    with open(os.path.join(REPORTS, "task_b_dev_report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print("N=%d" % N)
    for method in METHODS + AUX:
        s = summary[method]
        print("%-24s hit=%d/%d full=%d/%d aspects=%d/%d macro=%.4f units=%.2f chars=%.2f refused=%d wrong_supp=%d" % (
            method, s["hit"], N, s["full"], N, s["aspects_hit"], s["aspects_total"],
            s["macro_recall"], s["units_mean"], s["chars_mean"], s["answerable_refused"],
            s["wrong_supplements"]))
    print("no_answer", {m: no_answer_summary[m] for m in METHODS})
    print("module", module_summary["correct"], "/", module_summary["n"])
    print("failures", len(failure_rows))
    sys.exit(0)


if __name__ == "__main__":
    main()