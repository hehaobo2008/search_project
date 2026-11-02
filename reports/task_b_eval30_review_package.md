# Eval30 题目与标注复核包

> **请先复核，不要运行新题检索成绩。** 本批标注由同一 AI 完成，未做真人独立复核。

## 内容

- 30 道新题：`data/task_b_eval30_questions.jsonl`
- 标注包：`reports/task_b_eval30_annotations.md`
- 题目家族重叠：`reports/task_b_eval30_overlap.md`
- 复核协议：`reports/task_b_eval30_review_protocol.md`
- 哈希清单：`reports/task_b_eval30_manifest.json`

## 组成

- 10 道模糊岗位描述
- 10 道多信息需求/跨条款
- 10 道看似相关但库内无充分答案

## 当前状态

- 标注：AI 草案，待独立复核；不是真人盲测。
- 检索：**未运行**；本包不含新题检索成绩。
- 现有 20 道同语料改写候选另存，未混入。

## 复核人请先检查

- [ ] 题目是否自然，是否只是换词。
- [ ] 每个信息需求与充分组合是否有原文依据。
- [ ] 无答案题是否确实没有充分答案。
- [ ] 是否与开发题共享条款；共享的应降级为同语料改写。
- [ ] 冻结题目、gold、配置、模型和语料 hash 后，再运行计分。
