# 计时验证页会话管理修复记录

日期：2026-11-03
基线：commit `6a9aa37`
范围：只改计时测试入口的会话管理（`scripts/ux_trial_server.py`、`scripts/ux_trial_page.html`），
未改检索模型、语料、排序参数或拒绝规则；`TaskBSystem.answer(q, "hybrid_top5")` 与自动补证关闭保持不变。

## 1. 三种状态

| 状态 | 页面显示 | 服务端 | 允许的操作 |
| --- | --- | --- | --- |
| 未开始 | 当前状态：未开始 | `phase=idle`，`current_run_id=None` | 选择任务、开始 |
| 进行中 | 当前状态：进行中 | `phase=active` | 搜索、再次查询、查看原文、中止、结束 |
| 已结束 | 当前状态：已结束 | `phase=ended` | 只能选择下一个任务并开始 |

- 进行中时"开始任务"按钮与任务选择框禁用；即使绕过前端，`/api/start` 也返回 409 `session_active`。
- 中止是独立的结束方式：`outcome=aborted`，写入 `task_ended` 事件，不覆盖任何已有记录。
- 每次开始都生成新的 `run_id`，并新建 `logs/ux_trial/runs/<run_id>/`；不会续写上一轮的目录。

## 2. 开始前的页面清理

点击"开始任务"后先执行 `resetTaskView()`：停止并清空计时器、清空结果区与证据勾选、隐藏结束面板与
结束摘要、清空备注与题面、恢复"搜索/再次查询/结束/中止"的初始可用状态、清除 `localStorage` 中的
旧运行编号，然后再请求新运行。新题面只在服务端返回成功后才渲染，失败时回到未开始状态。

## 3. 服务端拒绝与留痕

| 情况 | HTTP | 记录位置 |
| --- | --- | --- |
| 进行中再次开始 | 409 `session_active` | 进行中 run 的 `events.jsonl` + `rejected_events.jsonl` |
| 重复结束 | 409 `run_already_ended` | 该 run 的 `events.jsonl`（原 `outcome/duration_ms/ended_at` 不变） |
| 未开始就搜索/结束 | 404 `run_not_found` | `page_events.jsonl` + `rejected_events.jsonl` |
| 证据 ID 不在实际展示结果中 | 400 `evidence_not_in_displayed_results` | 该 run 的 `events.jsonl`，任务保持 `active` |
| 问题与题面不一致 | 400 | `question_mismatch` 事件 |
| 1.2 秒内重复提交 | 409 | `duplicate_query` 事件 |

`displayed_evidence` 在每次检索后累积记录实际展示过的 `article_id`；拒绝时不改写 `run.json` 的
既有结论字段，只追加事件与 `rejections`。

## 4. 计时起点与时间戳含义

- `client_click_epoch_ms`：页面点击"开始任务"的客户端毫秒时间戳，由请求体传给服务端。
- `start_request_received_epoch_ms`：服务端收到开始请求的时刻。
- `start_response_sent_at`：服务端发出开始响应的时刻。
- `task_view_ready_client` 事件：页面收到响应并渲染题面的时刻，带 `roundtrip_ms`（点击到渲染完成）。
- `duration_ms`：`end_request_received_epoch_ms - client_click_epoch_ms`，**包含请求/响应往返**。
- `duration_server_ms`：服务端收到开始请求到收到结束请求。
- `duration_client_reported_ms`：页面 `performance.now()` 差值，仅作对照。
- 计时器起点是点击瞬间，不是 `await` 返回之后；因此网络延迟不会被悄悄算成零。
- `clock_note` 字段随 `run.json` 落盘，说明以上口径。

题面仍然只在点击开始后显示：`/api/start` 是唯一返回题面的接口，未开始时页面 DOM 里没有题面文本。

## 5. 实测结果

### 5.1 服务端实测（真实检索调用，29 项全部 PASS）

脚本 `scripts/ux_trial_session_check.py` 在 8766 端口起了独立服务实例，对真实接口发请求，
检索为真实 `hybrid_top5` 调用。结果文件：`logs/ux_trial/session_check_result.json`。

| 场景 | 内容 | 结果 |
| --- | --- | --- |
| S1 | 第一轮 task1 → 结束，第二轮 task2 → 结束，run_id 不同 | PASS，两目录事件各 5 条，互不含对方 run_id |
| S2 | task3 进行中再次开始 | PASS，409 `session_active`，`start_rejected` 已落盘 |
| S3 | task3 结束后再次结束 | PASS，409 `run_already_ended`；`outcome/duration_ms/ended_at` 与结束前一致 |
| S4 | 不存在的 run 搜索/结束 | PASS，404，`rejected_events.jsonl` 保留两条 |
| S5 | 结束时报 `rail_quality:art-999` | PASS，400；任务仍 `active`；改合法 ID 后可正常结束 |
| S6 | task2 直接中止 | PASS，`outcome=aborted`，`status=ended` |
| S7 | 进行中调用 `/api/session` 并记 `page_reloaded` | PASS，返回 `active=true`、`elapsed_ms>0`，事件写入原 run |
| S8 | 时间戳 | PASS，`click` 与 `recv` 相差 71 ms；`duration=544 > server=473`；`timer_basis=client_click` |

