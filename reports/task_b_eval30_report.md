# Eval30 首轮四方法对照结果

> **同语料、非产品准确率、非独立跨主题测试。** 本轮为冻结后首轮运行，gold 只交给评分器，系统只接收问题和方法名。
> 证据覆盖同时报告“条款 ID 命中”和“展示文字实际覆盖”；展示文字未包含校验词时，即使 ID 命中也不算充分。

- run_id：`eval30-first-rerun-20261103`
- 冻结 questions_only：`fb2b04d71630fc9deffa3d8426053c076aaf6ff054e58f0e4a56be459bdebe60`
- 冻结 gold：`700d6c267ccacba9a582b4ca1beada7687b0ebcbe7245952e157caa77bec9db9`
- 运行时长（共享模型/索引加载，不作为算法速度）：2.28 s

## 汇总

| 方法 | 可回答N | 展示全证据 | ID全命中 | 漏项数 | 有答案被误拒 | ID命中但展示不足题数 | 无答案N | 无答案误出证据 |
|---|---|---|---|---|---|---|---|---|
| 纯BM25 Top7 | 20 | 19 | 19 | 2 | 1 | 0 | 10 | 4 |
| 纯语义 Top7 | 20 | 17 | 17 | 4 | 1 | 0 | 10 | 4 |
| 混合 Top7 | 20 | 19 | 19 | 2 | 1 | 0 | 10 | 4 |
| 混合 Top5+≤2补证 | 20 | 19 | 19 | 2 | 1 | 0 | 10 | 4 |
| 混合 Top5（补证基线） | 20 | 19 | 19 | 2 | 1 | 0 | 10 | 4 |

## 补证统计

- 触发补证的题数：1/20；补证单元总数：1；错误补证单元：1。
- 相对混合 Top5：补证组独有覆盖 0 题，丢失覆盖 0 题，新增覆盖需求 0 项。
- 相对混合 Top7：补证组独有覆盖 0 题，丢失覆盖 0 题。

## 20 道可回答题逐题

| qid | 需求组 | BM25 展示全/漏项/误拒 | 语义 展示全/漏项/误拒 | 混合 展示全/漏项/误拒 | 补证 展示全/漏项/误拒 |
|---|---|---|---|---|---|
| N01 | 1 | True/0/False | True/0/False | True/0/False | True/0/False |
| N02 | 1 | True/0/False | True/0/False | True/0/False | True/0/False |
| N03 | 1 | True/0/False | True/0/False | True/0/False | True/0/False |
| N04 | 2 | True/0/False | True/0/False | True/0/False | True/0/False |
| N05 | 2 | True/0/False | True/0/False | True/0/False | True/0/False |
| N06 | 1 | True/0/False | True/0/False | True/0/False | True/0/False |
| N07 | 1 | True/0/False | True/0/False | True/0/False | True/0/False |
| N08 | 1 | True/0/False | True/0/False | True/0/False | True/0/False |
| N09 | 2 | True/0/False | True/0/False | True/0/False | True/0/False |
| N10 | 1 | True/0/False | True/0/False | True/0/False | True/0/False |
| N11 | 2 | False/2/True | False/2/True | False/2/True | False/2/True |
| N12 | 2 | True/0/False | True/0/False | True/0/False | True/0/False |
| N13 | 2 | True/0/False | True/0/False | True/0/False | True/0/False |
| N14 | 2 | True/0/False | False/1/False | True/0/False | True/0/False |
| N15 | 2 | True/0/False | True/0/False | True/0/False | True/0/False |
| N16 | 2 | True/0/False | False/1/False | True/0/False | True/0/False |
| N17 | 2 | True/0/False | True/0/False | True/0/False | True/0/False |
| N18 | 3 | True/0/False | True/0/False | True/0/False | True/0/False |
| N19 | 3 | True/0/False | True/0/False | True/0/False | True/0/False |
| N20 | 2 | True/0/False | True/0/False | True/0/False | True/0/False |

## 10 道无答案题

| qid | BM25 | 语义 | 混合 | 补证 |
|---|---|---|---|---|
| N21 | refuse | refuse | refuse | refuse |
| N22 | refuse | refuse | refuse | refuse |
| N23 | refuse | refuse | refuse | refuse |
| N24 | answer | answer | answer | answer |
| N25 | answer | answer | answer | answer |
| N26 | answer | answer | answer | answer |
| N27 | refuse | refuse | refuse | refuse |
| N28 | answer | answer | answer | answer |
| N29 | refuse | refuse | refuse | refuse |
| N30 | refuse | refuse | refuse | refuse |

## 失败明细

