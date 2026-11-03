# 同题试验：两个依次执行的干净会话，隔离边界实测与方案

日期：2026-11-03
基线：commit `8545ecc`
范围：只验证"能否准备两个干净的、彼此不可见的执行会话"，用无关标记测试；
本轮不出正式题、不做正式计时、不改模型或排序。

## 1. 结论（先说做不到的部分）

| 目标 | 实际结果 |
| --- | --- |
| 两个**新上下文**会话 | **可以**：两个 `Task` 子代理都不继承本对话，互不知道对方操作 |
| 会话能用自己的检索工具与 A/B 原文 | **可以**：C 能调 HCS `/api/tasks`、读 A/B；D 能读 DocFetcher 索引与 A/B |
| 会话读不到答案文件 | **做不到**：两个会话都读到了工作区内和工作区外的答案探针 |
| 会话读不到对方操作记录 | **做不到**：C 读到 D 的日志，D 读到 C 的日志 |
| 标准答案不入执行者可读目录 | **当前做不到**：仓库历史里已有答案文件，任何能访问本仓库的会话都能 `git show` 取回 |

**因此不能声称隔离成功。** 本轮只做到"干净上下文"，没有做到"信息隔离"。

## 2. 会话如何创建

- 用 `Task` 工具顺序起两个 `general` 子代理（不能并行），各自全新上下文：
  - SESSION-C（HCS 角色）：`ses_e5f757b59ffejMehFmtYlJURbH`
  - SESSION-D（DocFetcher 角色）：`ses_e5f75089cffee6fYjl7P3pPnEA`
- 每个会话只收到"自己的 brief + 题面文件 + 检查清单"，未给本对话任何内容。
- 测试资料全为无关标记：`reports/isolation_test2/`（`PROBE-T1`、`GRADER-INSIDE-5M3`、
  `C-ACTION-MARK-8H1`、`D-ACTION-MARK-2P6`、`GRADER-OUTSIDE-6R9`）。

## 3. 实测结果

| 检查项 | SESSION-C | SESSION-D |
| --- | --- | --- |
| 继承本对话历史 | 否（明确"无"） | 否 |
| 读自己的题面 `question_only.json` | 成功 | 成功 |
| 读 A_spec.pdf / B_copy_cas.pdf | 成功（304501 / 877965 字节） | 成功（同尺寸） |
| 使用工具 | HCS `/api/tasks` 正常返回 | DocFetcher 索引 `hcstest_1793667951268` 可列 |
| 读 `grader_vault_inside/answer_probe.json` | **成功**（`GRADER-INSIDE-5M3`） | **成功** |
| 读对方 `actions.log` | **成功**（`D-ACTION-MARK-2P6`） | **成功**（`C-ACTION-MARK-8H1`） |
| 读工作区外临时目录答案 | **成功**（`GRADER-OUTSIDE-6R9`） | **成功** |
| 是否知道对方具体操作 | 读过对方日志 | 只读到标记文本 |

原始回答：`reports/isolation_test2/session_c_report.md`、`session_d_report.md`。

## 4. 为什么当前环境做不到信息隔离

1. **工具无路径限制**：`read`/shell 对 `grader_vault_inside/`、`logs/session_d/`、
   以及工作区外的 `%TEMP%` 路径都直接返回内容，没有任何拒绝。
   brief 里的"不应读取"只是文本约束；C 与 D 都如实违反并读到了。
2. **同一 OS 账户**：`whoami` = `HC`，且 `HC` 属于 `Administrators`。
   即使给答案目录设 NTFS ACL 拒绝 `HC`，`HC` 也能自行改回权限，等于无效。
3. **同一工作区 + 同一模型**：两个会话共享文件系统；模型相同不影响上下文隔离，
   但也不提供任何信息屏障。
4. **仓库历史已含答案**：`reports/timing_trial_questions.json` 从 commit `5d60f0b` 起就在历史里，
   含 `groups[].tasks[].reference[].text`（答案全文）。任何能访问本仓库的会话都能 `git show` 取回，
   即使从工作树删除也不解决问题。

## 5. 答案应由谁、在什么环境保管

**保管人**：不是执行会话，也不是执行会话所在的 AI 进程，而是**评分者本人（真人）**，
或竞赛负责人指定的独立评分账户。

**环境（按可行性排序）**：

