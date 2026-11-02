# 任务B 实际运行记录（开发集探索）

> **重要边界：** 任务A人工闸门 H01-H08 尚未签字；本记录是在用户指令下开展的任务B开发集探索，**不是独立冻结测试成绩**，不用于宣称泛化或优于其他系统。冻结候选 20 题仍为 `unlabeled`，未运行。

## 一次运行身份

- 流水线 run_id：taskB-20261102T193549
- 任务与状态：B / 开发集探索已运行；冻结测试未标注、未运行
- 平台：当前 CodeArts Agent 会话，项目 `search_project`（截图待采集）
- 实际开始/结束及UTC偏移：2026-11-02T19:35:49.689019+08:00 至 2026-11-02T19:35:53.475311+08:00（UTC+08:00）
- 运行时：Python 3.13.2；onnxruntime 1.31.0 CPUExecutionProvider；tokenizers 0.23.3；jieba 0.42.1；rank_bm25 0.2.2；numpy 2.5.1
- 模型：BAAI/bge-small-zh-v1.5；分发仓库 Xenova/bge-small-zh-v1.5（ModelScope ONNX 转换）
- 模型 revision：`master` 分支下载；`onnx/model.onnx` SHA-256 `69a0b846f4f116b5e6aabf9546ea6754d02264f3211a13a1bd69b31b8040749a`（94851877 bytes）
- 模型许可：MIT（ModelScope 模型 API License=mit；BAAI 模型卡为 MIT；Xenova ONNX 转换仓库无独立 LICENSE 文件）
- 运行时配置：max_length=512；pooling=CLS token of last_hidden_state + L2 normalization；query 指令=`为这个句子生成表示以用于检索相关文章：`
- 语料：A 75 条 + B 82 条，条款级证据单元；不含 C 与旧版
- 配置 hash：`baa60e60e303ddaf39647f6146dcccafb0716df049256d8c4dcf049e700db39e`
- 开发问题集 hash：`b54e1230146af1bf61fc4966a4e18ee16d81b72f435f06af716d1d71e85f5fbd`；冻结候选 hash：`a18b7891e4cbb653d4e0981c514857e9f3d2faaae0ddcbe4568487003718d6cf`
- 语料 manifest hash：`9c6578527a447bf59412dbe6f5854c6c2aa9b8d9234bde1363e3b42e8137fed6`
- gold hash：包含在开发问题集与 `task_b_dev_results.json` 中，未独立冻结
- commit：项目未初始化 Git，无 commit
- 会话历史：本平台；截图待采集

## 实际命令与退出码

1. `python scripts/check_model.py` → exit=0，0.154s，日志 `logs/task_b/runs/taskB-20261102T193549/check_model.log`（357 bytes）
2. `python scripts/task_b_eval.py` → exit=0，1.714s，日志 `logs/task_b/runs/taskB-20261102T193549/eval_dev.log`（661 bytes）
3. `python scripts/run_task_b_tests.py` → exit=0，1.858s，日志 `logs/task_b/runs/taskB-20261102T193549/run_tests.log`（1267 bytes）
4. `python scripts/check_freeze.py` → exit=0，0.058s，日志 `logs/task_b/runs/taskB-20261102T193549/check_freeze.log`（150 bytes）

## 方法配置（开发集调试，未冻结）

- 词法：jieba `cut_for_search`，保护第X条/第X章/书名号/数字/英文；BM25Okapi
- 语义：BGE-small-zh-v1.5 ONNX，CLS pooling + L2；query 加中文检索指令，文档不加
- 融合：RRF k=60，每路候选 50；并列按 article_id 升序
- 输出预算：Top7 与 Top5+补证均每单元最多 400 字符、最多 7 单元（总上限 2800 字符）；Top5 辅助
- 补证：从 Top2 种子沿显式条款/修改关系补最多 2 条；目标须在融合前 10、版本已解析、排除重复；不自动回填；主题相关不混入
- 无答案：未知术语≥3，或未知≥1且最高语义相似度<0.62 时拒绝

## 检索结果（开发集 N=13）

| 方法 | 配对N | Hit | 全证据 | 命中组/总组 | 宏Recall | 微Recall | 单元均值 | 字符均值 | p50/p95 ms |
|---|---|---|---|---|---|---|---|---|---|
| 普通Top5（辅助） | 13 | 12/13 | 12/13 | 14/15 | 0.9231 | 0.9333 | 5.00 | 698.08 | 8.64/12.51 |
| 普通Top7（主基线） | 13 | 13/13 | 13/13 | 15/15 | 1.0000 | 1.0000 | 7.00 | 960.31 | 8.64/12.51 |
| Top5+≤2补证（主比较） | 13 | 13/13 | 13/13 | 15/15 | 1.0000 | 1.0000 | 5.08 | 708.62 | 8.64/12.51 |

## 配对变化与补证触发

