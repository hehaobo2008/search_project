# 任务B 实际运行记录（开发集端到端，dev_gold_v2）

> **边界：** 本记录是 13 道开发检索题的端到端工程评测，**不是产品准确率，也不是独立冻结测试**。gold 为 `dev_gold_v2`，由本次会话按信息需求重标，仍待人工复核。20 道同语料改写候选未标注、未运行，不能宣称跨主题泛化。

## 一次运行身份

- 流水线 run_id：taskB-20261102T222859
- 任务与状态：B / 开发集端到端评测；模块测试单列；改写测试未运行
- 平台：当前 CodeArts Agent 会话，项目 `search_project`（截图待采集）
- 实际开始/结束及UTC偏移：2026-11-02T22:28:59.559534+08:00 至 2026-11-02T22:29:04.693002+08:00（UTC+08:00）
- 运行时：Python 3.13.2；onnxruntime 1.31.0 CPUExecutionProvider；tokenizers 0.23.3；jieba 0.42.1；rank_bm25 0.2.2；numpy 2.5.1
- 模型：BAAI/bge-small-zh-v1.5，ONNX 分发仓库 Xenova/bge-small-zh-v1.5（ModelScope）
- 模型 revision / hash：`onnx/model.onnx` SHA-256 `69a0b846f4f116b5e6aabf9546ea6754d02264f3211a13a1bd69b31b8040749a`（94851877 bytes）
- 模型许可：MIT（ModelScope 模型 API License=mit；BAAI 模型卡为 MIT；Xenova ONNX 转换仓库无独立 LICENSE 文件）
- 配置 hash：`0037f32996f81bb399f14404701d2eec597f7d384b56ca09ec9170352d3cf65b`（运行前冻结）
- 开发问题集 hash：`947fc398fb756333a8fdb562bb99a639445f0d74b1279848a42a25d12fb52fe8`；模块题 hash：`cadfa1d32465662b72ead28c69b7c68ade88c2d1fccfaad245322407df9bb59e`；改写候选 hash：`704f7b633d63de4aaa853f11918180805c01069193574724ac02d7ace85d3c82`
- commit：项目未初始化 Git，无 commit

## 实际命令与退出码

1. `<LOCAL_PATH> scripts/check_model.py` → exit=0，0.178s，日志 `logs/task_b/runs/taskB-20261102T222859/check_model.log`（373 bytes）
2. `<LOCAL_PATH> scripts/task_b_eval.py` → exit=0，2.665s，日志 `logs/task_b/runs/taskB-20261102T222859/eval_dev.log`（1137 bytes）
3. `<LOCAL_PATH> scripts/run_task_b_tests.py` → exit=0，2.215s，日志 `logs/task_b/runs/taskB-20261102T222859/run_tests.log`（1517 bytes）
4. `<LOCAL_PATH> scripts/check_rewrite.py` → exit=0，0.073s，日志 `logs/task_b/runs/taskB-20261102T222859/check_rewrite.log`（277 bytes）

## 统一入口与数据隔离

- 被测系统：`TaskBSystem.answer(question, method)`，只接收自然语言问题与方法名，不读取 qid、题型、standard answer 或预标条款对。
- 评分器：`task_b_eval.py` 读取问题集与 gold，调用 `answer(question, method)`，再按信息需求评分。
- 版本/引用歧义：`module_version_check`、`module_relation_check` 只做模块测试，不进入端到端成绩。

## 证据标注 v2

每题按信息需求拆分 requirement；每个 requirement 允许多个可接受证据。
- D01/D16：监督取样主体（A30 或 B31）+ 记录签字依据（A30 或 B29）。A30 单条可同时覆盖两项；B31+B29 也构成一套充分组合。
- D17：A65 与 A66 两个独立需求。
- D03/D04/D18：A66/A67 只是入口，不替代被引条例原文。

## 同预算对照（开发集 N=13）

| 方法 | Hit | 全证据 | 需求命中/总需求 | 宏Recall | 微Recall | 单元均值 | 字符均值 | 查询p50/p95 ms |
|---|---|---|---|---|---|---|---|---|
| 纯BM25 Top7 | 13/13 | 12/13 | 15/16 | 0.9615 | 0.9375 | 7.00 | 969.54 | 9.72/12.14 |
| 纯语义 Top7 | 12/13 | 12/13 | 15/16 | 0.9231 | 0.9375 | 7.00 | 890.31 | 9.43/11.69 |
| 混合 Top7 | 13/13 | 13/13 | 16/16 | 1.0000 | 1.0000 | 7.00 | 961.38 | 9.51/12.15 |
| 混合 Top5+≤2补证 | 13/13 | 13/13 | 16/16 | 1.0000 | 1.0000 | 5.08 | 724.77 | 9.53/11.05 |
| 混合 Top5（辅助） | 12/13 | 12/13 | 15/16 | 0.9231 | 0.9375 | 5.00 | 714.23 | 9.79/10.68 |