产生的运行：`ux-20261103T135901-4d36`、`ux-20261103T135902-90f2`、`ux-20261103T135902-6ba7`、
`ux-20261103T135902-86e5`、`ux-20261103T135902-7908`、`ux-20261103T135902-950c`。

### 5.2 浏览器实测（Edge，真实点击，OCR 核对界面文字）

| 步骤 | 观察 | 结果 |
| --- | --- | --- |
| 初始 | "当前状态：未开始"，搜索/再次查询不可用 | PASS |
| 开始 task1 | 状态转"进行中"，开始按钮与任务框禁用，题面出现，`init_ms=1073.2` 单列 | PASS |
| 搜索 | 5 条，A8 第 1 位，未截断 | PASS |
| 刷新（F5） | 出现恢复横幅"已进行 47.2 秒"，状态回到未开始 | PASS |
| 恢复 | 题面与结果恢复，计时续接 | PASS |
| 中止 | "结束状态：aborted；已选证据：无；用时 85.3 秒" | PASS（run `ux-20261103T140041-ad38`） |
| 第二轮 task2 | 新 run、旧结果清空；搜索 A61 第 1 位；结束 `found`，选中 `rail_quality:art-61` | PASS（run `ux-20261103T140355-6aa8`） |
| 第三轮 task3 | 新 run、旧结果清空；搜索 `refuse` 显示"本次未提供充分依据"；结束 `not_found` | PASS（run `ux-20261103T140624-44e0`） |
| 二次刷新恢复 | 刷新后等待，恢复时页面计时 42.8 秒 vs 服务端 `elapsed_ms=43256.0` | PASS（run `ux-20261103T140747-7c46`） |
| 结束时序 | 点击 14:07:47、服务端收到 14:07:47（差 7 ms）、刷新、恢复 `elapsed=41388.6`、结束 `74039 ms` | PASS |

### 5.3 仅代码检查、未单独实跑的部分

- 未知 `task_id` 的 400 拒绝分支。
- 前端 `state.ending` 双击防抖（服务端重复结束 409 已实测兜底）。
- `resetTaskView()` 对证据复选框的清除（实测只观察了结果区被清空，未逐项核对复选框残留状态）。

## 6. 修复中发现并处理的问题

1. **恢复用了过期快照**：第一版刷新后点"恢复"使用的是页面加载时 `/api/session` 的旧 `elapsed_ms`，
   导致继续计时偏小（run `ux-20261103T140041-ad38` 页面显示 67.4 秒，服务端 85.3 秒）。
   已改为点击恢复时重新拉取 `/api/session`；run `ux-20261103T140747-7c46` 复测一致（42.8 vs 43.256 秒）。
   前一个 run 的偏小显示如实保留，不作为计时依据。
2. **服务重启后的旧 run**：页面刷新时 `localStorage` 里还留着上一实例的 run_id，服务端不认识，
   产生一条 `event_rejected run_not_found`（`rejected_events.jsonl` 13:59:56）。页面随后回到未开始状态。
   该噪声记录保留，不做清理。

## 7. 原试跑记录

`ux-20261103T112954-93ce`、`ux-20261103T114651-d3e5`、`ux-20261103T115958-2974` 三个目录文件
修改时间仍为 11:46、11:57，**未改写**；其 `run.json` 也没有本次新增的计时字段。
本轮只是新增目录，不覆盖历史。

## 8. 未解决问题

1. 屏幕坐标点击仍不可靠（滚动后按钮位置变化），本轮浏览器测试多次靠 OCR 重新定位；页面未引入键盘可达的
   证据选择方式。
2. 中止按钮在恢复横幅中直接结束时，页面会短暂显示空白任务面板（`taskPanel` 被 `settleEnded` 打开）。
3. 服务重启后旧 run 的刷新事件会记为 `event_rejected`，属预期噪声但会出现在拒绝日志里。
4. 计时仍是自动化代理操作耗时的口径；本轮所有 `duration_ms` 都不能作为真人耗时或效率结论。
5. 未测多人并发或多标签页同时操作同一会话（服务端为单会话状态，第二个标签页只能恢复同一 run）。
