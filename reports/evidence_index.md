# 任务A 证据索引（真实产物）

- run_id：pipeline-20261102T190529
- 生成时间：2026-11-02T19:05:32.214008+08:00

| 证据ID | 对应产物 | 证明什么 | 不能证明什么 / 待办 |
|---|---|---|---|
| E01 | 平台身份 | 本会话运行于 CodeArts Agent；项目路径与时间可复核 | 截图待采集；仅截图不能证明实验完成 |
| E02 | 首次任务与授权 | 会话内用户指令与交接包 FIRST_SESSION_PROMPT.txt | 未导出对话文件 |
| E03 | 实际改动 | scripts/ 11 个脚本、tests/ 7 个文件、corpus/locators/reports 产物 | 未初始化 Git，无 commit/diff hash |
| E04 | 运行证据 | logs/runs/<run_id>/ 每步独立日志；logs/run_manifest.json 九步退出码0 | 无 run_id 之外的外部流水号 |
| E05 | 条款回跳 | locators/index.json + verify_locators：158/158，A30/A66/B31 关键项通过 | 视觉确认待人工 |
| E06 | 版本反例 | version_counterexample_result.json：A2015 已被修订、B2017 首页仅载2017、条号位移、版本待核验 | B2017 仅作反例对照，不进入主索引 |
| E07 | 任务A人工复核 | human_review_checklist.md H01-H08 含 file:// 回跳链接 | 全部待人工填写，闸门未通过 |
| E08 | 任务B | 未执行 | 未获批，不准备虚假 E08 |
| E09 | 回归/失败 | tests 19/19；故意失败负控通过；O01-O03 已记录 | 未人为制造真实失败；合成故障单列 |
| E10 | 最终关联 | run_id、产物 hash、独立日志、测试输出可互相对照 | 无 commit 可关联 |
| E11 | 复验包 | dist/taskA_<run_id>.zip + SHA256SUMS | 包内含报告/日志/测试输出，不含法规全文 |

## 产物 hash

- `corpus/docs_manifest.json`：`9c6578527a447bf59412dbe6f5854c6c2aa9b8d9234bde1363e3b42e8137fed6`
- `corpus/articles.jsonl`：`55b600c53a33d2e7b4398d9094ebdc2f40bbc33c628921e6c102a57d55b04a3d`
- `corpus/relations.jsonl`：`3c66869a25e1217e1e426d55d2c9492ee39fb16d4324a7d36dca5d52f15b6619`
- `corpus/relation_diagnostics.json`：`a5f4ec97f577fed3ff9527271b889e5af0e7d292954f7b81cbe9c97c8d2b069b`
- `locators/index.json`：`82908369b5ed8d1e8c284620c140e5c3d0792102700f64fc80e3914b770d69f6`
- `reports/task_a_result.json`：`4888db0ce70389e1b358e9bc6329ef2a4400fa22ad8c47c82d15e12305cadcfd`
- `reports/locator_result.json`：`18239e5331d03c518904f67b0d1c8b191cef1e46253be80520662c768b1695bd`
- `reports/version_counterexample_result.json`：`42c6209a9feafe3494ccb2bb584e4d0ae9cc66aeccd6d98ede769f6da8adb9ea`
- `reports/test_result.json`：`2da69ac237acee06e4b841b1bb6504c7a690c71f6959b17544a6f83d7f094b5b`
- `logs/run_manifest.json`：`efb323511ebf868bb9d7d5a68883dbb360f07804f43c13a605825d71b7a24412`

> 未采集的截图、未提交的 commit 均未列入已完成证据；不得用本文件替代主办方要求的平台记录。
