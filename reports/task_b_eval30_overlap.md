# Eval30 题目家族重叠检查

本批 30 题与开发集 15 题、模块题 3 题、同语料改写候选 20 题分别比较：
检查共享 gold 条款与问法字符 2-gram Jaccard 相似度，避免只换几个词就当作新题。

| qid | 组 | gold 条款 | 与开发题共享条款 | 与改写候选共享条款 | 最大问法相似度 | 最相近题 | 判定 |
|---|---|---|---|---|---|---|---|
| N01 | vague_role | rail_quality:art-8 | - | - | 0.1311 | dev/D05 | 未发现直接重叠（同语料新题） |
| N02 | vague_role | rail_quality:art-23 | - | - | 0.1020 | dev/D07 | 未发现直接重叠（同语料新题） |
| N03 | vague_role | rail_quality:art-32 | - | - | 0.0357 | dev/D02 | 未发现直接重叠（同语料新题） |
| N04 | vague_role | construction_quality:art-37,construction_quality:art-38,rail_quality:art-39 | - | F06:construction_quality:art-37；F11:construction_quality:art-37；F12:construction_quality:art-37 | 0.0408 | rewrite/F06 | 共享条款家族 |
| N05 | vague_role | construction_quality:art-39,construction_quality:art-40,rail_quality:art-33 | - | F02:construction_quality:art-40 | 0.1111 | dev/D08 | 共享条款家族 |
| N06 | vague_role | rail_quality:art-42 | - | - | 0.1556 | rewrite/F16 | 未发现直接重叠（同语料新题） |
| N07 | vague_role | construction_quality:art-35,rail_quality:art-35 | - | - | 0.0847 | dev/D04 | 未发现直接重叠（同语料新题） |
| N08 | vague_role | rail_quality:art-54 | - | - | 0.0870 | dev/D05 | 未发现直接重叠（同语料新题） |
| N09 | vague_role | rail_quality:art-47,rail_quality:art-5 | - | - | 0.1111 | dev/D05 | 未发现直接重叠（同语料新题） |
| N10 | vague_role | construction_quality:art-22,rail_quality:art-21 | - | - | 0.0943 | dev/D09 | 未发现直接重叠（同语料新题） |
| N11 | multi_requirement | construction_quality:art-18,construction_quality:art-34,rail_quality:art-19,rail_quality:art-34 | - | - | 0.0588 | dev/D04 | 未发现直接重叠（同语料新题） |
| N12 | multi_requirement | rail_quality:art-43,rail_quality:art-44 | - | - | 0.0909 | rewrite/F01 | 未发现直接重叠（同语料新题） |
| N13 | multi_requirement | construction_quality:art-48,construction_quality:art-50,rail_quality:art-50,rail_quality:art-51 | - | - | 0.0685 | dev/D08 | 未发现直接重叠（同语料新题） |
| N14 | multi_requirement | construction_quality:art-49,rail_quality:art-61 | - | - | 0.1897 | rewrite/F02 | 未发现直接重叠（同语料新题） |
| N15 | multi_requirement | construction_quality:art-54,rail_quality:art-56 | - | - | 0.1525 | dev/D04 | 未发现直接重叠（同语料新题） |
| N16 | multi_requirement | construction_quality:art-63,rail_quality:art-64 | - | - | 0.1212 | dev/D04 | 未发现直接重叠（同语料新题） |
| N17 | multi_requirement | construction_quality:art-57,rail_quality:art-59 | - | - | 0.1343 | dev/D04 | 未发现直接重叠（同语料新题） |
| N18 | multi_requirement | construction_quality:art-17,construction_quality:art-59,rail_quality:art-18 | - | - | 0.1607 | dev/D06 | 未发现直接重叠（同语料新题） |
| N19 | multi_requirement | construction_quality:art-41,construction_quality:art-66,rail_quality:art-33 | - | - | 0.1905 | dev/D08 | 未发现直接重叠（同语料新题） |
| N20 | multi_requirement | construction_quality:art-58,rail_quality:art-60 | - | - | 0.1167 | dev/D04 | 未发现直接重叠（同语料新题） |
| N21 | no_answer | - | - | - | 0.1026 | rewrite/F14 | 未发现直接重叠（同语料新题） |
| N22 | no_answer | - | - | - | 0.4062 | rewrite/F15 | 未发现直接重叠（同语料新题） |
| N23 | no_answer | - | - | - | 0.2895 | rewrite/F16 | 未发现直接重叠（同语料新题） |
| N24 | no_answer | - | - | - | 0.1389 | rewrite/F15 | 未发现直接重叠（同语料新题） |
| N25 | no_answer | - | - | - | 0.1026 | rewrite/F07 | 未发现直接重叠（同语料新题） |
| N26 | no_answer | - | - | - | 0.2432 | dev/D11 | 未发现直接重叠（同语料新题） |
| N27 | no_answer | - | - | - | 0.1000 | rewrite/F04 | 未发现直接重叠（同语料新题） |
| N28 | no_answer | - | - | - | 0.1351 | rewrite/F14 | 未发现直接重叠（同语料新题） |
| N29 | no_answer | - | - | - | 0.1026 | rewrite/F14 | 未发现直接重叠（同语料新题） |
| N30 | no_answer | - | - | - | 0.1667 | dev/D06 | 未发现直接重叠（同语料新题） |

## 说明

- 本批只使用同一 A/B 语料，因此即使没有共享 gold 条款，也不能宣称跨主题泛化。
- 20 道同语料改写候选单独存放于 `data/task_b_rewrite_candidates.jsonl`，未混入本批。
- 若上表出现共享条款或高相似度，复核时应判断是否降级为同语料改写，而不是新题。
- N04/N05 与改写候选 F06/F11/F12/F02 共享部分条款；这是为保留正确答案而接受的同语料重叠，不删除正确答案。

