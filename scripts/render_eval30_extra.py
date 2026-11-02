import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
r = json.load(open(os.path.join(ROOT, "reports", "task_b_eval30_results.json"), encoding="utf-8"))
methods = ["bm25_top7", "dense_top7", "hybrid_top7", "hybrid_top5_supplement"]
lines = [
    "# Eval30 条款ID命中 vs 展示文字实际覆盖",
    "",
    "- run_id：`%s`" % r["run_id"],
    "- 判定：`full_id` 只看返回单元是否含可接受条款ID；`full_display` 还要求展示文字包含该需求的校验词。",
    "- 只有 `full_display` 算展示证据充分；截断导致校验词缺失时，即使 `full_id` 命中也不算。",
    "",
    "| qid | 方法 | ID全命中 | 展示全证据 | 缺展示需求 | ID命中但展示不足 | 补证单元/错误补证 |",
    "|---|---|---|---|---|---|---|",
]
for row in r["answerable_rows"]:
    for m in methods:
        x = row["methods"][m]
        gap = "是" if x["id_display_gap"] else "否"
        lines.append("| %s | %s | %s | %s | %s | %s | %s/%s |" % (
            row["qid"], m, "是" if x["full_id"] else "否", "是" if x["full_display"] else "否",
            "、".join(x["missing_display"]) or "-", gap,
            x["supplement_count"], len(x["wrong_supplement_ids"])))
lines += [
    "",
    "## 10 道无答案题：是否误出证据",
    "",
    "| qid | 方法 | 决策 | 错误证据ID |",
    "|---|---|---|---|",
]
for row in r["no_answer_rows"]:
    for m in methods:
        x = row["methods"][m]
        lines.append("| %s | %s | %s | %s |" % (
            row["qid"], m, x["decision"],
            ",".join(x["evidence_ids"]) if x["decision"] != "refuse" else "-"))
lines += ["", "## 汇总", ""]
for m in methods:
    s = r["summary"][m]
    lines.append("- %s：ID全命中 %d/20，展示全证据 %d/20，误拒 %d，无答案误出证据 %d/10。" % (
        m, s["full_id"], s["full_display"], s["answerable_refused"], s["no_answer_wrong_evidence"]))
open(os.path.join(ROOT, "reports", "task_b_eval30_id_vs_display.md"), "w",
     encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")

notes = """# Eval30 首轮运行与重跑说明

## 冻结

- 冻结 commit：`9070b73c1961dd306e484520d57a311f07a7f98d`
- 冻结清单：`reports/task_b_eval30_freeze_manifest.json`
- 冻结状态：`frozen_no_retrieval`，首次检索前创建。

## 首轮运行

- run_id：`eval30-first-20261103`
- 退出码：1
- 原因：结果、报告、raw 与 run_manifest 已写出后，控制台最后一行打印使用了循环残留变量 `s`，触发 `KeyError: 'hybrid_top5_supplement'`。
- 影响：仅控制台打印；评分结果已完整写出。首轮 raw 保留于 `logs/task_b_eval30/runs/eval30-first-20261103/raw.json`，首轮结果副本保留于 `reports/task_b_eval30_results_first.json`。

## 修复与重跑

- 代码变化：`scripts/task_b_eval30.py` 仅将打印行从 `s["hybrid_top5_supplement"]` 改为 `summary["hybrid_top5_supplement"]`；未改评分、gold、配置、模型或排序参数。
- 重跑 run_id：`eval30-first-rerun-20261103`
- 重跑命令：`python scripts/task_b_eval30.py --rerun --reason "print KeyError after first run wrote raw/results; scoring logic unchanged"`
- 首轮与重跑的 `summary`、`failures` 完全一致；逐题原始 JSON 的计时字段不同。
- 首轮 raw 与失败记录保留，不使用重跑覆盖首轮原始输出。
"""
open(os.path.join(ROOT, "reports", "task_b_eval30_run_notes.md"), "w",
     encoding="utf-8", newline="\n").write(notes)
print("written id_vs_display and run_notes")
