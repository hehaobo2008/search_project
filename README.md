# HCS 任务A：中文条款切分、定位与引用验证

本目录是华为ICT大赛 HCS 项目的第一阶段工作区。任务A只做公开中文法规的条款切分、原文定位、引用关系确认与版本/故障校验，不做 embedding、OCR、端侧或云部署。

## 数据来源（公开官方入口，2026-11-02 取得）

- A 铁路建设工程质量监督管理规定（2021修正）：交通运输部 HTML 与规范 PDF
- B 建设工程质量管理条例（2019第二次修订）：市场监管总局 HTML；中科院公开 PDF 副本仅作页锚点回跳
- C 修改决定（交通运输部令2021年第35号）：与 A 共页，已分离正文，未重复计入文档数
- 版本反例：A 2015 旧页（标题标注“已被修订”）、B 2017 PDF（首页仅载2017修订）

原始文件、来源 URL、取得时间与 SHA-256 见 `corpus/docs_manifest.json`。

## 从全新克隆复现

```bash
git clone https://github.com/hehaobo2008/search_project.git
cd search_project
python -m venv .venv
# Windows: .venv/Scripts/activate
# Linux/macOS: source .venv/bin/activate
python -m pip install -r requirements.txt

# 1) 获取并校验法规原文与模型权重（逐文件核对 SHA-256）
python scripts/fetch_sources.py --model

# 2) 任务A：生成语料/定位页，运行切分、定位、引用关系与校验
python scripts/run_pipeline.py

# 3) 任务B：模型校验、开发集评测、任务B测试、改写候选校验
python scripts/task_b_pipeline.py

# 4) 全量测试（任务A+B）
python -m unittest discover -s tests -v
```

`fetch_sources.py` 读取 `corpus/docs_manifest.json` 与 `docs/bge-small-zh-v1.5-MODEL_MANIFEST.json`，下载到 `work/` 并逐文件比对 SHA-256；hash 不一致时停止，不静默替换锁定版本。`run_pipeline.py` 使用 `scripts/env_check.py`，把每一步退出码、耗时和日志写入 `logs/runs/<run_id>/`。`task_b_pipeline.py` 使用 `docs/` 中的模型清单，日志写入 `logs/task_b/runs/`。所有排序方法共用同一无答案拒绝规则；模型/索引加载共享，查询耗时不能当作各算法独立的速度成绩。

单独运行测试：

```bash
python -m unittest discover -s tests -v
```

**本轮新克隆验证：未做。** 上一轮 `de5ea74` 已做过本地全新克隆验证（fetch → 任务A → 任务B 均退出 0）；本轮新增的是待复核题目与标注，没有重新跑克隆验证，也未运行新题检索。

## 产物

- `corpus/docs_manifest.json`：文档身份、版本、来源、文件 hash、偏移约定、B31 旧记录与更正原因
- `corpus/articles.jsonl`：A 75 条 + B 82 条的原文、字符区间、锚点、PDF 页、条款 hash（含法规全文，仅本地）
- `corpus/relations.jsonl`：显式文件级、显式条款级、主题相关、修改/重新公布四类关系，含目标版本解析状态
- `corpus/relation_diagnostics.json`：版本歧义或目标缺失的待确认项
- `locators/`：本地原文定位副本、`index.html` 与 `index.json`（`../locators/...#art-N`）
- `reports/task_a_report.md`：自动校验结果
- `reports/task_a_result.json`：逐用例结果与闸门状态
- `reports/locator_result.json`：158 个本地锚点回跳校验
- `reports/version_counterexample_result.json`：真实版本反例结果
- `reports/test_result.json`：流水线内回归测试汇总
- `reports/human_review_checklist_public.md`：H01-H08 公开版核对清单（不含原文全文）
- `reports/RESULTS_taskA_filled.md`：基于交接包模板填写的实际记录
- `reports/evidence_index.md`：证据索引与产物 hash
- `dist/taskA_<run_id>.zip`：复验包（源码、测试、报告、独立运行日志、测试输出；不含法规全文）