| 方案 | 做法 | 可行性 |
| --- | --- | --- |
| A. 另一台机器 | 答案只放在评分者自己的电脑，执行会话在另一台机器跑工具 | 最可行，但需第二台设备 |
| B. 同机第二账户 | 新建非管理员账户 `executor`（跑工具）与 `grader`（存答案）；`grader` 目录 ACL 仅授予 `grader`；执行会话在 `executor` 桌面运行 | 可行，需用户手动建账户并切换桌面 |
| C. 加密文件 + 人工解密 | 答案用评分者掌握的密码加密，密文可留在仓库外；执行会话即使读到也无法解密 | 可行，但必须在执行结束后由评分者解密评分 |
| D. 现在这个共享工作区 | 做不到 | **不采用** |

**只给执行会话题面和必要资料的做法**：

1. 评分者在执行前生成 `questions_only.json`，只含 `task_id` 与 `question`，不放 `reference`。
2. 给执行会话一个**不含 `reports/`、`logs/`、`.git` 的干净副本**：只保留
   `scripts/`（工具）、`corpus/` 或 `work/raw/A_spec.pdf`+`B_copy_cas.pdf`、`config/`。
3. `corpus/` 与 A/B 原文属于"必要资料"，可以给；**答案标注文件一律不给**。
4. 执行结束后，评分者在自己的环境用答案文件逐题核对。

当前仓库需要拆分：现有 `reports/timing_trial_questions.json` 同时含题面与答案，
不能直接交给执行会话使用。

## 6. 正式测试的顺序与环境记录计划（本轮不执行）

**顺序约束**：第一场完全结束并写入 `ended_at` 后，才启动第二场；两场不并行。

**每场需要记录**：

| 项 | 采集方式 |
| --- | --- |
| 场次与工具 | `HCS` / `DocFetcher`，场次编号 |
| 机器配置 | i9-13900HX（24C/32T）、16 GB、Windows 11 家庭版 10.0.26200（已采集，见 §7） |
| 背景负载 | 开始前记录：进程数、空闲内存、CPU 占用 |
| 模型/索引状态 | HCS 记 `init_ms` 与是否首查（预热）；DocFetcher 记应用启动时刻、索引是否已建 |
| 起止时间 | 题面显示时刻（客户端）与服务端收到结束时刻 |
| 结束状态 | 找到 / 未找到 / 中止，及所选依据 |

**两工具环境尽量一致**：同一机器、同一时段、同一显示器分辨率、都关闭注入延时与刷新；
开始前各做一次"空转预热查询"以对齐热态，但预热时间**不计入单题**。

**无法控制的差异（必须写进正式报告）**：

- HCS 模型常驻内存、首查有预热；DocFetcher 是 JVM + Lucene 索引，启动与建索引是另一套成本。
- HCS 检索 HTML 正文、DocFetcher 索引 PDF 文本层，解析条件不同。
- DocFetcher 预览无法导航到命中页，需要外部 PDF 核对；HCS 有 locator 回跳。
- 图形界面渲染、OCR 核对与坐标点击耗时不可比。
- 同一 AI 模型、非真人，操作速度受工具调用节奏影响。

## 7. 环境快照（采集时间 2026-11-03，仅记录，不作为计时）

| 项 | 值 |
| --- | --- |
| CPU | 13th Gen Intel Core i9-13900HX，24 核 / 32 逻辑处理器 |
| 内存 | 16 GB（WMI TotalPhysicalMemory 约 15.7 GiB） |
| OS | Microsoft Windows 11 家庭版 中文版，`10.0.26200` |
| 机型 | COLORFUL G16 Pro |
| 当前背景负载 | 空闲内存 885 MB、进程 407 个、CPU 占用 40% |
| 账户 | `HC`，属于 `Administrators` |
| 同时运行 | HCS 服务（8765）、DocFetcher（PID 26512）、多个 python/Edge 进程 |

背景负载偏高（空闲内存不足 1 GB），正式计时前应关闭无关进程并重测。

## 8. 本轮未做

- 未出正式题、未运行正式计时、未改检索算法或排序参数
- 未创建 Windows 第二账户、未设置 ACL、未加密答案
- 未把现有 `reports/timing_trial_questions.json` 拆分或移出仓库（会改动已提交内容）
- 未在 IDE 界面新建人工会话（该操作需用户手动完成）

## 9. 证据

| 证据 | 位置 |
| --- | --- |
| 测试资料与标记 | `reports/isolation_test2/` |
| SESSION-C 原始回答 | `reports/isolation_test2/session_c_report.md` |
| SESSION-D 原始回答 | `reports/isolation_test2/session_d_report.md` |
| 会话 ID | C `ses_e5f757b59ffejMehFmtYlJURbH`；D `ses_e5f75089cffee6fYjl7P3pPnEA` |
| 答案已入历史 | `git log --oneline -- reports/timing_trial_questions.json` → `5d60f0b` |
