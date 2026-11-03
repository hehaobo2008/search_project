# 计时入口结束竞态修复记录

日期：2026-11-03
基线：commit `abb8870`
范围：只改计时入口（`scripts/ux_trial_server.py`、`scripts/ux_trial_page.html`）与会话检查脚本；
未改检索方法、语料、模型、排序参数或拒绝规则。

## 1. 原有竞态

`abb8870` 的结束流程是"先检查 `status == active`，再在锁内写入结束状态"，而检索在锁外执行。
于是存在三类交错：

1. 检索进行中（锁外 `TaskBSystem.answer`）时，另一请求可以结束该 run；检索返回后仍会
   `queries.append` 并写 `run.json`，页面还会渲染这批"结束之后才到"的结果。
2. 两个结束请求同时通过 `status` 检查，都能把 run 写成 ended 并各写一次 `task_ended`。
3. 同一 run 的两个检索请求可以同时进入，产生重复查询记录。

## 2. 修复方式

### 2.1 搜索占位（search token）

- `/api/search` 在锁内完成"状态检查 + 占位"：`search_running=True`，并分配一次性 `search_token`；
  已在搜索中时返回 409 `search_in_progress`。
- 检索在锁外执行。
- 返回后重新取锁，按 `status == active && search_token == token` 判定是否仍然有效：
  - 有效：写入 `queries` / `displayed_evidence`，记 `results_ready`；
  - 失效（已结束或被取消）：**不写入、不返回结果**，记 `search_result_discarded`，
    响应 409 `search_discarded`。

### 2.2 结束与搜索不交错

- 搜索进行中，普通结束请求返回 409 `search_in_progress`（"等待搜索结束后才能结束"），
  任务保持 `active`，等检索完成后可正常结束。前端同时禁用"结束任务并记录"与"中止任务"。
- 需要立即停止时，结束请求可带 `cancel_search=true`：服务端作废该 `search_token`、记
  `search_cancelled`，再正常结束；随后迟到的检索结果按 2.1 判定为失效并记 `search_result_discarded`。
- 前端没有"取消搜索并结束"按钮，该路径只用于极端恢复与自动化测试。

### 2.3 原子保护

- 开始：`new_run` 全程在 `RLock` 内完成"检查是否已有 active run + 创建 run + 设置 current_run_id"。
- 搜索：状态检查、占位、结果写入、丢弃判定都在同一把锁内，锁外的只有检索本身。
- 结束：状态检查、搜索占位检查、证据校验、结束字段写入、`task_ended` 事件全部在同一把锁内，
  重复或并发结束只有一个能进入，其余返回 409 `run_already_ended`。
- `run.json` 改为"临时文件 + `os.replace`"原子替换，避免并发写出半截文件；`events.jsonl` 追加也在锁内。
- 已结束 run 的 `outcome` / `duration_ms` / `ended_at` 不被后续请求改写；被拒请求只追加事件。

## 3. 计时说明与局限（页面同步显示）

| 项 | 来源 | 含义 |
| --- | --- | --- |
| `client_click_epoch_ms` | 浏览器 `Date.now()`（点击开始） | 任务计时起点，随请求体提交 |
| `end_click_epoch_ms` | 浏览器 `Date.now()`（点击结束） | 结束操作时刻 |
| `client_elapsed_ms` | 浏览器 `performance.now()` 差值 | 页面计时器读数，仅作对照 |
| `start_request_received_epoch_ms` | 服务端 `time.time()` | 服务端收到开始请求 |
| `end_request_received_epoch_ms` | 服务端 `time.time()` | 服务端收到结束请求 |
| `duration_ms` | 结束收到时刻 − 点击开始时刻 | 含请求与响应往返 |
| `duration_server_ms` | 结束收到 − 开始收到 | 不含客户端网络与渲染 |

局限（写给复核者，也写在页面 `timingNote`）：

- 两端都基于系统时钟；机器时钟被调整或被 NTP 校正时，差值会失真。
- `duration_ms` 只能给出"点击开始到服务端收到结束"的总时长，**无法拆出网络耗时**；
  想拆需要额外打点，本轮没有做。
- 页面刷新后 `performance.now()` 归零，恢复时以服务端 `elapsed_ms` 重算起点，
  刷新期间的时间仍计入任务，这是有意的。
- `init_ms`（模型/索引初始化）单列，不计入 `duration_ms`。
- 本轮所有 `duration_ms` 都是自动化代理在本机操作页面的耗时，不是真人耗时。

## 4. 证据与"已核对"的区分

- `/api/search` 返回的 `evidence` 只表示**服务端给出了候选条款**，`results_ready` 事件里带
  `displayed_is_not_reviewed: true`，页面也固定显示"返回证据不代表已核对原文"。
