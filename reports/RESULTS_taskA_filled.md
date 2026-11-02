# 任务A 验收整改后实际运行记录

> 本文件由真实运行产物生成；原空白模板 `HCS_CODEARTS_HANDOFF_20261102/HCS_CODEARTS_HANDOFF_20261102/RESULTS_TEMPLATE.md` 保持未改。
> 本轮按复验意见整改：独立日志落盘、失败退出码、本地原文回跳、多版本歧义、B31页码更正、回归测试与打包。

## 一次运行身份

- 流水线 run_id：pipeline-20261102T222829
- 任务A 校验 run_id：taskA-20261102T222831
- 运行日志目录：`logs/runs/pipeline-20261102T222829/`（每步独立日志与 run_manifest.json）
- 任务与状态：任务A / 自动链路、回跳验证、回归测试已运行；人工闸门待核验
- CodeArts 平台与项目：当前 CodeArts Agent 会话，项目 `search_project`（截图 E01 待采集）
- 实际开始/结束时间及UTC偏移：2026-11-02T22:28:29.271540+08:00 至 2026-11-02T22:28:37.903248+08:00（UTC+08:00）
- 操作者与人工复核者：操作者为本次会话用户；人工复核者待填
- 授权记录：会话内用户指令“完成第一阶段”“先完成任务A的验收整改”及交接包 `FIRST_SESSION_PROMPT.txt`
- 运行时/操作系统/可见CPU及内存：Python 3.13.2；Windows-11-10.0.26200-SP0；AMD64；32 逻辑CPU；内存未测
- 依赖版本、许可证、锁文件hash：pypdf 6.21.1、lxml 6.1.3；许可证与锁文件未建立（待补）
- 模型仓库/revision/文件hash/许可：任务A不适用
- 语料manifest hash：`28d704ebef95fede1feb0f57a35dc4033cc43d280f79b8383494c56ef9c30a04`
- 条款表 hash：`55b600c53a33d2e7b4398d9094ebdc2f40bbc33c628921e6c102a57d55b04a3d`；关系表 hash：`3c66869a25e1217e1e426d55d2c9492ee39fb16d4324a7d36dca5d52f15b6619`
- 问题集/gold hash：任务A不适用；任务B见 `config/task_b_config.json` 与 `data/task_b_dev_questions.jsonl`
- 前置commit / 结果commit / diff位置：本项目未初始化 Git，无 commit；改动即 `scripts/`、`tests/`、`corpus/`、`locators/`、`reports/`
- 实际命令、退出码、原日志位置：见下方命令表；汇总 `logs/run_manifest.json`
- 会话历史位置、截图编号：会话历史在本平台；E01/E03/E04 截图待采集
- 失败重跑关联：本轮无自动失败；负控失败测试见“退出码与失败传播”

## 实际命令与退出码

1. `<LOCAL_PATH> scripts/env_check.py` → exit=0，0.679s，日志 `logs/runs/pipeline-20261102T222829/env_check.log`（590 bytes）
2. `<LOCAL_PATH> scripts/build_corpus.py` → exit=0，0.902s，日志 `logs/runs/pipeline-20261102T222829/build_corpus.log`（287 bytes）
3. `<LOCAL_PATH> scripts/build_locators.py` → exit=0，0.404s，日志 `logs/runs/pipeline-20261102T222829/build_locators.log`（42 bytes）
4. `<LOCAL_PATH> scripts/build_relations.py` → exit=0，0.402s，日志 `logs/runs/pipeline-20261102T222829/build_relations.log`（2148 bytes）
5. `<LOCAL_PATH> scripts/verify_task_a.py` → exit=0，0.156s，日志 `logs/runs/pipeline-20261102T222829/verify_task_a.log`（1725 bytes）
6. `<LOCAL_PATH> scripts/verify_counterexamples.py` → exit=0，0.750s，日志 `logs/runs/pipeline-20261102T222829/verify_counterexamples.log`（1532 bytes）
7. `<LOCAL_PATH> scripts/verify_locators.py` → exit=0，0.164s，日志 `logs/runs/pipeline-20261102T222829/verify_locators.log`（549 bytes）
8. `<LOCAL_PATH> scripts/run_tests.py` → exit=0，5.039s，日志 `logs/runs/pipeline-20261102T222829/run_tests.log`（3905 bytes）
9. `<LOCAL_PATH> scripts/generate_review_checklist.py` → exit=0，0.124s，日志 `logs/runs/pipeline-20261102T222829/generate_review_checklist.log`（43 bytes）

