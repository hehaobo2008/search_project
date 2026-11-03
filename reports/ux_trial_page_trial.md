# 本机回环页面验证记录（HCS 任务计时验证页）

日期：2026-11-03
运行环境：Windows 本机回环，`http://127.0.0.1:8765/`，Edge 浏览器
代码：`scripts/ux_trial_page.html`、`scripts/ux_trial_server.py`（Python 标准库 `http.server`，未引入新依赖）

## 1. 本轮做什么、不做什么

**做**：用本机回环单页，把"开始任务 → 读题输入 → 搜索 → 看结果 → 打开原文 → 结束任务"走一遍，
验证页面能展示真实条文/文件名/版本/截断提示、出处能打开对应位置、事件能如实落盘。

**不做**：不开发完整 App；不做公网部署；不装新工具、不下载模型、不接付费 API；
不运行新题（只用 3 个已见任务）；不计算真人节省时间；不宣称效率提升；页面不读 gold。

## 2. 配置锁定

| 项 | 值 |
| --- | --- |
| 检索入口 | `TaskBSystem.answer(question, "hybrid_top5")`（与评测同一入口） |
| 方法 | `hybrid_top5` |
| 自动补证 | 关闭（`auto_supplement = false`） |
| 配置标识 | `cfg-0037f32996f8-hybrid_top5` |
| 模型/索引初始化 | `init_ms = 821.9`（**单独记录，不计入单题计时**） |
| 证据展示上限 | 每条约 400 字符，`truncated` 显式展示 |

单题计时从"点击开始任务"起算，到"点击结束任务并记录"为止，包含读题、输入、搜索、原文核查。

## 3. 启动方法

```bat
python scripts/ux_trial_server.py --port 8765
```

输出 `ready=... init_ms=821.9 config_id=cfg-0037f32996f8-hybrid_top5` 后，本机浏览器打开
`http://127.0.0.1:8765/`。服务强制只监听 `127.0.0.1`；传其它 `--host` 会以退出码 2 拒绝启动。

日志位置：

- `logs/ux_trial/runs/<run_id>/run.json`：运行元数据、每次查询的证据全文与来源
- `logs/ux_trial/runs/<run_id>/events.jsonl`：逐条事件
- `logs/ux_trial/page_events.jsonl`：不属于任何 run 的页面级事件

## 4. 三题实测轨迹

> **计时性质声明**：以下 `duration_ms` 是**自动化代理在本机操作页面**的耗时，含代理截图、OCR 核对、
> 坐标重试等开销，**不是真人操作耗时**，不能用于任何效率结论。真人配对计时需按约定另行安排。

### 4.1 任务 1 —— 建设单位质量管理人员与检查记录留存

- run：`ux-20261103T112954-93ce`
- 题面：建设单位需要配备什么质量管理人员、谁留存检查记录？
- 结果：`answer`，5 条；第 1 位 `rail_quality:art-8`（《铁路建设工程质量监督管理规定》第八条），
  第 2 位 `construction_quality:art-50`（《建设工程质量管理条例》第五十条）；5 条均 `truncated=false`
- 操作：提交查询 →（再次查询一次）→ 重复提交被 1.2s 节流拦截并记 `duplicate_query` →
  点"查看原文"打开 `/locator/rail_quality#art-8` 并看到 A8 正文 → 点"确认原文已核对" → 结束（`found`）

事件时间线（节选）：

| 时间 | 事件 | 说明 |
| --- | --- | --- |
| 11:29:54.457 | `task_started` | `init_ms=821.9` 单列 |
| 11:31:16.628 | `query_submitted` | 读题+输入 82.2s |
| 11:31:18.469 | `results_ready` | `search_ms=1839.2`（首次查询含预热） |
| 11:33:14.797 | `query_again_client` | 操作者再次查询 |
| 11:33:15.108 | `duplicate_query` | 重复提交被拦截并记录 |
| 11:33:18.006 | `original_open_requested` | 打开 `rail_quality#art-8` |
| 11:35:07.639 | `original_confirmed` | 操作者确认已核对 A8 正文 |
| 11:45:42.218 | `task_ended` | `outcome=found`，`duration_ms=947761` |

**已知缺陷（如实记录）**：结束时选中证据被记成 `construction_quality:art-50`，实际核对的是
`rail_quality:art-8`。原因是页面滚动后坐标点击落到第 2 张卡片的复选框。原始 `run.json` / `events.jsonl`
未改写，更正说明见 `reports/ux_trial_task1_correction.md`。该 run 的 `selected_evidence` 不可用于评分。

### 4.2 任务 2 —— 竣工验收备案时限与逾期罚则

- run：`ux-20261103T114651-d3e5`
- 题面：竣工验收后多久备案，逾期备案罚则在哪？
- 结果：`answer`，5 条；第 1 位 `rail_quality:art-61`（《铁路建设工程质量监督管理规定》第六十一条，
  修正版 `amended_2021_12_23`，PDF 第 18 页），第 2 位 `construction_quality:art-49`；均未截断
- 操作：提交查询 → 打开 A61 原文（看到"逾期 30 天（含）以内处 20–30 万元""超过 30 天处 30–50 万元"）
  → 确认原文已核对 → 结束（`found`，选中 `rail_quality:art-61`）

| 时间 | 事件 | 说明 |
| --- | --- | --- |
| 11:46:51.534 | `task_started` | |
| 11:48:16.658 | `query_submitted` | 读题+输入 85.1s |
| 11:48:16.835 | `results_ready` | `search_ms=175.2` |
| 11:52:19.876 | `original_open_requested` | 打开 `rail_quality#art-61` |
| 11:55:48.312 | `original_confirmed` | 操作者确认 |
| 11:57:49 | `task_ended` | `duration_ms=658343` |

