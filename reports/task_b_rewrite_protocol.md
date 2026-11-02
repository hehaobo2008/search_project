# 任务B 同语料改写候选协议（非独立冻结测试）

本文件中的 20 道候选题来自同一 A/B 语料，且多题与开发集共享条款或问法家族。它们**不是独立冻结测试集**，不能用于宣称跨主题泛化。

## 当前状态

- 20 题全部 `status=unlabeled`、`split=same_corpus_rewrite_candidate`，未运行、未计分。
- 配置 `rewrite_candidates.is_independent_test=false`。
- 这些题只在开发集标准答案与配置固定后，作为同语料改写稳定性检查；若与开发题同条款，报告必须标注 `same_corpus_rewrite`。

## 标注与运行顺序

1. 标注者先打开锁定版本原文，独立确定每个信息需求的必需证据组与可接受替代；不看系统输出。
2. 两人独立标注，分歧由第三人复核；先定标准答案与分母。
3. 冻结配置、模型 revision、问题集与 gold 的 SHA-256；冻结后不再按结果调参。
4. 再运行 `python scripts/task_b_pipeline.py` 或评测脚本计分。
5. 报告实际 N、未运行数、失败数；不得用开发集 13 题结果替代改写测试成绩。

## 题型分层

| 题型 | 数量 | 说明 |
|---|---|---|
| retrieval | 13 | |
| no_answer | 3 | |
| version_conflict | 2 | |
| citation_ambiguity | 2 | |

## 题目家族重叠

| 候选 | 重叠开发题 | 重叠条款 | 处理 |
|---|---|---|---|
| F01 | - | rail_quality:art-20 | 标为同语料改写，不得当独立测试 |
| F02 | - | construction_quality:art-40 | 标为同语料改写，不得当独立测试 |
| F03 | - | rail_quality:art-75 | 标为同语料改写，不得当独立测试 |
| F04 | - | construction_quality:art-82 | 标为同语料改写，不得当独立测试 |
| F05 | D01, D02, D16 | rail_quality:art-30, construction_quality:art-29, construction_quality:art-31 | 标为同语料改写，不得当独立测试 |
| F06 | - | construction_quality:art-37 | 标为同语料改写，不得当独立测试 |
| F07 | D06 | rail_quality:art-16 | 标为同语料改写，不得当独立测试 |
| F08 | D17 | rail_quality:art-65, rail_quality:art-66 | 标为同语料改写，不得当独立测试 |
| F09 | - | construction_quality:art-7 | 标为同语料改写，不得当独立测试 |
| F10 | D09 | construction_quality:art-11 | 标为同语料改写，不得当独立测试 |
| F11 | F06, F12 | construction_quality:art-37 | 标为同语料改写，不得当独立测试 |
| F12 | F06, F11 | construction_quality:art-37 | 标为同语料改写，不得当独立测试 |
| F13 | - | rail_quality:art-14 | 标为同语料改写，不得当独立测试 |
| F17 | D13 | - | 标为同语料改写，不得当独立测试 |
| F18 | D13 | - | 标为同语料改写，不得当独立测试 |
| F19 | - | rail_quality:art-62, construction_quality:art-60 | 标为同语料改写，不得当独立测试 |
| F20 | D14 | rail_quality:art-30, construction_quality:art-29 | 标为同语料改写，不得当独立测试 |

F05、F07、F08、F10 与开发题主题及问法高度接近，必须在结果中单列为 `same_corpus_rewrite`。