## 当前状态

自动链路：16 项自动用例 16 通过、失败 0、已更正记录 1（B31）；真实版本反例 6/6；包内相对链接回跳 158/158；回归测试独立 28/28、流水线内 26/26（1 个测试类按设计跳过）；全部正式步骤退出码 0。

任务A闸门：**未通过（待人工）**。`reports/human_review_checklist_public.md` 中 H01-H08 尚未由人工核对签字。

## 边界与整改

- 独立日志：每次运行写入 `logs/runs/<run_id>/`，公共 `logs/` 只保留最新副本；回归测试验证每份日志存在且非空。
- 失败语义：校验脚本有 FAIL 时返回 2，流水线传播为退出码 1；故意失败负控已验证。
- 原文回跳：本地副本仅注入锚点，不改条文文字；定位链接为相对路径，复制到其他目录仍可打开并跳转，自动验证目标文本一致。
- 版本选择：独立配置 `config/version_pins.json` 显式锁定；正式入口读取该配置，缺失且多版本时停止补证并以退出码 2 报错，不静默任取。
- B31：按实际 PDF 文本层更正为第 7 页；旧记录“续至第 8 页”保留在 `legacy_records`，附修正原因。
- B 官方 HTML 无页码，不编造页码；PDF 页仅用于批准的副本回跳。
- 未调用外部 LLM/API，未安装模型，未上传私有材料，未生成虚构日志、成绩或截图。

## 任务B（开发集端到端，dev_gold_v2）

- 模型：`BAAI/bge-small-zh-v1.5`，ONNX 分发仓库 `Xenova/bge-small-zh-v1.5`（ModelScope），`onnx/model.onnx` 已锁定 SHA-256；许可 MIT。
- 统一入口：`TaskBSystem.answer(question, method)` 只接收自然语言问题与方法名；题型、标准答案、预标条款对只在评分器中读取。
- 对照：纯 BM25、纯语义、混合、混合+≤2 补证，同一输出预算（最多 7 单元、每单元 400 字符、总 2800 字符）。
- 开发集 13 道检索题：纯BM25 13/13 Hit、12/13 全证据；纯语义 12/13；混合 13/13；混合+补证 13/13。补证没有展示出额外收益。
- 无答案 2/2 正确拒绝；版本/引用歧义作为模块测试 3/3，单列不计端到端。
- **不是产品准确率，也不是独立冻结测试。** 20 道同语料改写候选未标注、未运行；F05/F07/F08/F10 与开发题高度重叠，只能作为同语料改写测试。
- 结果：`reports/task_b_dev_report.md`、`reports/RESULTS_taskB_filled.md`；复现入口见上一节。

## 任务B 新题批次 Eval30（已运行首轮对照）

- 30 道新题：10 道模糊岗位描述、10 道多信息需求/跨条款、10 道看似相关但库内无充分答案。
- 题目与标注：`data/task_b_eval30_questions.jsonl`、`reports/task_b_eval30_annotations.md`。
- 标注状态：`revised_after_independent_ai_review`，已于 `reports/task_b_eval30_freeze_manifest.json` 冻结（`frozen_no_retrieval`）；本次由另一 AI 依据锁定原文进行独立复核步骤，**不是人工签字、专家审核或真人盲测**。
- 检索：已按冻结版本完成首轮四方法对照；冻结发生在首次检索之前。首轮结果见 `reports/task_b_eval30_report.md` 与 `reports/task_b_eval30_results.json`。
- 题目家族重叠：`reports/task_b_eval30_overlap.md`；与开发题无共享 gold，N04/N05 与改写候选共享部分条款（为保留正确答案而接受），最大问法相似度 0.4062。
- 复核协议：`reports/task_b_eval30_review_protocol.md`；哈希清单：`reports/task_b_eval30_manifest.json`。
- 现有 20 道同语料改写候选另存于 `data/task_b_rewrite_candidates.jsonl`，未混入本批。
- 首轮结果：展示全证据 BM25 19/20、语义 17/20、混合 19/20、混合+补证 19/20；N11 被统一拒绝规则误拒，N14/N16 在纯语义下漏项。
- 无答案题：10 道中 4 道（N24/N25/N26/N28）被误出证据；补证仅触发 N14，补入 B56 为错误补证，无增益。
- 首轮 run `eval30-first-20261103` 在写出结果后因控制台打印 KeyError 退出 1；首轮 raw 保留，修复仅改打印行后以 `eval30-first-rerun-20261103` 重跑，summary/failures 与首轮一致。详见 `reports/task_b_eval30_run_notes.md`。


