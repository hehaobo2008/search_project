# HCS 任务A：中文条款切分、定位与引用验证

本目录是华为ICT大赛 HCS 项目的第一阶段工作区。任务A只做公开中文法规的条款切分、原文定位、引用关系确认与版本/故障校验，不做 embedding、OCR、端侧或云部署。

## 数据来源（公开官方入口，2026-11-02 取得）

- A 铁路建设工程质量监督管理规定（2021修正）：交通运输部 HTML 与规范 PDF
- B 建设工程质量管理条例（2019第二次修订）：市场监管总局 HTML；中科院公开 PDF 副本仅作页锚点回跳
- C 修改决定（交通运输部令2021年第35号）：与 A 共页，已分离正文，未重复计入文档数
- 版本反例：A 2015 旧页（标题标注“已被修订”）、B 2017 PDF（首页仅载2017修订）

原始文件、来源 URL、取得时间与 SHA-256 见 `corpus/docs_manifest.json`。

## 复现

```bash
# 本机实测解释器：python（Python 3.13.2）
python scripts/run_pipeline.py
python scripts/generate_deliverables.py
```

`run_pipeline.py` 依次执行环境检查、语料构建、本地定位页生成、关系抽取、任务A校验、版本反例校验、回跳校验、回归测试、人工清单生成，并把每一步的真实退出码、耗时和日志写入 `logs/runs/<run_id>/` 与 `logs/run_manifest.json`。任一步失败时流水线以非零退出码结束。

单独运行测试：

```bash
python -m unittest discover -s tests -v
```

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
- `reports/human_review_checklist.md`：H01-H08 人工视觉与语义核对清单（含本地回跳链接）
- `reports/RESULTS_taskA_filled.md`：基于交接包模板填写的实际记录
- `reports/evidence_index.md`：证据索引与产物 hash
- `dist/taskA_<run_id>.zip`：复验包（源码、测试、报告、独立运行日志、测试输出；不含法规全文）

## 当前状态

自动链路：16 项自动用例 16 通过、失败 0、已更正记录 1（B31）；真实版本反例 6/6；包内相对链接回跳 158/158；回归测试独立 19/19、流水线内 17/17（1 个测试类按设计跳过）；全部正式步骤退出码 0。

任务A闸门：**未通过（待人工）**。`reports/human_review_checklist.md` 中 H01-H08 尚未由人工核对签字。

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
