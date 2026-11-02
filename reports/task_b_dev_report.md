# 任务B 开发集端到端评测（dev_gold_v2）

> **不是产品准确率，也不是独立冻结测试。** 开发集 13 道检索题、2 道无答案题；gold 为 `dev_gold_v2`，由本次会话按信息需求重标，仍待人工复核。
> 冻结测试尚未建立；同语料改写候选 20 题未标注、未运行，不能宣称跨主题泛化。

## 统一入口与隔离

- 被测系统入口：`TaskBSystem.answer(question, method)`，只接收自然语言问题与方法名。
- 题型、标准答案、预标条款对只在评分器 `task_b_eval.py` 中读取，不传给被测系统。
- 版本/引用歧义检查保留为模块测试，单独统计，不进入端到端成绩。

## 证据标注 v2

按每个问题的信息需求标注，每个需求允许多个可接受证据；多需求题按需求逐项覆盖，不再把能独立覆盖问题的单条与其它条款强行设为同时必需。

## 同预算对照（N=13）

| 方法 | Hit | 全证据 | 需求命中/总需求 | 宏Recall | 微Recall | 单元均值 | 字符均值 | 查询p50/p95 ms |
|---|---|---|---|---|---|---|---|---|
| 纯BM25 Top7 | 13/13 | 12/13 | 15/16 | 0.9615 | 0.9375 | 7.00 | 969.54 | 9.72/12.14 |
| 纯语义 Top7 | 12/13 | 12/13 | 15/16 | 0.9231 | 0.9375 | 7.00 | 890.31 | 9.43/11.69 |
| 混合 Top7 | 13/13 | 13/13 | 16/16 | 1.0000 | 1.0000 | 7.00 | 961.38 | 9.51/12.15 |
| 混合 Top5+≤2补证 | 13/13 | 13/13 | 16/16 | 1.0000 | 1.0000 | 5.08 | 724.77 | 9.53/11.05 |
| 混合 Top5（辅助） | 12/13 | 12/13 | 15/16 | 0.9231 | 0.9375 | 5.00 | 714.23 | 9.79/10.68 |

> 耗时说明：模型与文档向量只加载一次，各方法各自调用 `answer()` 独立查询；表中查询耗时是每方法独立查询的 p50/p95，不把同一轮共享检索耗时复制成多个方法的“独立速度成绩”。

## 配对变化

| 比较 | A独有成功 | B独有成功 | 均成功 | 均失败 |
|---|---|---|---|---|
| 混合Top7 vs 补证 | 0 | 0 | 13 | 0 |
| 纯BM25 vs 混合Top7 | 0 | 0 | 13 | 0 |
| 纯语义 vs 混合Top7 | 0 | 1 | 12 | 0 |

## 失败统计（保留全部）

| 方法 | Hit失败 | 全证据失败 | 有答案却被拒绝 | 无答案却出结果 | 错误补证单元 | 补证单元总数 |
|---|---|---|---|---|---|---|
| 纯BM25 Top7 | 0 | 1 | 0/13 | 0/2 | 0 | 0 |
| 纯语义 Top7 | 1 | 1 | 0/13 | 0/2 | 0 | 0 |
| 混合 Top7 | 0 | 0 | 0/13 | 0/2 | 0 | 0 |
| 混合 Top5+≤2补证 | 0 | 0 | 0/13 | 0/2 | 0 | 1 |
| 混合 Top5（辅助） | 1 | 1 | 0/13 | 0/2 | 0 | 0 |

## 模块测试（不计端到端）

| 用例 | 类型 | 期望 | 实际 | 结论 |
|---|---|---|---|---|
| D13 | version_conflict | version_pending | version_pending | 通过 |
| D14 | citation_ambiguity | topic_related | topic_related | 通过 |
| D15 | citation_ambiguity | explicit_document | explicit_document | 通过 |

## 逐题逐方法

