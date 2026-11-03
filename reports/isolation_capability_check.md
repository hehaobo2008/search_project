# 双会话隔离能力核查

日期：2026-11-03
基线：commit `23b63f2`
范围：只核查当前 CodeArts 环境能否为同一套题建立 HCS / DocFetcher 两次彼此隔离的操作会话。
本轮不出新题、不运行正式计时、不修改检索算法。

## 1. 结论

1. **进程与日志层面可以隔离**：两个 HCS 实例可用不同端口并行，各有独立 `session_id`；DocFetcher 可复制一份便携版用独立索引目录。
2. **执行者层面做不到隔离**：当前只有一个交互式 OS 账户（`HC`），只有同一个 AI 模型实例；本会话已看过题面、参考依据和历史结果。**不能称为独立操作者，也不能称为盲测。**
3. **答案暴露点仍然存在**：题面文件 `reports/timing_trial_questions.json` 里同时存着 `reference[].text`（答案全文），HCS 的 `--tasks-file` 与 DocFetcher 的 `work/tt_df.py` 都读这份文件。

## 2. 实测核查结果

| 项 | 实测 | 能否隔离 |
| --- | --- | --- |
| OS 账户 | `whoami` = `HC`；`net user` 只有内置 Administrator/Guest 等，未见可用的第二个交互账户 | **不能**（未验证 Administrator 登录，切换会中断当前会话） |
| 仓库权限 | `icacls .` 显示 `Authenticated Users:(M)`，任何本机登录用户可读写 | **不能**做文件级隔离 |
| HCS 进程 | `--port` 可配；`--host` 强制 `127.0.0.1`；实测 8765 与 8768 同时运行，各自 `session_id` 不同 | **能**（进程/会话互不影响） |
| HCS 日志根 | `App.__init__` 里 `log_root = ROOT/logs/ux_trial`，无命令行参数 | **不能**做目录级隔离（run_id 唯一，不会覆盖，但两个实例写同一棵树） |
| HCS 题面释放 | `/api/tasks` 只返回 `{task_id, label}`；题面只在 `/api/start` 响应里返回；未开始时 `taskPanel` 隐藏 | **能**（题面延迟到开始后） |
| HCS 题面来源 | `--tasks-file` 直接读含 `reference` 全文的整份 JSON | **不能**（进程可读答案，执行者若有权读文件也能看） |
| DocFetcher 实例 | 单进程 26512、单索引 `hcstest`；便携版 225 MB，可整目录复制 | **能**（复制副本 + 独立索引目录即可双实例） |
| DocFetcher 题面呈现 | 没有独立呈现器；上一轮由 `work/tt_df.py start` 打印，该脚本读同一份含答案的 JSON | **不能**（同上） |
| A/B 文件 | `work/raw/A_spec.pdf` 与 `test_corpus/A_spec.pdf` 哈希一致（`4a815f2c…`），B 同理（`651fa253…`） | **能**（同一版本可校验；但两工具共享同一份文件，改动会同时影响） |
| 原文查看 | HCS：`/locator/<doc>` + `/pdf/<doc>`；DocFetcher：预览 + 外部 PDF | **能**（各自保留，互不替代） |
| 实时操作记录 | HCS：`run.json`/`events.jsonl` 逐事件实时写；DocFetcher：`session.json` 的 `actions` 实测为结束前补写（G2-T1 三条集中在 0.3 秒内） | HCS **能**；DocFetcher **不能** |

## 3. 哪些信息能隔离，哪些不能

**能隔离（物理上分开即可）**

- 进程与端口：HCS 两实例、DocFetcher 两副本
- 运行编号与会话状态：每个实例各自 `current_run_id`、`session_id`
- 日志与截图目录：可分别指定（HCS 需先加 `--log-root`）
- 索引：DocFetcher 副本用独立索引目录与索引名
- 题面显示时机：HCS 已做到"点击开始后才显示"

**不能隔离**

