# 两场原始记录的上传说明（脱敏副本）

上传时间：2026-11-03
来源：本机 `logs/df_lookup_20261103/`、`logs/hcs_explore_20261103/`
性质：**脱敏副本**。原始文件保留在本机，未修改；本目录只替换了本机路径字符。

## 1. 脱敏规则

| 规则 | 替换为 | 命中次数 |
| --- | --- | --- |
| 项目根目录（含反斜杠/正斜杠变体） | `<PROJECT_ROOT>` | 6 |
| 本机临时目录 | `<TEMP>` | 1 |
| 其它盘符绝对路径 | `<LOCAL_PATH>` | 15 |

仅做字符串替换：**未改动时间戳、事件顺序、字段结构、行数，以及已有的 `backfilled`/`note` 补记标记**。
已校验：`df_lookup_20261103/events.jsonl` 65 行、`hcs_explore_20261103/ops_log.jsonl` 16 行，
前后行的 `ts` 序列完全一致；全部 JSON/JSONL 可正常解析。

## 2. 文件清单（28 个）

### DocFetcher 场（`df_lookup_20261103/`，3 个）

- `events.jsonl`（65 条事件）
- `summary.json`
- `REPORT.md`

### HCS 场（`hcs_explore_20261103/`，17 个）

- `env_baseline.json`、`env_end_load.json`
- `ops_log.jsonl`（16 条）
- `q1_search.json`、`q2_search.json`、`q3_search.json`、`q4_search.json`
- `q1_original_check.json`、`q2_original_check.json`、`q3_original_check.json`、`q4_original_check.json`
- `server_start.json`、`server_stop.json`、`server_stdout.log`
- `summary.json`、`summary.md`
- `tasks_only.json`（只含题面，无 gold、条号、页码、评分口径）

### HCS 对应 run（`hcs_explore_20261103/runs_snapshot/`，8 个）

`ux-20261103T181837-608b`、`ux-20261103T181910-9029`、`ux-20261103T181927-ca43`、`ux-20261103T181957-a65d`
各含 `events.jsonl` 与 `run.json`。

## 3. 未上传的内容与原因

| 内容 | 原因 |
| --- | --- |
| `df_lookup_20261103/screens/`（16 张 PNG） | 界面截图含本机文件路径列与桌面信息，脱敏需裁剪像素；本轮按要求只推原始文本记录，截图留在本机 |
| `corpus/articles.jsonl`、`corpus/docs_manifest.json` | 属原始法规语料，不在本次"两场记录"范围 |
| `work/raw/A_spec.pdf`、`work/tools/docfetcher/test_corpus/*.pdf` | 原始法规文件，不上传 |
| `reports/timing_trial_questions.json` 等含评分依据的文件 | 不在本次记录范围 |

注意：`run.json`、`q*_search.json` 中保留了检索返回的**单条证据摘录**（每条不超过 400 字符，
来自公开官方网页），这与"整部法规全文"不同；如需连单条摘录一并去除，须另行裁剪并会改变原始记录。

## 4. 缺失或无法归属的事件（未推算、未补造）

1. **DocFetcher 的 search 事件没有 `qid`**：`search_start` 8 条、`search_submitted` 8 条、
   `search_result` 8 条全部不带题目编号，**无法可靠归属到 Q1–Q4**。本目录保留原样，不做时间上的推断。
2. **DocFetcher 的 Q4 没有 `open_original_*` 事件**，只有 `question_begin → answer_not_found → question_end`。
3. **DocFetcher 的 Q1 记为 `open_original_attempt`（未确认打开）**，Q2/Q3 记为 `open_original_confirmed`。
4. **HCS 的 `ops_log.jsonl` 中 `q1_ended`/`q2_ended`/`q3_ended`/`q4_ended` 四条没有时间戳字段**
   （其余 12 条有 `logged_at`）。这四条按原样保留为缺时间戳，未用相邻事件推算。
5. **HCS 的 `runs/` 目录在采集时为空**，对应运行记录来自 `runs_snapshot/`；本目录只上传
   `runs_snapshot/`，不存在"从空目录推算"的情况。
6. **DocFetcher 有两条 `backfilled: true`**（`load_sample_backfilled`、`app_start_recorded`），
   以及 `index_state`/`index_build_span_recorded` 上的说明"索引早于本场建立、建索引耗时不可得"。
   这些标记原样保留。

## 5. 未做的事

- 未重跑任何一题、未重算耗时、未重新生成事件
- 未修改本机原始文件
- 未补充任何缺失的时间戳
- 未计算效率对比

## 6. 校验位置

脱敏操作由 `work/stage_trial_logs.py` 执行，统计写入 `work/trial_logs_redaction_stats.json`
（`files=28, root_hits=6, path_hits=15, temp_hits=1`）。