## 退出码与失败传播（本轮整改）

- `verify_task_a.py`、`verify_counterexamples.py`、`verify_locators.py`、`run_tests.py` 在存在 FAIL/失败用例时返回退出码 `2`，不再“记录 FAIL 但返回 0”。
- `run_pipeline.py` 按每一步真实退出码汇总；任一非零即 `all_passed=false`、`failed_steps` 非空，并以退出码 `1` 结束。
- 故意失败负控：`HCS_EXTRA_FAILING_STEP=1` 时追加一个 `sys.exit(7)` 步骤。`tests/test_pipeline_logs.py::test_intentional_failure_makes_pipeline_fail` 已实际运行通过，验证流水线返回非零且 `failed_steps=['negative_control']`。
- 完整测试输出见 `logs/tests_full.log`；流水线内测试输出见 `logs/runs/pipeline-20261102T222829/run_tests.log`。

## 任务A 自动用例

| 用例ID | 名称 | 状态 | 实际结果 |
|---|---|---|---|
| T01 | 文档身份与共页分离 | PASS | documents=3 distinct_source_files=2 shared_page=True |
| T02 | A/B 条号连续且边界完整 | PASS | A=1..75(75条) B=1..82(82条) |
| T03 | 原文偏移回跳与哈希 | PASS | span_fail=0 hash_fail=0 pdf_page_missing=0 |
| T04 | A第2条范围条款 | PASS | ok pdf_page=1 |
| T05 | A第30条检测/取样/签认 | PASS | status=ok keywords=['试块', '监督', '专人签字', '签认'] paras=2 pdf_page=9 |
| T06 | A66→B65 显式条款引用与正确版本 | PASS | status=ok edges=1 target=第六十五条 version=revised_2019_04_23 |
| T07 | B29/B31/B65 原文与页锚点 | PASS | B29 p7 B31 p7 B65 p16 |
| T07b | B31按实际PDF第7页更正并保留旧记录 | PASS | page=7 cross=False legacy=superseded correction=corrected |
| T08 | C修改与重新公布关系 | PASS | amendment=3 targets=['None', '第七十条', '第六十九条'] C_articles=0 |
| T09 | 负例：A30与B29/B31仅主题相关 | PASS | explicit_edges=0 topic_edges=2 |
| T10 | 负例：A1→B 仅文件级不生成条款边 | PASS | A1文件级B边=1 A1条款级边=0 |
| T11 | 显式关系目标无悬空边 | PASS | dangling=0 [] |
| T12 | 版本守卫：2017副本不得静默替代2019 | PASS | status=version_pending available=['revised_2017_10_07'] |
| T13 | 故障用例：缺条/重复/缺版本/错位 | PASS | missing=article_not_found duplicate=ambiguous_article no_version=version_unknown tampered=locator_mismatch |
| T14 | 主题相关与显式引用隔离 | PASS | topic_related=2 |
| T15 | C与A共页去重 | PASS | C_indexed_articles=0 C_edges=3 |

## 版本反例（真实文件）

