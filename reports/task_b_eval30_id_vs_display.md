# Eval30 条款ID命中 vs 展示文字实际覆盖

- run_id：`eval30-first-rerun-20261103`
- 判定：`full_id` 只看返回单元是否含可接受条款ID；`full_display` 还要求展示文字包含该需求的校验词。
- 只有 `full_display` 算展示证据充分；截断导致校验词缺失时，即使 `full_id` 命中也不算。

| qid | 方法 | ID全命中 | 展示全证据 | 缺展示需求 | ID命中但展示不足 | 补证单元/错误补证 |
|---|---|---|---|---|---|---|
| N01 | bm25_top7 | 是 | 是 | - | 否 | 0/0 |
| N01 | dense_top7 | 是 | 是 | - | 否 | 0/0 |
| N01 | hybrid_top7 | 是 | 是 | - | 否 | 0/0 |
| N01 | hybrid_top5_supplement | 是 | 是 | - | 否 | 0/0 |
| N02 | bm25_top7 | 是 | 是 | - | 否 | 0/0 |
| N02 | dense_top7 | 是 | 是 | - | 否 | 0/0 |
| N02 | hybrid_top7 | 是 | 是 | - | 否 | 0/0 |
| N02 | hybrid_top5_supplement | 是 | 是 | - | 否 | 0/0 |
| N03 | bm25_top7 | 是 | 是 | - | 否 | 0/0 |
| N03 | dense_top7 | 是 | 是 | - | 否 | 0/0 |
| N03 | hybrid_top7 | 是 | 是 | - | 否 | 0/0 |
| N03 | hybrid_top5_supplement | 是 | 是 | - | 否 | 0/0 |
| N04 | bm25_top7 | 是 | 是 | - | 否 | 0/0 |
| N04 | dense_top7 | 是 | 是 | - | 否 | 0/0 |
| N04 | hybrid_top7 | 是 | 是 | - | 否 | 0/0 |
| N04 | hybrid_top5_supplement | 是 | 是 | - | 否 | 0/0 |
| N05 | bm25_top7 | 是 | 是 | - | 否 | 0/0 |
| N05 | dense_top7 | 是 | 是 | - | 否 | 0/0 |
| N05 | hybrid_top7 | 是 | 是 | - | 否 | 0/0 |
| N05 | hybrid_top5_supplement | 是 | 是 | - | 否 | 0/0 |
| N06 | bm25_top7 | 是 | 是 | - | 否 | 0/0 |
| N06 | dense_top7 | 是 | 是 | - | 否 | 0/0 |
| N06 | hybrid_top7 | 是 | 是 | - | 否 | 0/0 |
| N06 | hybrid_top5_supplement | 是 | 是 | - | 否 | 0/0 |
| N07 | bm25_top7 | 是 | 是 | - | 否 | 0/0 |
| N07 | dense_top7 | 是 | 是 | - | 否 | 0/0 |
| N07 | hybrid_top7 | 是 | 是 | - | 否 | 0/0 |
| N07 | hybrid_top5_supplement | 是 | 是 | - | 否 | 0/0 |
| N08 | bm25_top7 | 是 | 是 | - | 否 | 0/0 |
| N08 | dense_top7 | 是 | 是 | - | 否 | 0/0 |
| N08 | hybrid_top7 | 是 | 是 | - | 否 | 0/0 |
| N08 | hybrid_top5_supplement | 是 | 是 | - | 否 | 0/0 |
| N09 | bm25_top7 | 是 | 是 | - | 否 | 0/0 |
| N09 | dense_top7 | 是 | 是 | - | 否 | 0/0 |
| N09 | hybrid_top7 | 是 | 是 | - | 否 | 0/0 |
| N09 | hybrid_top5_supplement | 是 | 是 | - | 否 | 0/0 |
| N10 | bm25_top7 | 是 | 是 | - | 否 | 0/0 |
| N10 | dense_top7 | 是 | 是 | - | 否 | 0/0 |
| N10 | hybrid_top7 | 是 | 是 | - | 否 | 0/0 |
| N10 | hybrid_top5_supplement | 是 | 是 | - | 否 | 0/0 |
| N11 | bm25_top7 | 否 | 否 | 勘察设计单位不得转包或违法分包、工程监理单位不得转让监理业务 | 否 | 0/0 |
| N11 | dense_top7 | 否 | 否 | 勘察设计单位不得转包或违法分包、工程监理单位不得转让监理业务 | 否 | 0/0 |
| N11 | hybrid_top7 | 否 | 否 | 勘察设计单位不得转包或违法分包、工程监理单位不得转让监理业务 | 否 | 0/0 |
| N11 | hybrid_top5_supplement | 否 | 否 | 勘察设计单位不得转包或违法分包、工程监理单位不得转让监理业务 | 否 | 0/0 |
| N12 | bm25_top7 | 是 | 是 | - | 否 | 0/0 |
| N12 | dense_top7 | 是 | 是 | - | 否 | 0/0 |
| N12 | hybrid_top7 | 是 | 是 | - | 否 | 0/0 |
| N12 | hybrid_top5_supplement | 是 | 是 | - | 否 | 0/0 |
| N13 | bm25_top7 | 是 | 是 | - | 否 | 0/0 |
| N13 | dense_top7 | 是 | 是 | - | 否 | 0/0 |
| N13 | hybrid_top7 | 是 | 是 | - | 否 | 0/0 |
| N13 | hybrid_top5_supplement | 是 | 是 | - | 否 | 0/0 |
| N14 | bm25_top7 | 是 | 是 | - | 否 | 0/0 |
| N14 | dense_top7 | 否 | 否 | 竣工验收备案时限与文件 | 否 | 0/0 |
| N14 | hybrid_top7 | 是 | 是 | - | 否 | 0/0 |
| N14 | hybrid_top5_supplement | 是 | 是 | - | 否 | 1/1 |
| N15 | bm25_top7 | 是 | 是 | - | 否 | 0/0 |
| N15 | dense_top7 | 是 | 是 | - | 否 | 0/0 |
| N15 | hybrid_top7 | 是 | 是 | - | 否 | 0/0 |
| N15 | hybrid_top5_supplement | 是 | 是 | - | 否 | 0/0 |
| N16 | bm25_top7 | 是 | 是 | - | 否 | 0/0 |
| N16 | dense_top7 | 否 | 否 | 条例对勘察设计违法行为的罚则 | 否 | 0/0 |
| N16 | hybrid_top7 | 是 | 是 | - | 否 | 0/0 |
| N16 | hybrid_top5_supplement | 是 | 是 | - | 否 | 0/0 |
| N17 | bm25_top7 | 是 | 是 | - | 否 | 0/0 |
| N17 | dense_top7 | 是 | 是 | - | 否 | 0/0 |
| N17 | hybrid_top7 | 是 | 是 | - | 否 | 0/0 |
| N17 | hybrid_top5_supplement | 是 | 是 | - | 否 | 0/0 |
| N18 | bm25_top7 | 是 | 是 | - | 否 | 0/0 |
| N18 | dense_top7 | 是 | 是 | - | 否 | 0/0 |
| N18 | hybrid_top7 | 是 | 是 | - | 否 | 0/0 |
| N18 | hybrid_top5_supplement | 是 | 是 | - | 否 | 0/0 |
| N19 | bm25_top7 | 是 | 是 | - | 否 | 0/0 |
| N19 | dense_top7 | 是 | 是 | - | 否 | 0/0 |
| N19 | hybrid_top7 | 是 | 是 | - | 否 | 0/0 |
| N19 | hybrid_top5_supplement | 是 | 是 | - | 否 | 0/0 |
| N20 | bm25_top7 | 是 | 是 | - | 否 | 0/0 |
| N20 | dense_top7 | 是 | 是 | - | 否 | 0/0 |
| N20 | hybrid_top7 | 是 | 是 | - | 否 | 0/0 |
| N20 | hybrid_top5_supplement | 是 | 是 | - | 否 | 0/0 |