- `displayed_evidence` 只用于约束结束时的 `selected_evidence` 合法范围，**不等于操作员看过**。
- 只有操作员点"确认原文已核对"才产生 `original_confirmed`，且这仍只是操作者声明，不是自动验证。
- 本轮浏览器实测中 `ux-20261103T150707-efc8` 的 `selected_evidence` 为空、`original_confirmed` 缺失，
  即便检索返回了 5 条证据，也不能据此认为操作员核对了 A8。

## 5. 实测结果

### 5.1 竞态脚本（真实检索 + 注入延时，20 项全 PASS）

`scripts/ux_trial_race_check.py` 起独立服务（端口 8767），用 `--search-delay-ms 1200`
在检索前注入固定延时，以稳定复现竞态窗口。**该延时只用于测试，日志里记作
`test_search_delay_applied`，检索方法与结果不变。**

| 场景 | 断言 | 结果 |
| --- | --- | --- |
| S1 慢搜索时点结束 | 409 `search_in_progress`，任务仍 active，搜索返回后写入 1 条查询，再结束成功 | PASS |
| S2 慢搜索时取消并结束 | 结束 200；迟到响应 409 `search_discarded`；`queries=0`、`displayed_evidence=0`；有 `search_cancelled` 与 `search_result_discarded` | PASS |
| S3 4 个并发结束 | 1 个 200、3 个 409；`task_ended` 仅 1 次；之后可开始新任务 | PASS |
| S4 结束后再发搜索 | 409 `run_not_active`，查询记录数不变 | PASS |
| S5 3 个并发搜索 | 1 个 200、2 个 409；只写入 1 条查询 | PASS |
| S6 计时 | `duration_ms(1865) >= duration_server_ms(1796) > 0`；延时与"未经核对"标记均在事件里 | PASS |

运行编号：`ux-20261103T150546-720c`（S1）、`ux-20261103T150548-18cf`（S2）、
`ux-20261103T150550-7e17`（S3）、`ux-20261103T150551-86ec`（S3 后续开始）、
`ux-20261103T150551-a075`（S4）、`ux-20261103T150552-a3d8`（S5）。

事件顺序可直接看出交错被拦住：

- S1：`query_submitted → test_search_delay_applied → end_rejected → results_ready → task_ended`
- S2：`query_submitted → test_search_delay_applied → search_cancelled → task_ended → search_result_discarded`
- S3：`results_ready → task_ended → end_rejected ×3`

结果文件：`logs/ux_trial/race_check_result.json`。

### 5.2 浏览器实测（真实点击，注入延时 2500 ms）

run `ux-20261103T150707-efc8`：

1. 点"搜索"后 0.6 秒内页面显示"正在搜索……完成按钮在搜索结束前不可用。"与
   "搜索进行中：结束与中止暂不可用，等待结果或等待超时。"
2. 在搜索窗口内点击"结束任务并记录"，**日志中没有 `end_rejected`**，说明按钮确实处于禁用状态，
   点击未产生结束请求；搜索结束后结果正常返回（5 条）。
3. 结果区顶部显示"以下为服务端返回的候选证据……不代表你已看到或核对"。
4. 结束时未勾选任何证据，`selected_evidence` 为空，用时 125.5 秒（含注入延时与人工查看）。

该 run 含 2.5 秒注入延时，其 `duration_ms` 不能当作检索耗时。

### 5.3 仅代码检查、未单独实跑

- 前端 `endTask` 内"搜索中直接返回"的二次保护（实测路径被按钮禁用挡在前面，未触发）。
- `cancel_search` 只能由接口触发，页面无入口（脚本已覆盖服务端行为）。

## 6. 原试跑记录

`ux-20261103T112954-93ce`、`ux-20261103T114651-d3e5`、`ux-20261103T115958-2974`、
`ux-20261103T140041-ad38`、`ux-20261103T140355-6aa8`、`ux-20261103T140624-44e0`、
`ux-20261103T140747-7c46` 均未改写，只新增目录。

## 7. 未解决问题

1. 屏幕坐标点击仍不可靠：本轮浏览器实测中一次点击落在"查看原文"链接上，产生了额外的
   `original_open_requested`（`rail_quality:art-8`），已保留不删。
2. 搜索没有超时与"取消搜索"的前端入口；检索卡住时只能等，或由接口带 `cancel_search` 结束。
3. 并发结束的输赢依赖加锁顺序，日志里只能看到"1 个成功、N 个 409"，无法提前指定哪个请求成功。
4. 注入延时是测试手段，`test_search_delay_applied` 会让该 run 的 `duration_ms` 偏大；
   分析时需排除这类 run。
5. 仍未做多人/多机计时，所有时长仅代表本机自动化代理操作。
