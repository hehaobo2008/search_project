# 任务B 证据索引（开发集探索）

- run_id：taskB-20261102T193549
- 生成时间：2026-11-02T19:35:51.472656+08:00

| 证据ID | 对应产物 | 证明什么 | 不能证明什么 / 待办 |
|---|---|---|---|
| B01 | 平台与会话 | 本次运行发生在 CodeArts Agent 会话 | 截图待采集；不能单独证明实验完成 |
| B02 | 模型 manifest | 来源、许可、revision 与文件 hash | 非 BAAI 原始权重逐字节一致；许可需人工复核 |
| B03 | 配置 hash | 融合、候选、预算、补证、答案判定配置 | 开发集调试配置，未冻结 |
| B04 | 独立运行日志 | logs/task_b/runs/taskB-20261102T193549 四步日志与退出码0 | 不代表任务A闸门通过 |
| B05 | 开发集结果 | 18 题逐题结果、整数计数、失败与限制 | 非独立测试；样本小 |
| B06 | 冻结候选 | 20 题 unlabeled，未运行 | 尚未标注，不产生成绩 |
| B07 | 任务B测试 | 8/8 通过 | 只验证工程规则，不验证检索泛化 |
| B08 | 边界声明 | 明确未做端侧、用户试用、显著性 | 不能外推 |

## 产物 hash

- `config/task_b_config.json`：`baa60e60e303ddaf39647f6146dcccafb0716df049256d8c4dcf049e700db39e`
- `data/task_b_dev_questions.jsonl`：`b54e1230146af1bf61fc4966a4e18ee16d81b72f435f06af716d1d71e85f5fbd`
- `data/task_b_freeze_candidates.jsonl`：`a18b7891e4cbb653d4e0981c514857e9f3d2faaae0ddcbe4568487003718d6cf`
- `corpus/docs_manifest.json`：`9c6578527a447bf59412dbe6f5854c6c2aa9b8d9234bde1363e3b42e8137fed6`
- `reports/task_b_dev_results.json`：`3900ce31b47074aa86e0ab6c2107071204138313593a05400687845cc32a9bd6`
- `logs/task_b/run_manifest.json`：`6747bf9a21882b4dd55090e12281f5de4239df6d999e605b06d52e08e68e74d0`

> 模型权重约 95MB，未纳入本记录；hash 见 MODEL_MANIFEST.json。