- `N11` / bm25_top7：answerable_refused 
- `N11` / dense_top7：answerable_refused 
- `N11` / hybrid_top7：answerable_refused 
- `N11` / hybrid_top5_supplement：answerable_refused 
- `N11` / hybrid_top5：answerable_refused 
- `N14` / dense_top7：missing_requirements ['竣工验收备案时限与文件']
- `N14` / hybrid_top5_supplement：wrong_supplement ['construction_quality:art-56']
- `N16` / dense_top7：missing_requirements ['条例对勘察设计违法行为的罚则']
- `N24` / bm25_top7：no_answer_wrong_evidence ['construction_quality:art-8', 'rail_quality:art-25', 'construction_quality:art-24', 'construction_quality:art-15', 'rail_quality:art-23', 'construction_quality:art-19', 'rail_quality:art-20']
- `N24` / dense_top7：no_answer_wrong_evidence ['rail_quality:art-62', 'rail_quality:art-22', 'rail_quality:art-60', 'rail_quality:art-23', 'rail_quality:art-66', 'rail_quality:art-64', 'rail_quality:art-63']
- `N24` / hybrid_top7：no_answer_wrong_evidence ['rail_quality:art-23', 'rail_quality:art-25', 'rail_quality:art-62', 'rail_quality:art-64', 'rail_quality:art-63', 'rail_quality:art-22', 'rail_quality:art-56']
- `N24` / hybrid_top5_supplement：no_answer_wrong_evidence ['rail_quality:art-23', 'rail_quality:art-25', 'rail_quality:art-62', 'rail_quality:art-64', 'rail_quality:art-63']
- `N24` / hybrid_top5：no_answer_wrong_evidence ['rail_quality:art-23', 'rail_quality:art-25', 'rail_quality:art-62', 'rail_quality:art-64', 'rail_quality:art-63']
- `N25` / bm25_top7：no_answer_wrong_evidence ['rail_quality:art-17', 'construction_quality:art-1', 'rail_quality:art-1', 'rail_quality:art-44', 'construction_quality:art-58', 'rail_quality:art-16', 'construction_quality:art-49']
- `N25` / dense_top7：no_answer_wrong_evidence ['rail_quality:art-36', 'rail_quality:art-40', 'rail_quality:art-30', 'rail_quality:art-47', 'rail_quality:art-37', 'rail_quality:art-41', 'rail_quality:art-39']
- `N25` / hybrid_top7：no_answer_wrong_evidence ['rail_quality:art-40', 'rail_quality:art-15', 'rail_quality:art-44', 'rail_quality:art-39', 'rail_quality:art-52', 'rail_quality:art-16', 'rail_quality:art-17']
- `N25` / hybrid_top5_supplement：no_answer_wrong_evidence ['rail_quality:art-40', 'rail_quality:art-15', 'rail_quality:art-44', 'rail_quality:art-39', 'rail_quality:art-52']
- `N25` / hybrid_top5：no_answer_wrong_evidence ['rail_quality:art-40', 'rail_quality:art-15', 'rail_quality:art-44', 'rail_quality:art-39', 'rail_quality:art-52']
- `N26` / bm25_top7：no_answer_wrong_evidence ['rail_quality:art-23', 'construction_quality:art-11', 'construction_quality:art-23', 'rail_quality:art-10', 'construction_quality:art-56', 'rail_quality:art-29', 'rail_quality:art-58']
- `N26` / dense_top7：no_answer_wrong_evidence ['rail_quality:art-23', 'rail_quality:art-22', 'rail_quality:art-14', 'rail_quality:art-21', 'rail_quality:art-24', 'rail_quality:art-20', 'rail_quality:art-29']
- `N26` / hybrid_top7：no_answer_wrong_evidence ['rail_quality:art-23', 'rail_quality:art-22', 'rail_quality:art-10', 'rail_quality:art-29', 'rail_quality:art-14', 'construction_quality:art-23', 'rail_quality:art-31']
- `N26` / hybrid_top5_supplement：no_answer_wrong_evidence ['rail_quality:art-23', 'rail_quality:art-22', 'rail_quality:art-10', 'rail_quality:art-29', 'rail_quality:art-14']
- `N26` / hybrid_top5：no_answer_wrong_evidence ['rail_quality:art-23', 'rail_quality:art-22', 'rail_quality:art-10', 'rail_quality:art-29', 'rail_quality:art-14']
- `N28` / bm25_top7：no_answer_wrong_evidence ['construction_quality:art-74', 'rail_quality:art-42', 'rail_quality:art-9', 'construction_quality:art-63', 'construction_quality:art-70', 'rail_quality:art-60', 'construction_quality:art-31']
- `N28` / dense_top7：no_answer_wrong_evidence ['rail_quality:art-42', 'rail_quality:art-43', 'rail_quality:art-45', 'rail_quality:art-44', 'rail_quality:art-63', 'rail_quality:art-66', 'rail_quality:art-65']
- `N28` / hybrid_top7：no_answer_wrong_evidence ['rail_quality:art-42', 'rail_quality:art-60', 'rail_quality:art-43', 'rail_quality:art-44', 'rail_quality:art-66', 'rail_quality:art-9', 'rail_quality:art-45']
- `N28` / hybrid_top5_supplement：no_answer_wrong_evidence ['rail_quality:art-42', 'rail_quality:art-60', 'rail_quality:art-43', 'rail_quality:art-44', 'rail_quality:art-66']
- `N28` / hybrid_top5：no_answer_wrong_evidence ['rail_quality:art-42', 'rail_quality:art-60', 'rail_quality:art-43', 'rail_quality:art-44', 'rail_quality:art-66']
