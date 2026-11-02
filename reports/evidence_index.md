# 任务A 证据索引（真实产物）

- run_id：pipeline-20261102T222829
- 生成时间：2026-11-02T22:28:31.809857+08:00

| 证据ID | 对应产物 | 证明什么 | 不能证明什么 / 待办 |
|---|---|---|---|
| E01 | 平台身份 | 本会话运行于 CodeArts Agent；项目路径与时间可复核 | 截图待采集；仅截图不能证明实验完成 |
| E02 | 首次任务与授权 | 会话内用户指令与交接包 FIRST_SESSION_PROMPT.txt | 未导出对话文件 |
| E03 | 实际改动 | scripts/ 11 个脚本、tests/ 7 个文件、corpus/locators/reports 产物 | 未初始化 Git，无 commit/diff hash |
| E04 | 运行证据 | logs/runs/<run_id>/ 每步独立日志；logs/run_manifest.json 九步退出码0 | 无 run_id 之外的外部流水号 |
| E05 | 条款回跳 | locators/index.json + verify_locators：158/158，A30/A66/B31 关键项通过 | 视觉确认待人工 |
| E06 | 版本反例 | version_counterexample_result.json：A2015 已被修订、B2017 首页仅载2017、条号位移、版本待核验 | B2017 仅作反例对照，不进入主索引 |
| E07 | 任务A人工复核 | human_review_checklist.md H01-H08 含 file:// 回跳链接 | 全部待人工填写，闸门未通过 |
| E08 | 任务B | 开发集端到端已运行；同语料改写未标注未运行 | 不把开发集写成产品准确率或独立测试 |
| E09 | 回归/失败 | tests 19/19；故意失败负控通过；O01-O03 已记录 | 未人为制造真实失败；合成故障单列 |
| E10 | 最终关联 | run_id、产物 hash、独立日志、测试输出可互相对照 | 无 commit 可关联 |
| E11 | 复验包 | dist/taskA_<run_id>.zip + SHA256SUMS | 包内含报告/日志/测试输出，不含法规全文 |

## 产物 hash

- `corpus/docs_manifest.json`：`28d704ebef95fede1feb0f57a35dc4033cc43d280f79b8383494c56ef9c30a04`
- `corpus/articles.jsonl`：`55b600c53a33d2e7b4398d9094ebdc2f40bbc33c628921e6c102a57d55b04a3d`
- `corpus/relations.jsonl`：`3c66869a25e1217e1e426d55d2c9492ee39fb16d4324a7d36dca5d52f15b6619`
- `corpus/relation_diagnostics.json`：`a5f4ec97f577fed3ff9527271b889e5af0e7d292954f7b81cbe9c97c8d2b069b`
- `locators/index.json`：`463a315c160accd12d67368a5bf023217f947cba6112b272325cdeee911fa04d`
- `reports/task_a_result.json`：`87cd3f25139fca714d2dfb32af6f962a2133d41890043352300de6c0f604ce0d`
- `reports/locator_result.json`：`a12215229b8582b4b8189a8faccff8bdd2e0615ee7b3491c46a21a759190c2ab`
- `reports/version_counterexample_result.json`：`983dfded766d903363e4cdb24d702328c93bf436e4e4f046ca70ed1c1a8586bc`
- `reports/test_result.json`：`8af9b4aeaac2ce78d64004d71bfb36eb4d2e351a3d3d0065332b2c376ec62824`
- `logs/run_manifest.json`：`33716ccda781feea93281b7af86d1014d40d338390d5a3aba3373d425bef0b84`

> 未采集的截图、未提交的 commit 均未列入已完成证据；不得用本文件替代主办方要求的平台记录。