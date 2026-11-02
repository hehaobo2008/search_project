# Eval30 首轮运行与重跑说明

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
