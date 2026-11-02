# 脱敏运行日志

- 任务A run：`pipeline-20261102T222829`（9 步独立日志 + run_manifest）
- 任务B run：`taskB-20261102T222859`（4 步独立日志 + run_manifest）
- 测试输出：`tests_full.log`、`tests_full_ab.log`

脱敏规则：项目绝对路径替换为 `<PROJECT_ROOT>`；本机解释器路径替换为 `python`；用户目录替换为 `<USER_HOME>`；临时目录与绝对 file 链接替换为 `<TEMP>` / `<LOCAL_PATH>`。时间、退出码、计数、错误内容未修改。

原始日志保留在用户本地，未上传；公共 `logs/` 目录中的最新副本不随仓库分发。