| 用例ID | 名称 | 状态 | 实际结果 |
|---|---|---|---|
| V01 | A2015旧页明确标注已被修订 | PASS | title=铁路建设工程质量监督管理规定（中华人民共和国交通运输部令2015年第2号）（已被修订）-政府信息公开-交通运输部 |
| V02 | A条号在2015与2021版间发生位移 | PASS | A2015#70==A2021#70? False; A2015#70==A2021#71? True; a2015_70_len=77 |
| V03 | B2017副本首页仅载2017修订 | PASS | first_page_head=-1-建设工程质量管理条例(2000年1月30日中华人民共和国国务院令第279号发布根据2017年10月7日《国务院关于修改部分行政法规的决定》修订)第一章总则 |
| V04 | B2017第65条文本层可读且去页码后对比 | PASS | B2017_len=147 B2019_len=137 去页码后相同=True |
| V05 | 真实2017语料下请求2019版第65条必须待核验 | PASS | status=version_pending available=['revised_2017_10_07'] |
| V06 | 真实2015语料存在第70条且与2021版内容不同 | PASS | 2015_len=77 2021_len=146 |

## 本地原文回跳（本轮整改）

- 方式：`scripts/build_locators.py` 从官方公开 HTML 生成本地副本，向对应条款元素注入 `id=art-N`，保留条文文字不变；本地副本与索引位于 `locators/`，链接一律为相对路径，复制到其他目录后仍可定位。
- 验证：`scripts/verify_locators.py` 解析本地 HTML，按 `id` 与 `data-article-part` 收集目标元素，比对 `corpus/articles.jsonl` 原文；结果 `158/158` 通过。
- 关键项：
  - `rail_quality:art-2`：PASS；rail_quality.locator.html#art-2
  - `rail_quality:art-30`：PASS；rail_quality.locator.html#art-30
  - `rail_quality:art-66`：PASS；rail_quality.locator.html#art-66
  - `construction_quality:art-29`：PASS；construction_quality.locator.html#art-29
  - `construction_quality:art-31`：PASS；construction_quality.locator.html#art-31
  - `construction_quality:art-65`：PASS；construction_quality.locator.html#art-65
  - `rail_quality_amendment:decision`：PASS；rail_quality_amendment.locator.html#decision
- 说明：`../locators/...#art-N` 为包内相对链接，复制到其他目录后仍可打开并滚动到对应元素；自动测试验证锚点唯一、目标文本一致，视觉确认仍列入 H01-H07。

## 版本选择策略（本轮整改）

- 引用目标版本由独立配置 `config/version_pins.json` 显式锁定；`build_relations.py` 正式入口读取该配置，不再从 `docs_manifest.json` 的文档列表推导版本，也不会从版本集合任取。
- 配置缺失或未覆盖某目标文档且该文档存在多版本时，关系记录 `target_version_status=ambiguous_version`，不生成补证边，写入 `corpus/relation_diagnostics.json`，CLI 以退出码 2 停止；锁定版本不存在时标 `pinned_version_missing`。
- 本轮正式语料版本状态分布：external=7，pinned=2，resolved=18。
- 回归：`tests/test_version_selection.py` 验证解析函数；`tests/test_relation_cli.py` 实际调用命令行入口，交换 2017/2019 两个版本的排列顺序，验证无配置→歧义停边且退出码2、有配置→两种顺序都只选2019。

## B31 页码更正（本轮整改）

- 旧记录：`B29及B31在物理第7页、B31续至第8页`（来源：HCS_CODEARTS_HANDOFF_20261102/MATERIALS_MANIFEST.md（2026-11-02整理），状态：superseded）。
- 实际观察：CAS副本PDF文本层第7页完整包含B31句尾‘进行检测。’；第8页首条为B32。
- 更正后：B31 `pdf_page_start=7`、`pdf_cross_page=False`；第8页首条为B32。
- 修正原因：按实际PDF文本层逐页核对，B31未跨页；保留旧记录与修正原因供复验追溯，旧记录不再作为事实使用。
- 旧记录仍保留在 `corpus/docs_manifest.json` 的 `legacy_records`，articles 中保留 `page_record_correction`，可追溯，不删除。

## 回归测试（本轮整改）

