# 任务B 题目家族重叠检查

本表用于阻止把同条款改写当成独立冻结测试。开发集与改写候选共享条款或问法的题，只能报告为同语料改写稳定性。

| 候选 | 题型 | 重叠开发题 | 重叠条款 | 判定 |
|---|---|---|---|---|
| F01 | retrieval | - | rail_quality:art-20 | 同条款家族 |
| F02 | retrieval | - | construction_quality:art-40 | 同条款家族 |
| F03 | retrieval | - | rail_quality:art-75 | 同条款家族 |
| F04 | retrieval | - | construction_quality:art-82 | 同条款家族 |
| F05 | retrieval | D01, D02, D16 | rail_quality:art-30, construction_quality:art-29, construction_quality:art-31 | 同语料改写（高重叠） |
| F06 | retrieval | - | construction_quality:art-37 | 同条款家族 |
| F07 | retrieval | D06 | rail_quality:art-16 | 同语料改写（高重叠） |
| F08 | retrieval | D17 | rail_quality:art-65, rail_quality:art-66 | 同语料改写（高重叠） |
| F09 | retrieval | - | construction_quality:art-7 | 同条款家族 |
| F10 | retrieval | D09 | construction_quality:art-11 | 同语料改写（高重叠） |
| F11 | retrieval | F06, F12 | construction_quality:art-37 | 同语料改写（高重叠） |
| F12 | retrieval | F06, F11 | construction_quality:art-37 | 同语料改写（高重叠） |
| F13 | retrieval | - | rail_quality:art-14 | 同条款家族 |
| F14 | no_answer | - | - | 未发现直接重叠；仍属同语料 |
| F15 | no_answer | - | - | 未发现直接重叠；仍属同语料 |
| F16 | no_answer | - | - | 未发现直接重叠；仍属同语料 |
| F17 | version_conflict | D13 | - | 同语料改写（高重叠） |
| F18 | version_conflict | D13 | - | 同语料改写（高重叠） |
| F19 | citation_ambiguity | - | rail_quality:art-62, construction_quality:art-60 | 同条款家族 |
| F20 | citation_ambiguity | D14 | rail_quality:art-30, construction_quality:art-29 | 同语料改写（高重叠） |

## 结论

- F05 ↔ D01/D02/D16；F07 ↔ D06；F08 ↔ D17；F10 ↔ D09：同主题、同条款、问法接近。
- F06/F11/F12 共享 B37；F17/F18 同属版本题；F19/F20 同属引用关系题。
- 因此 20 题不能称为独立冻结测试集；若运行，只能作为同语料改写测试，并明确不宣称跨主题泛化。