> 耗时：模型/文档向量只加载一次；各方法各自调用 `answer()` 独立查询。表中为每方法独立查询 p50/p95，不把同一轮共享检索耗时复制成多个方法的独立速度成绩。

## 失败统计（保留全部失败题）

| 方法 | Hit失败 | 全证据失败 | 有答案却被拒绝 | 无答案却出结果 | 错误补证单元 | 补证单元总数 |
|---|---|---|---|---|---|---|
| 纯BM25 Top7 | 0 | 1 | 0/13 | 0/2 | 0 | 0 |
| 纯语义 Top7 | 1 | 1 | 0/13 | 0/2 | 0 | 0 |
| 混合 Top7 | 0 | 0 | 0/13 | 0/2 | 0 | 0 |
| 混合 Top5+≤2补证 | 0 | 0 | 0/13 | 0/2 | 0 | 1 |
| 混合 Top5（辅助） | 1 | 1 | 0/13 | 0/2 | 0 | 0 |

## 配对变化

| 比较 | A独有成功 | B独有成功 | 均成功 | 均失败 |
|---|---|---|---|---|
| 混合Top7 vs 补证 | 0 | 0 | 13 | 0 |
| 纯BM25 vs 混合Top7 | 0 | 0 | 13 | 0 |
| 纯语义 vs 混合Top7 | 0 | 1 | 12 | 0 |

## 模块测试（不计端到端）

| 用例 | 类型 | 期望 | 实际 | 结论 |
|---|---|---|---|---|
| D13 | version_conflict | version_pending | version_pending | 通过 |
| D14 | citation_ambiguity | topic_related | topic_related | 通过 |
| D15 | citation_ambiguity | explicit_document | explicit_document | 通过 |

## 逐题结果（方法 Hit / 全证据）

| qid | 需求组 | 纯BM25 | 纯语义 | 混合 | 补证 |
|---|---|---|---|---|---|
| D01 | 2 | True/True | True/True | True/True | True/True |
| D02 | 1 | True/True | True/True | True/True | True/True |
| D03 | 1 | True/True | False/False | True/True | True/True |
| D04 | 1 | True/True | True/True | True/True | True/True |
| D05 | 1 | True/True | True/True | True/True | True/True |
| D06 | 1 | True/True | True/True | True/True | True/True |
| D07 | 1 | True/True | True/True | True/True | True/True |
| D08 | 1 | True/True | True/True | True/True | True/True |
| D09 | 1 | True/True | True/True | True/True | True/True |
| D10 | 1 | True/True | True/True | True/True | True/True |
| D16 | 2 | True/True | True/True | True/True | True/True |
| D17 | 2 | True/False | True/True | True/True | True/True |
| D18 | 1 | True/True | True/True | True/True | True/True |
| D11 | no_answer | refuse | refuse | refuse | refuse |
| D12 | no_answer | refuse | refuse | refuse | refuse |

## 失败明细

- `D03` / dense_top7：all_aspects_missed ['条例第65条原文']
- `D03` / hybrid_top5：all_aspects_missed ['条例第65条原文']
- `D17` / bm25_top7：missing_required_aspect ['偷工减料/不合格材料处罚']

## 回归测试

- 任务B测试：9 项，通过 9，失败 0，错误 0（`logs/task_b/runs/taskB-20261102T222859/run_tests.log`）。

## 失败与限制

- 开发集仅 13 道检索题；BM25/语义/混合/补证结果只能说明该开发集上的工程表现。
- 补证组与混合 Top7 的 Hit 相同，没有展示出额外收益；D03 在补证组成功、在纯语义与混合 Top5 失败。
- 有答案却被拒绝 0、无答案却出结果 0、错误补证 0（按本开发集与被测规则）。这不代表在其他问题上不会发生。
- 同语料改写候选 20 题未标注、未运行；F05/F07/F08/F10 与开发题高度接近，只能作为同语料改写测试。
- 未做端侧转换、手机性能、真实用户试用、显著性检验。

## 可主张范围

本轮可主张：统一入口在 13 道开发检索题上可运行；纯BM25、纯语义、混合、混合+补证在同一输出预算下完成了对照；失败题、拒绝/误出证据、错误补证均有逐题记录。不可主张：产品准确率、跨主题泛化、独立冻结测试成绩、补证已被证明有效、端侧性能或真实业务提效。