- 独立完整运行：28 项，通过 28，失败/错误 0（`logs/tests_full.log`、`reports/test_result_full.json`）。
- 流水线内运行：26 项，通过 26，跳过测试类 1 个、跳过测试用例 0 个，失败/错误 0（跳过的是嵌套流水线测试类，避免递归；`logs/runs/pipeline-20261102T222829/run_tests.log`）。
- 覆盖：独立日志落盘、失败退出码与流水线失败传播、故意失败负控、本地锚点回跳、版本多版本歧义、B31 更正、语料完整性、关系负例。

## 汇总

- 计划用例：自动 16 + 版本反例 6 + 人工 8 = 30
- 已运行：22（自动 16 + 版本反例 6）
- 通过：22（自动 16 + 版本反例 6）
- 失败：0（自动 0 + 版本反例 0）
- 已更正记录：1（B31 页位）
- 待人工核验：8
- 回归测试：独立 28/28；流水线内 26/26（1 个测试类按设计跳过）
- 未运行：0（任务A）；任务B开发集已运行，需区分
- 关键缺陷是否为0：待人工确认后填写
- 闸门结论：NOT_PASSED_PENDING_HUMAN_REVIEW（自动用例、回跳与回归测试不等同人工复核）

## 人工核对待办

- [ ] H01 A第2条与交通运输部规范PDF物理第1页的视觉一致性
- [ ] H02 A第30条与规范PDF物理第9页的视觉一致性（两款完整、签字主体与签认对象不混同）
- [ ] H03 A第66条与规范PDF物理第22页的视觉一致性（显式引用措辞）
- [ ] H04 B第29条与中科院副本PDF物理第7页的视觉一致性
- [ ] H05 B第31条位置：自动文本层仅第7页，清单记录为续至第8页，冲突待视觉确认
- [ ] H06 B第65条与中科院副本PDF物理第16页的视觉一致性
- [ ] H07 C修改决定全文：修改第69条、增设第70条、条文序号调整与重新公布
- [ ] H08 引用四分法语义复核：A1→B文件级、A30与B29/B31主题相关、A66→B65显式、C→A修改

## 失败与观察

| failure_id | 用例 | 首次现象 | 原日志 | 原因是否确认 | 修复 | 重跑run_id | 仍未解决 |
|---|---|---|---|---|---|---|---|
| O01 | B31页位 | 旧记录称B31续至第8页 | `logs/pdf_page_detail.log` | 是（PDF文本层第7页含条尾，第8页首条B32） | 更正为第7页并保留旧记录 | pipeline-20261102T222829 | 否（待人工视觉确认） |
| O02 | V04 | 2017版PDF第65条文本层混入页码`- 17 -` | `logs/b2017_65.txt` | 是（PDF页码噪声） | 比较时去页码 | 已重跑 | 仅作反例，不用于主索引 |
| O03 | 日志路径 | 报告指向独立目录但日志缺失 | 旧日志目录 | 是（只写公共目录） | 每步双写独立目录与公共目录，并纳入回归测试 | pipeline-20261102T222829 | 否 |

## 本次实际完成与可主张范围

**实际完成：** 取得 A/B/C 三份官方材料与两份真实版本反例；完成 A 75 条、B 82 条切分、偏移、HTML 锚点、PDF 页文本层锚点与 SHA-256；完成四类关系表（库内文件级 1、库外书名 7、显式条款级 14、主题相关 2、修改/重新公布 3）；完成 158 个本地锚点回跳验证、16 项自动校验、6 项真实版本反例、28 项独立回归测试与故意失败负控；所有正式流水线步骤退出码 0。

**仍未完成：** H01-H08 人工视觉与语义复核、平台截图采集（E01/E03/E04）、Git commit、任务B同语料改写测试与人工冻结。

**适用范围：** 本批最小公开语料（A/B/C）与工程链路；不代表中文检索效果、法律结论、领域泛化或手机端性能。自动用例通过不等于任务A闸门通过。