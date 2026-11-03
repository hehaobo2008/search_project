# G2-T1 耗时与结论矛盾核查

核查对象：commit `5d60f0b` 中 DocFetcher 可答题 `G2-T1`
核查时间：2026-11-03
证据文件：`reports/timing_trial_g2t1_timeout_evidence.json`

## 1. 矛盾点

同一份 `session.json` 里同时存在：

| 字段 | 值 |
| --- | --- |
| `duration_ms` | `224228`（224.228 秒） |
| `time_limit_seconds` | `300` |
| `timeout` | `false` |
| `note` | "第十三条全文已核对；操作过程超过300秒上限，按未完成记" |

结果报告 `reports/timing_trial_results.md` 与评分 `reports/timing_trial_scores.json` 都按
224.2 秒、未超时处理，即 `note` 与其余三处（字段、报告、评分）不一致。

## 2. 原始记录位置

| 记录 | 路径 | 说明 |
| --- | --- | --- |
| 本地原始 session | `logs/timing_trial/df-20261103T153954-5418/session.json` | 文件 mtime `15:43:38.288`，与 `ended_at` 一致 |
| 上传副本 | `.upload_repo/reports/timing_trial_runs/df-20261103T153954-5418/session.json` | 字段值逐一比对与本地一致（见证据 JSON 的 `copy_note`） |
| 操作截图 6 张 | `work/tools/docfetcher/screens/tt_g2t1_*.png` | 原始未裁剪；归档副本在 `reports/timing_trial_screens/05_…`、`06_…` |
| 结果报告 | `reports/timing_trial_results.md` | 3.4 节、第 4 节表格、第 5 节评分 |
| 评分文件 | `reports/timing_trial_scores.json` | `rows[G2-T1]` |

每个文件的字节数与 SHA-256 已写入 `reports/timing_trial_g2t1_timeout_evidence.json`。

## 3. 时间线重建

| 时刻 | 事件 | 来源 |
| --- | --- | --- |
| 15:39:54.060 | 脚本写出题面，操作者首次看到 `G2-T1` 题面（计时起点） | `session.shown_at` / `shown_epoch_ms=1793691594060` |
| 15:40:00.253 | 完整题面搜索完成，结果区显示 A_spec(1219)/B(901)，截图 | `tt_g2t1_results.png` mtime |
| 15:40:43.100 | 尝试右键菜单，截图 | `tt_g2t1_menu.png` mtime |
| 15:41:17.327 | 双击预览、滚动无效，截图（仍为第 1 页） | `tt_g2t1_preview2.png` mtime |
| 15:42:03.892 | 用系统默认程序打开 A_spec.pdf，截图 | `tt_g2t1_pdf.png` mtime |
| 15:42:34.066 | PDF 内滚动到第十四条附近，截图 | `tt_g2t1_pdf2.png` mtime |
| 15:43:16.143 | 回滚定位到第十三条，截图 | `tt_g2t1_pdf3.png` mtime |
| 15:43:38.288 | 写入结束状态 `found`，`ended_epoch_ms=1793691818288` | `session.ended_at` + 文件 mtime |

`ended_epoch_ms - shown_epoch_ms = 224228`，与 `duration_ms` 完全一致；6 张截图 mtime 全部落在
15:39:54–15:43:38 之间且顺序与操作步骤吻合。

## 4. 矛盾原因

`note` 是结束命令里手写的字符串，不是脚本计算结果。写 `note` 时我按主观印象认为已过 5 分钟，
没有回看 `duration_ms`；同一时刻脚本用真实时间戳算出 224.228 秒并置 `timeout=false`。
换言之：

- **数值以时间戳为准**：224.228 秒，未超过 300 秒。
- **`note` 是错误表述**：它与同一文件里的 `duration_ms`、`timeout` 自相矛盾。

此外，本轮结束前我把当前系统时间估计偏晚约 3 分钟（以为是 15:46 左右，实际 15:43:38），
这是 `note` 判断错误的直接来源。

## 5. 可独立核实的程度

**可核实**：

1. 耗时 224.228 秒：由 `shown_epoch_ms` 与 `ended_epoch_ms` 两个字段重算，且 `session.json` 的
   文件 mtime 与 `ended_at` 吻合。
2. 操作发生在该区间：6 张截图的文件系统 mtime 构成完整且递增的时间序列，覆盖 15:40:00–15:43:16。
3. 第十三条确实在结束前被读到：`tt_g2t1_pdf3.png`（15:43:16）已由 OCR 复核出该条正文。