## 10 道无答案题：是否误出证据

| qid | 方法 | 决策 | 错误证据ID |
|---|---|---|---|
| N21 | bm25_top7 | refuse | - |
| N21 | dense_top7 | refuse | - |
| N21 | hybrid_top7 | refuse | - |
| N21 | hybrid_top5_supplement | refuse | - |
| N22 | bm25_top7 | refuse | - |
| N22 | dense_top7 | refuse | - |
| N22 | hybrid_top7 | refuse | - |
| N22 | hybrid_top5_supplement | refuse | - |
| N23 | bm25_top7 | refuse | - |
| N23 | dense_top7 | refuse | - |
| N23 | hybrid_top7 | refuse | - |
| N23 | hybrid_top5_supplement | refuse | - |
| N24 | bm25_top7 | answer | construction_quality:art-8,rail_quality:art-25,construction_quality:art-24,construction_quality:art-15,rail_quality:art-23,construction_quality:art-19,rail_quality:art-20 |
| N24 | dense_top7 | answer | rail_quality:art-62,rail_quality:art-22,rail_quality:art-60,rail_quality:art-23,rail_quality:art-66,rail_quality:art-64,rail_quality:art-63 |
| N24 | hybrid_top7 | answer | rail_quality:art-23,rail_quality:art-25,rail_quality:art-62,rail_quality:art-64,rail_quality:art-63,rail_quality:art-22,rail_quality:art-56 |
| N24 | hybrid_top5_supplement | answer | rail_quality:art-23,rail_quality:art-25,rail_quality:art-62,rail_quality:art-64,rail_quality:art-63 |
| N25 | bm25_top7 | answer | rail_quality:art-17,construction_quality:art-1,rail_quality:art-1,rail_quality:art-44,construction_quality:art-58,rail_quality:art-16,construction_quality:art-49 |
| N25 | dense_top7 | answer | rail_quality:art-36,rail_quality:art-40,rail_quality:art-30,rail_quality:art-47,rail_quality:art-37,rail_quality:art-41,rail_quality:art-39 |
| N25 | hybrid_top7 | answer | rail_quality:art-40,rail_quality:art-15,rail_quality:art-44,rail_quality:art-39,rail_quality:art-52,rail_quality:art-16,rail_quality:art-17 |
| N25 | hybrid_top5_supplement | answer | rail_quality:art-40,rail_quality:art-15,rail_quality:art-44,rail_quality:art-39,rail_quality:art-52 |
| N26 | bm25_top7 | answer | rail_quality:art-23,construction_quality:art-11,construction_quality:art-23,rail_quality:art-10,construction_quality:art-56,rail_quality:art-29,rail_quality:art-58 |
| N26 | dense_top7 | answer | rail_quality:art-23,rail_quality:art-22,rail_quality:art-14,rail_quality:art-21,rail_quality:art-24,rail_quality:art-20,rail_quality:art-29 |
| N26 | hybrid_top7 | answer | rail_quality:art-23,rail_quality:art-22,rail_quality:art-10,rail_quality:art-29,rail_quality:art-14,construction_quality:art-23,rail_quality:art-31 |
| N26 | hybrid_top5_supplement | answer | rail_quality:art-23,rail_quality:art-22,rail_quality:art-10,rail_quality:art-29,rail_quality:art-14 |
| N27 | bm25_top7 | refuse | - |
| N27 | dense_top7 | refuse | - |
| N27 | hybrid_top7 | refuse | - |
| N27 | hybrid_top5_supplement | refuse | - |
| N28 | bm25_top7 | answer | construction_quality:art-74,rail_quality:art-42,rail_quality:art-9,construction_quality:art-63,construction_quality:art-70,rail_quality:art-60,construction_quality:art-31 |
| N28 | dense_top7 | answer | rail_quality:art-42,rail_quality:art-43,rail_quality:art-45,rail_quality:art-44,rail_quality:art-63,rail_quality:art-66,rail_quality:art-65 |
| N28 | hybrid_top7 | answer | rail_quality:art-42,rail_quality:art-60,rail_quality:art-43,rail_quality:art-44,rail_quality:art-66,rail_quality:art-9,rail_quality:art-45 |
| N28 | hybrid_top5_supplement | answer | rail_quality:art-42,rail_quality:art-60,rail_quality:art-43,rail_quality:art-44,rail_quality:art-66 |
| N29 | bm25_top7 | refuse | - |
| N29 | dense_top7 | refuse | - |
| N29 | hybrid_top7 | refuse | - |
| N29 | hybrid_top5_supplement | refuse | - |
| N30 | bm25_top7 | refuse | - |
| N30 | dense_top7 | refuse | - |
| N30 | hybrid_top7 | refuse | - |
| N30 | hybrid_top5_supplement | refuse | - |

## 汇总

- bm25_top7：ID全命中 19/20，展示全证据 19/20，误拒 1，无答案误出证据 4/10。
- dense_top7：ID全命中 17/20，展示全证据 17/20，误拒 1，无答案误出证据 4/10。
- hybrid_top7：ID全命中 19/20，展示全证据 19/20，误拒 1，无答案误出证据 4/10。
- hybrid_top5_supplement：ID全命中 19/20，展示全证据 19/20，误拒 1，无答案误出证据 4/10。