**过程说明**：鼠标点击"结束任务并记录"在页面滚动后未命中按钮，本 run 的结束改为经页面调用的
同一接口 `/api/end` 提交，`note` 字段已写明这一点。事件与字段均正常落盘，但页面停留在未结束视图，
说明"按钮坐标"仍是可用性缺陷。

### 4.3 任务 3 —— 环保验收监测因子与频次

- run：`ux-20261103T115958-2974`
- 题面：环保验收需要监测哪些因子、频次多少？
- 结果：`refuse`，0 条，页面显示 **"本次未提供充分依据。页面不推断资料中一定不存在答案。"**
- 操作：提交查询 → 结束（`not_found`，无选中证据）

| 时间 | 事件 | 说明 |
| --- | --- | --- |
| 11:59:58.216 | `task_started` | |
| 12:00:25.4 | `query_submitted` | 读题+输入 27.2s |
| 12:00:25.4 | `results_ready` | `decision=refuse`，`search_ms=158.4` |
| 12:01:31 | `task_ended` | `outcome=not_found`，`duration_ms=93408.7` |

本 run 无 `original_open_requested`：没有证据可打开，页面也不伪造出处。

## 5. 汇总

| 任务 | run_id | 结束状态 | 证据数 | duration_ms（代理操作，非真人） |
| --- | --- | --- | --- | --- |
| task1 | `ux-20261103T112954-93ce` | found（选中记录有误，见 §4.1） | 5 | 947761 |
| task2 | `ux-20261103T114651-d3e5` | found | 5 | 658343 |
| task3 | `ux-20261103T115958-2974` | not_found | 0（refuse） | 93408.7 |

页面不判定答对与否；是否答对、证据是否充分留给独立评分。

## 6. 截图

脱敏后仅保留页面内容区（已裁掉浏览器标签栏、地址栏、书签栏）：

- `reports/ux_trial_screens/01_page_initial.png` 初始页
- `reports/ux_trial_screens/02_task1_started.png` 任务 1 点开始后才显示题面
- `reports/ux_trial_screens/03_task1_results.png` 任务 1 结果列表（含文件名/版本/页码/截断说明）
- `reports/ux_trial_screens/04_task1_original_a8.png` 打开 A8 原文并定位
- `reports/ux_trial_screens/05_task1_ended.png` 任务 1 结束摘要
- `reports/ux_trial_screens/06_task2_results.png` 任务 2 结果（A61 第 1 位）
- `reports/ux_trial_screens/07_task2_original_a61.png` A61 原文，可读到罚款档次
- `reports/ux_trial_screens/08_task3_refuse.png` 任务 3 拒绝提示
- `reports/ux_trial_screens/09_task3_ended.png` 任务 3 以 not_found 结束

## 7. 示例日志

`logs/ux_trial/runs/ux-20261103T115958-2974/events.jsonl`：

```
{"ts": "2026-11-03T11:59:58.216...", "event": "task_started", "run_id": "ux-20261103T115958-2974", "task_id": "task3", "question": "环保验收需要监测哪些因子、频次多少？", "init_ms": 821.9, "method": "hybrid_top5", "config_id": "cfg-0037f32996f8-hybrid_top5"}
{"ts": "2026-11-03T12:00:25.4...", "event": "query_submitted", "run_id": "ux-20261103T115958-2974", "question": "环保验收需要监测哪些因子、频次多少？"}
{"ts": "2026-11-03T12:00:25.4...", "event": "results_ready", "run_id": "ux-20261103T115958-2974", "decision": "refuse", "evidence_ids": [], "result_count": 0, "search_ms": 158.4, "message": "本次未提供充分依据"}
{"ts": "2026-11-03T12:01:31...", "event": "task_ended", "run_id": "ux-20261103T115958-2974", "outcome": "not_found", "selected_evidence": [], "note": "", "duration_ms": 93408.7}
```

`run.json` 中每条证据都带 `article_id / article_no / doc_title / version_id / text / chars / full_chars /
truncated / source_url / source_sha256 / locator_route / pdf_route / pdf_page`，例如：

```
rail_quality:art-61  amended_2021_12_23  p18  158/158  truncated=false
```

## 8. 已发现的问题

1. **坐标点击不可靠**：页面滚动后，鼠标点"结束任务并记录"或证据复选框会落错位置。任务 1 因此把
   `selected_evidence` 记成了非选中项；任务 2 的结束只能改走接口。已通过保留原始记录 + 更正说明处理，
   但页面本身需改成键盘可达或按 `article_id` 定位。
2. **页面不刷新运行状态**：任务 2 经接口结束后，页面仍显示未结束视图，需要人工刷新或重新开始。
3. **"打开原文"只记录请求**：`original_open_requested` 与 `original_confirmed` 分离，点击不算定位成功，
   必须由操作者点"确认原文已核对"；本轮两次都在截图/OCR 中看到目标条文，确认由人给出。
4. **`page_unload_client` 时间口径**：该事件记的是 `performance.now()` 相对值，与 `duration_ms`
   不严格对应，仅作离页留痕，不能当计时用。
5. **代理耗时会被误读**：三题的 `duration_ms` 都远大于真人可能用时（15.8 / 11.0 / 1.6 分钟），
   因自动化操作含截图核对与重试；报告与日志都已标注，但对外的任何效率说法仍须等真人配对测试。

## 9. 结论

页面在"只读题面、不读 gold、只调同一检索入口"的前提下，能把真实条文、文件名、版本、页码、
截断状态和拒绝提示展示出来，出处可打开，事件可落盘。**本轮不产生任何效率或准确率结论**，
也不改变历史实验与首轮失败记录。