| qid | 需求组 | 方法 | 决策 | Hit | 全证据 | 单元/字符 | 补证 | 错误补证 |
|---|---|---|---|---|---|---|---|---|
| D01 | 2 | 纯BM25 Top7 | answer | True | True | 7/900 | 0 | - |
| D01 | 2 | 纯语义 Top7 | answer | True | True | 7/785 | 0 | - |
| D01 | 2 | 混合 Top7 | answer | True | True | 7/918 | 0 | - |
| D01 | 2 | 混合 Top5+≤2补证 | answer | True | True | 5/721 | 0 | - |
| D01 | 2 | 混合 Top5（辅助） | answer | True | True | 5/721 | 0 | - |
| D02 | 1 | 纯BM25 Top7 | answer | True | True | 7/1025 | 0 | - |
| D02 | 1 | 纯语义 Top7 | answer | True | True | 7/1056 | 0 | - |
| D02 | 1 | 混合 Top7 | answer | True | True | 7/995 | 0 | - |
| D02 | 1 | 混合 Top5+≤2补证 | answer | True | True | 5/784 | 0 | - |
| D02 | 1 | 混合 Top5（辅助） | answer | True | True | 5/784 | 0 | - |
| D03 | 1 | 纯BM25 Top7 | answer | True | True | 7/780 | 0 | - |
| D03 | 1 | 纯语义 Top7 | answer | False | False | 7/416 | 0 | - |
| D03 | 1 | 混合 Top7 | answer | True | True | 7/837 | 0 | - |
| D03 | 1 | 混合 Top5+≤2补证 | answer | True | True | 6/788 | 1 | - |
| D03 | 1 | 混合 Top5（辅助） | answer | False | False | 5/651 | 0 | - |
| D04 | 1 | 纯BM25 Top7 | answer | True | True | 7/821 | 0 | - |
| D04 | 1 | 纯语义 Top7 | answer | True | True | 7/1314 | 0 | - |
| D04 | 1 | 混合 Top7 | answer | True | True | 7/1349 | 0 | - |
| D04 | 1 | 混合 Top5+≤2补证 | answer | True | True | 5/1109 | 0 | - |
| D04 | 1 | 混合 Top5（辅助） | answer | True | True | 5/1109 | 0 | - |
| D05 | 1 | 纯BM25 Top7 | answer | True | True | 7/1062 | 0 | - |
| D05 | 1 | 纯语义 Top7 | answer | True | True | 7/632 | 0 | - |
| D05 | 1 | 混合 Top7 | answer | True | True | 7/800 | 0 | - |
| D05 | 1 | 混合 Top5+≤2补证 | answer | True | True | 5/480 | 0 | - |
| D05 | 1 | 混合 Top5（辅助） | answer | True | True | 5/480 | 0 | - |
| D06 | 1 | 纯BM25 Top7 | answer | True | True | 7/879 | 0 | - |
| D06 | 1 | 纯语义 Top7 | answer | True | True | 7/1064 | 0 | - |
| D06 | 1 | 混合 Top7 | answer | True | True | 7/949 | 0 | - |
| D06 | 1 | 混合 Top5+≤2补证 | answer | True | True | 5/612 | 0 | - |
| D06 | 1 | 混合 Top5（辅助） | answer | True | True | 5/612 | 0 | - |
| D07 | 1 | 纯BM25 Top7 | answer | True | True | 7/801 | 0 | - |
| D07 | 1 | 纯语义 Top7 | answer | True | True | 7/685 | 0 | - |
| D07 | 1 | 混合 Top7 | answer | True | True | 7/728 | 0 | - |
| D07 | 1 | 混合 Top5+≤2补证 | answer | True | True | 5/482 | 0 | - |
| D07 | 1 | 混合 Top5（辅助） | answer | True | True | 5/482 | 0 | - |
| D08 | 1 | 纯BM25 Top7 | answer | True | True | 7/1090 | 0 | - |
| D08 | 1 | 纯语义 Top7 | answer | True | True | 7/713 | 0 | - |
| D08 | 1 | 混合 Top7 | answer | True | True | 7/769 | 0 | - |
| D08 | 1 | 混合 Top5+≤2补证 | answer | True | True | 5/552 | 0 | - |
| D08 | 1 | 混合 Top5（辅助） | answer | True | True | 5/552 | 0 | - |
| D09 | 1 | 纯BM25 Top7 | answer | True | True | 7/1096 | 0 | - |
| D09 | 1 | 纯语义 Top7 | answer | True | True | 7/639 | 0 | - |
| D09 | 1 | 混合 Top7 | answer | True | True | 7/773 | 0 | - |
| D09 | 1 | 混合 Top5+≤2补证 | answer | True | True | 5/660 | 0 | - |
| D09 | 1 | 混合 Top5（辅助） | answer | True | True | 5/660 | 0 | - |
| D10 | 1 | 纯BM25 Top7 | answer | True | True | 7/1253 | 0 | - |
| D10 | 1 | 纯语义 Top7 | answer | True | True | 7/857 | 0 | - |
| D10 | 1 | 混合 Top7 | answer | True | True | 7/1028 | 0 | - |
| D10 | 1 | 混合 Top5+≤2补证 | answer | True | True | 5/626 | 0 | - |
| D10 | 1 | 混合 Top5（辅助） | answer | True | True | 5/626 | 0 | - |
| D16 | 2 | 纯BM25 Top7 | answer | True | True | 7/855 | 0 | - |
| D16 | 2 | 纯语义 Top7 | answer | True | True | 7/744 | 0 | - |
| D16 | 2 | 混合 Top7 | answer | True | True | 7/808 | 0 | - |
| D16 | 2 | 混合 Top5+≤2补证 | answer | True | True | 5/634 | 0 | - |
| D16 | 2 | 混合 Top5（辅助） | answer | True | True | 5/634 | 0 | - |
| D17 | 2 | 纯BM25 Top7 | answer | True | False | 7/1012 | 0 | - |
| D17 | 2 | 纯语义 Top7 | answer | True | True | 7/1287 | 0 | - |
| D17 | 2 | 混合 Top7 | answer | True | True | 7/1162 | 0 | - |
| D17 | 2 | 混合 Top5+≤2补证 | answer | True | True | 5/850 | 0 | - |
| D17 | 2 | 混合 Top5（辅助） | answer | True | True | 5/850 | 0 | - |
| D18 | 1 | 纯BM25 Top7 | answer | True | True | 7/1030 | 0 | - |
| D18 | 1 | 纯语义 Top7 | answer | True | True | 7/1382 | 0 | - |
| D18 | 1 | 混合 Top7 | answer | True | True | 7/1382 | 0 | - |
| D18 | 1 | 混合 Top5+≤2补证 | answer | True | True | 5/1124 | 0 | - |
| D18 | 1 | 混合 Top5（辅助） | answer | True | True | 5/1124 | 0 | - |
| D11 | no_answer | 纯BM25 Top7 | refuse | - | - | - | - | - |
| D11 | no_answer | 纯语义 Top7 | refuse | - | - | - | - | - |
| D11 | no_answer | 混合 Top7 | refuse | - | - | - | - | - |
| D11 | no_answer | 混合 Top5+≤2补证 | refuse | - | - | - | - | - |
| D11 | no_answer | 混合 Top5（辅助） | refuse | - | - | - | - | - |
| D12 | no_answer | 纯BM25 Top7 | refuse | - | - | - | - | - |
| D12 | no_answer | 纯语义 Top7 | refuse | - | - | - | - | - |
| D12 | no_answer | 混合 Top7 | refuse | - | - | - | - | - |
| D12 | no_answer | 混合 Top5+≤2补证 | refuse | - | - | - | - | - |
| D12 | no_answer | 混合 Top5（辅助） | refuse | - | - | - | - | - |

## 失败明细

- `D03` / dense_top7：all_aspects_missed ['条例第65条原文']
- `D03` / hybrid_top5：all_aspects_missed ['条例第65条原文']
- `D17` / bm25_top7：missing_required_aspect ['偷工减料/不合格材料处罚']

## 结论边界

- 纯BM25、纯语义、混合、混合+补证在同一输出预算下对照；补证没有收益就如实记录，不把它写成已证明有效。
- 开发集结果只能说明这 13 道题上的工程链路表现，不能写成产品准确率或跨主题泛化成绩。
- 同一轮共享模型/索引加载，查询按方法独立调用；不把共享成本包装成各方法独立速度。