## DocFetcher 1.1.27 流程试跑

- 报告：`reports/docfetcher_baseline_trial.md`；机器可读记录：`reports/docfetcher_baseline_trial_queries.json`；截图：`reports/docfetcher_baseline_screens/`。
- 使用官方 Windows 64-bit 便携版，测试目录只放 A、B 两份锁定 PDF，中文索引名 `hcstest`。
- 三个试跑任务均先查完整问题、再查预定关键词；Q1 定位到 A8（第2页），Q2 定位到 A16/A61（第4/18页），Q3 在 A/B 中查找“监测因子”“频次”均 0/0，记为未找到充分依据。
- 中文索引与搜索完成；预览加载第1页并显示高亮，但没有自动跳到目标条款；原文件通过 DocFetcher 双击结果在 Edge 打开并定位。
- 这是流程试跑，不是效果测试；AI 代理操作，不把操作耗时写成人类耗时。

## DocFetcher 与 HCS 三题双流程对照

- 报告：`reports/docfetcher_vs_hcs_trial.md`；HCS 真实前5条：`reports/docfetcher_vs_hcs_trial_hcs.json`；解析差异核对：`reports/docfetcher_vs_hcs_trial_parse_check.json`。
- DocFetcher 使用 PDF；HCS A/B 正文来自官方 HTML，PDF 仅作页锚点；不宣称解析条件完全相同。
- Q1/Q2 HCS 的前5条直接给出 A8、A61/A16 且已实际打开本地回跳；DocFetcher 预览停在第1页，工具栏上一/下一命中禁用、翻页按钮点击无可见变化，最终打开原 PDF 定位。
- Q3 两边均无充分依据：DocFetcher 返回 A/B 相关文件但不是答案；HCS 两轮拒绝。Q3 记为持平/无法判断，不当作 HCS 效果胜出。
- 不计算真人耗时，不宣称独立测试或产品胜出。

## 本机回环页面验证（计时记录）

- 报告：`reports/ux_trial_page_trial.md`；截图：`reports/ux_trial_screens/`；任务1误选更正：`reports/ux_trial_task1_correction.md`。
- 启动：`python scripts/ux_trial_server.py --port 8765`，然后本机打开 `http://127.0.0.1:8765/`。服务强制只监听 `127.0.0.1`，传其它 `--host` 以退出码 2 拒绝。
- 只复用一个检索入口 `TaskBSystem.answer(question, "hybrid_top5")`，自动补证关闭，配置 `cfg-0037f32996f8-hybrid_top5`；页面只接收题面与操作，不读取 gold。
- 模型/索引初始化 `init_ms` 单列，不计入单题计时；单题计时从点击“开始任务”到点击“结束任务并记录”，含读题、输入、搜索、原文核查。
- 结束任务只表示操作者停止，由操作者选“已找到依据 / 未找到 / 中止”，本页不判定答对或证据是否充分。
- 仅用 3 个已见任务验证，不产生效率或准确率结论；日志中的 `duration_ms` 是自动化代理操作耗时，不是真人耗时。
- 已知缺陷：页面滚动后坐标点击会误选证据或点不中结束按钮（任务1 的 `selected_evidence` 因此记错，见更正说明）；任务2 的结束改走 `/api/end` 同一接口。