**不可核实或只能部分核实**：

1. **没有录屏**，无法逐帧复核输入、点击与页面响应。
2. **`actions` 不是实时日志**：三条动作时间戳集中在 `15:43:37.99–15:43:38.20`（结束前 0.3 秒内），
   是结束前一次性补写的，不能作为逐步时间证据；`G2-T2` 同样有 `15:39:42` 集中补写的情况。
3. **计时起点由执行者脚本写入**：`shown_at` 是 `tt_df.py start` 的输出时刻，无法独立证明
   "此前未看过题面"；执行者同时是出题者，已声明非盲。
4. 截图只能证明"某个时刻屏幕上是什么"，不能证明两次截图之间的全部操作。

结论：**耗时数值可核实，`note` 的超时说法不可核实且与字段冲突**。

## 6. 处置（不改原记录）

按照"保留原记录、不推测、不覆盖"的要求：

- `logs/timing_trial/…/session.json` 原文保留，`note` 不修改，`timeout=false` 不修改。
- `reports/timing_trial_results.md` 与 `reports/timing_trial_scores.json` 不修改（本轮按要求不改实验结果）。
- 核查结论以本文件为准：

| 项 | 结论 |
| --- | --- |
| 完成状态 | **限时内完成（224.228 秒 < 300 秒）**，依据时间戳，不依据 `note` |
| `note` | **错误表述**，应视为无效文字，不参与评分 |
| 评分 | **维持"充分（正确）"**；评分依据是证据内容与来源，与耗时无关 |
| 是否需要标"待核" | 不需要。完成状态可由两路时间证据确认；仅 `note` 文字错误 |

如果复核方要求"必须有录屏或实时逐步日志才能确认"，则该题的完成状态应改为**待核**；
本文件已把这一判断条件写明，供复核方选择，不代替其决定。

## 7. HCS `G1-T1` 未勾选证据对评分的影响

事实：`run.json` 中 `selected_evidence = []`，同时存在 `original_open_requested`（`rail_quality:art-12`）
与 `original_confirmed`（`rail_quality:art-12`）；展示证据第 1 位也是 `rail_quality:art-12`
（98/98 字符未截断）。三者指向同一条，只是没有进入 `selected_evidence`。

影响：

1. **按协议口径（第 8 节"展示或选中证据包含参考条款"）**：展示证据已包含 A12，且操作者声明已核对原文，
   "充分（正确）"成立，不依赖勾选。
2. **若复核方坚持只看"操作者选中的依据"**：该题缺少 `selected_evidence`，只能记为
   "展示充分、选择缺失"，评分应改为**待核**，不能直接算正确。
3. 两种口径的分歧源于同一处：结束时证据复选框没有被点中（坐标不稳）。
   好在 `original_open_requested` 与 `original_confirmed` 都绑定 `rail_quality:art-12`，
   与展示第 1 位一致，因此"操作者核对的是哪一条"在事件层面可以确定；
   缺的只是"选中的依据"这一字段本身。

本轮不修改评分，但在此明确：**`G1-T1` 的"充分"判定依据是展示证据，不是选中证据**；
若采用更严格口径，该题应与 `G2-T1` 一样进入待核。

## 8. 协议中的 `actions.jsonl` 是否存在

**不存在。**

- 协议 `reports/timing_trial_protocol.md` 第 7 节写的是
  `logs/timing_trial/<session_id>/session.json` + `actions.jsonl`。
- 实际实现只有 `session.json`，动作记录嵌在它的 `actions` 数组里；
  `logs/timing_trial/` 与 `reports/timing_trial_runs/` 下都找不到任何 `actions.jsonl`。
- 因此"逐动作实时日志"这一协议项**未落实**：`actions` 既不是独立文件，也不是实时写入。

这属于协议与实现不一致的记录缺陷，已在此登记，不在本轮修复范围内。

## 9. 保留声明

本轮只新增本核查文件与证据 JSON，未修改：

- 任何 `session.json`、`run.json`、`events.jsonl`
- `reports/timing_trial_results.md`、`reports/timing_trial_scores.json`
- 任何截图

`reports/timing_trial_g2t1_timeout_evidence.json` 记录了上述文件在核查时的字节数与 SHA-256，
可用于确认"核查期间未被改写"。