- 补证组独有成功：0；Top7 独有成功：0；均成功：13；均失败：0
- 补证触发题数：1/13；补证单元总数：1
- 观察：补证组与 Top7 在开发集 Hit 相同；补证组平均使用 5.08 个单元、708.62 字符，Top7 为 7 个单元、960.31 字符。样本小，不能据此宣称补证更优。

## 独立分组

| 分组 | N | 正确 | 错误/其他 |
|---|---|---|---|
| 无答案 | 2 | 2 正确拒绝 | 0 错误输出证据 |
| 版本冲突 | 1 | 1 正确提示待核验 | 0 错版本/其他 |
| 引用歧义 | 2 | 2 正确提示 | 0 错误硬连 |

## 逐题摘要

| qid | 题型 | 问题 | Top5 | Top7 | 补证 | 单元/字符 |
|---|---|---|---|---|---|---|
| D01 | retrieval | 铁路工地试块送检要谁在场？检测记录签字的规定在哪？ | True | True | True | 5/721 |
| D02 | retrieval | 施工单位设立的工地试验室出具检测结果后，资料如何签认和保存？ | True | True | True | 5/784 |
| D03 | retrieval | 铁路规定第66条提到的条例第65条原文在哪？ | False | True | True | 6/578 |
| D04 | retrieval | 监理单位与施工单位串通降低工程质量，铁路规定第67条依照的上位条例怎么处罚？ | True | True | True | 5/1109 |
| D05 | retrieval | 铁路建设项目开工前在哪里办理工程质量监督手续？ | True | True | True | 5/480 |
| D06 | retrieval | 铁路工程竣工验收由谁组织，提前几天通知监管部门，验收后多久备案？ | True | True | True | 5/612 |
| D07 | retrieval | 隐蔽工程在隐蔽前，施工单位应当通知哪些单位？ | True | True | True | 5/482 |
| D08 | retrieval | 施工中出现质量问题或者竣工验收不合格，施工单位应当承担什么责任？ | True | True | True | 5/552 |
| D09 | retrieval | 施工图设计文件未经审查批准可以使用吗？审查办法由谁制定？ | True | True | True | 5/660 |
| D10 | retrieval | 建设单位能否明示或者暗示施工单位使用不合格的建筑材料？进场材料由谁组织检查？ | True | True | True | 5/626 |
| D16 | retrieval | 试块取样送检由谁监督？检验记录由谁签字？ | True | True | True | 5/634 |
| D17 | retrieval | 施工单位偷工减料、使用不合格材料怎么处罚？未对涉及结构安全的试块取样检测又怎么处罚？ | True | True | True | 5/850 |
| D18 | retrieval | 铁路规定第66条对未取样检测的罚款，依照的上位条例条款原文是什么？ | True | True | True | 5/1124 |
| D11 | no_answer | 铁路工程混凝土配合比设计的具体计算方法是什么？ | 正确拒绝 | - | - | - |
| D12 | no_answer | 铁路建设工程施工招标评标的评分细则和分值表在哪里？ | 正确拒绝 | - | - | - |
| D13 | version_conflict | 2015年版铁路建设工程质量监督管理规定第70条规定了什么？ | 版本待核验 | - | - | - |
| D14 | citation_ambiguity | 铁路规定第30条和条例第31条是不是直接引用关系？ | topic_related | - | - | - |
| D15 | citation_ambiguity | 铁路规定第1条是不是直接引用了条例第29条？ | explicit_document | - | - | - |

## 回归测试

- 任务B测试：8 项，通过 8，失败 0，错误 0（`logs/task_b/runs/taskB-20261102T193549/run_tests.log`）。
- 覆盖：检索确定性、三方法预算、补证 base5 不变、D03 补到 B65、无答案/版本/歧义分支、指标函数、模型 hash、冻结候选未标注

## 失败与限制

- 任务A人工闸门未签字；任务B正式冻结测试未开始，不得进入“测试成绩”表述。
- 开发集仅 13 道检索题；补证组无 Top7 之外的独有成功；无答案规则样本仅 2 题。
- BGE 使用 ModelScope 的 ONNX 转换版本，非 BAAI 原始 PyTorch 权重逐字节一致；已固定文件 hash，未做转换等价性验证。
- 未做模型 revision 多版本比较、FP16/量化、ONNX 与 PyTorch 输出对比、手机端推理或性能测试。
- 未做真实用户试用、阅读负担、核查用时和岗位收益测试。

## 可主张范围

本轮可主张：在公开 A/B 语料与 13 道开发题上，中文 BM25+BGE+RRF 检索链路可运行；Top7 与补证组均达到 13/13 Hit；版本冲突、无答案和引用歧义分支能给出待核验/拒绝/主题相关提示。不可主张：独立测试成绩、领域泛化、优于其他系统、端侧性能、真实业务提效，也不可把开发集结果追认为任务A闸门通过。
