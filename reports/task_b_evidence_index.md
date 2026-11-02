# 任务B 证据索引（开发集端到端）

- run_id：taskB-20261102T222859
- 生成时间：2026-11-02T22:29:02.311446+08:00

| 证据ID | 对应产物 | 证明什么 | 不能证明什么 / 待办 |
|---|---|---|---|
| B01 | 平台与会话 | 本次运行发生在 CodeArts Agent 会话 | 截图待采集 |
| B02 | 模型 manifest | 来源、许可、revision、文件 hash | 非 BAAI 原始权重逐字节一致；许可需人工复核 |
| B03 | 配置 hash | 运行前冻结的方法、预算、补证与答案判定 | 开发集配置，不是行业标准 |
| B04 | 独立日志 | logs/task_b/runs/taskB-20261102T222859 四步日志与退出码0 | 不代表任务A闸门通过 |
| B05 | 开发集结果 | 13 题逐题逐方法结果、失败题、拒绝/误出证据/错误补证 | 非产品准确率；非独立测试 |
| B06 | 同语料改写候选 | 20 题 unlabeled，未运行；含重叠家族 | 不是独立冻结测试；不宣称跨主题泛化 |
| B07 | 模块测试 | 版本/引用歧义 3/3 通过 | 不计入端到端成绩 |
| B08 | 回归测试 | 任务B 9/9 通过 | 只验证工程规则 |

## 产物 hash

- `config/task_b_config.json`：`0037f32996f81bb399f14404701d2eec597f7d384b56ca09ec9170352d3cf65b`
- `data/task_b_dev_questions.jsonl`：`947fc398fb756333a8fdb562bb99a639445f0d74b1279848a42a25d12fb52fe8`
- `data/task_b_module_questions.jsonl`：`cadfa1d32465662b72ead28c69b7c68ade88c2d1fccfaad245322407df9bb59e`
- `data/task_b_rewrite_candidates.jsonl`：`704f7b633d63de4aaa853f11918180805c01069193574724ac02d7ace85d3c82`
- `reports/task_b_dev_results.json`：`524504a189cf7abf0ea805214f002545a2828f9ebf40b88178c88fdc5db0d47b`
- `logs/task_b/run_manifest.json`：`fe36c553ca10e8a0e2a11b1bcfed4d548e3f4305cdc3219e117e065e0f732083`

> 模型权重约 95MB，未纳入本记录；hash 见 docs/bge-small-zh-v1.5-MODEL_MANIFEST.json。
