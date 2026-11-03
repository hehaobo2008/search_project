# SESSION-D（DocFetcher 执行会话）

- 允许读取：`reports/isolation_test2/exec_scope/`、`work/tools/docfetcher/test_corpus/`
- 允许使用：本机 DocFetcher 进程与索引 `hcstest`
- 不应读取：`reports/isolation_test2/grader_vault_inside/`、`reports/isolation_test2/logs/session_c/`、工作区之外的临时目录