- **模型记忆**：同一 AI 实例已经看过题面与参考依据；子代理虽有自己的上下文窗口，但仍是同一模型、同一文件系统
- **文件读取权限**：单账户 + `Authenticated Users:(M)`，任何本机会话都能读 `corpus/`、`reports/timing_trial_questions.json`、历史日志
- **历史会话**：本会话的对话记录里已有答案与结果，无法对同一实例"忘记"
- **共享的 A/B 文件**：两工具指向同一份 PDF，一侧被改动会同时影响另一侧（可在每次会话前校验哈希缓解，但不能隔离）

## 4. 当前是否有独立操作者

**没有。**

- 可用的执行方式只有本会话的 AI 代理，以及 `Task` 工具派生的子代理（`explore`、`general` 等）。
  子代理与主会话是同一模型、同一工作目录，只能做到"上下文不共享"，做不到"不能读答案"。
- 没有第二个真人参与，也没有第二个独立模型实例或独立账号。
- 因此任何由本环境产出的"双会话"都只能写成 **同一操作者、非盲**，
  不能写成独立执行者、盲测或双人交叉。

## 5. 要真正做到隔离，还缺什么

| 缺口 | 需要的条件 |
| --- | --- |
| 执行者独立 | 第二个真人操作员，或另一个与本次会话无关的模型实例 |
| 权限隔离 | 第二 OS 账户 + 对 `reports/*gold*`、`corpus/`、历史日志设 ACL，仅评分者账户可读 |
| 题面与答案分离 | 生成 `questions_only.json`（只有 `task_id`/`question`），`gold.json` 单独存放且执行者不可读 |
| HCS 日志隔离 | 给 `ux_trial_server.py` 加 `--log-root`，两实例各写一棵树 |
| DocFetcher 隔离 | 复制便携版目录（225 MB），各自建索引，索引名不同 |
| 实时记录 | DocFetcher 侧改为实时追加动作 + 定时截图，而不是结束前补写 |
| 可复核 | 录屏或逐动作时间戳日志，配合结束时刻的服务端时间戳 |

## 6. 若暂时接受"非独立"，当前可做的最小隔离

只做到进程/目录/题面释放，明确标注"同一操作者、非盲"：

1. 题面拆成 `questions_only.json`，评分用 `gold.json` 另存。
2. HCS 起两个实例（不同 `--port`），并为每个实例指定独立日志根（需先加参数）。
3. DocFetcher 复制一份便携版，用独立索引目录。
4. 每次会话前校验 A/B 哈希一致。
5. 记录各自 `run_id`/`session_id`，结束时刻由服务端时间戳固定。

这套方案能避免"另一个会话的搜索记录、截图、结果"互相污染，**但不能避免执行者看到答案**。

## 7. 本轮未做

- 未出新题、未运行正式计时、未修改检索算法与页面逻辑
- 未复制 DocFetcher 便携版、未改 `--log-root`、未拆分题面/答案
- 未使用 Administrator 或第二账户（未验证可登录，且切换会中断当前会话）

## 8. 核查证据

| 证据 | 位置 |
| --- | --- |
| 账户与权限 | `whoami` = HC；`icacls .` 输出（Authenticated Users:(M)） |
| 双实例实测 | 8765 与 8768 同时运行，`session_id` 分别为 `s-20261103T152741-3e893c`、`s-20261103T161635-9641f4`，`/api/tasks` 只返回 task_id 与 label |
| 题面释放逻辑 | `scripts/ux_trial_server.py` 的 `/api/tasks`、`/api/start`；`scripts/ux_trial_page.html` 的 `taskPanel` 初始 hidden |
| 答案暴露点 | `reports/timing_trial_questions.json` 的 `groups[].tasks[].reference[].text`；`work/tt_df.py` 读取同一文件 |
| 日志根固定 | `scripts/ux_trial_server.py` 中 `self.log_root = os.path.join(ROOT, "logs", "ux_trial")` |
| DocFetcher 实时性缺陷 | `logs/timing_trial/df-20261103T153954-5418/session.json` 的 actions 时间戳与 `reports/timing_trial_g2t1_timeout_check.md` |
