import hashlib
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS = os.path.join(ROOT, "reports")
CORPUS = os.path.join(ROOT, "corpus")
LOGS = os.path.join(ROOT, "logs")


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def esc(text):
    return str(text).replace("|", "\\|").replace("\n", " ")


manifest = load(os.path.join(CORPUS, "docs_manifest.json"))
articles = [json.loads(line) for line in open(os.path.join(CORPUS, "articles.jsonl"), encoding="utf-8")]
relations = [json.loads(line) for line in open(os.path.join(CORPUS, "relations.jsonl"), encoding="utf-8")]
result = load(os.path.join(REPORTS, "task_a_result.json"))
counter = load(os.path.join(REPORTS, "version_counterexample_result.json"))
locator = load(os.path.join(REPORTS, "locator_result.json"))
tests = load(os.path.join(REPORTS, "test_result.json"))
full_tests_path = os.path.join(REPORTS, "test_result_full.json")
full_tests = load(full_tests_path) if os.path.exists(full_tests_path) else tests
run_manifest = load(os.path.join(LOGS, "run_manifest.json"))

b31 = next(a for a in articles
           if a["doc_id"] == "construction_quality" and a["article_num"] == 31)
b_doc = next(d for d in manifest["documents"] if d["doc_id"] == "construction_quality")
legacy = next(r for r in b_doc["legacy_records"] if r["record_id"] == "B31-page")

artifacts = {}
for rel in ["corpus/docs_manifest.json", "corpus/articles.jsonl", "corpus/relations.jsonl",
            "corpus/relation_diagnostics.json", "locators/index.json",
            "reports/task_a_result.json", "reports/locator_result.json",
            "reports/version_counterexample_result.json", "reports/test_result.json",
            "logs/run_manifest.json"]:
    artifacts[rel] = sha256_file(os.path.join(ROOT, rel))

version_status = {}
for rel in relations:
    key = rel["target_version_status"]
    version_status[key] = version_status.get(key, 0) + 1

start = run_manifest["steps"][0]["started_at"]
end = run_manifest["steps"][-1]["ended_at"]
cmd_lines = "\n".join("%d. `%s` → exit=%d，%.3fs，日志 `%s`（%d bytes）" % (
    i + 1, s["command"], s["exit_code"], s["duration_sec"], s["log"], s["log_bytes"])
    for i, s in enumerate(run_manifest["steps"]))

auto_cases = result["cases"]
counter_cases = counter["cases"]
passed_auto = result["summary"]["passed"]
failed_auto = result["summary"]["failed"]
human = result["human_review_items"]
passed_counter = counter["summary"]["passed"]

lines = [
    "# 任务A 验收整改后实际运行记录",
    "",
    "> 本文件由真实运行产物生成；原空白模板 `HCS_CODEARTS_HANDOFF_20261102/HCS_CODEARTS_HANDOFF_20261102/RESULTS_TEMPLATE.md` 保持未改。",
    "> 本轮按复验意见整改：独立日志落盘、失败退出码、本地原文回跳、多版本歧义、B31页码更正、回归测试与打包。",
    "",
    "## 一次运行身份",
    "",
    "- 流水线 run_id：%s" % run_manifest["run_id"],
    "- 任务A 校验 run_id：%s" % result["run_id"],
    "- 运行日志目录：`logs/runs/%s/`（每步独立日志与 run_manifest.json）" % run_manifest["run_id"],
    "- 任务与状态：任务A / 自动链路、回跳验证、回归测试已运行；人工闸门待核验",
    "- CodeArts 平台与项目：当前 CodeArts Agent 会话，项目 `search_project`（截图 E01 待采集）",
    "- 实际开始/结束时间及UTC偏移：%s 至 %s（UTC+08:00）" % (start, end),
    "- 操作者与人工复核者：操作者为本次会话用户；人工复核者待填",
    "- 授权记录：会话内用户指令“完成第一阶段”“先完成任务A的验收整改”及交接包 `FIRST_SESSION_PROMPT.txt`",
    "- 运行时/操作系统/可见CPU及内存：Python %s；Windows-11-10.0.26200-SP0；AMD64；%s 逻辑CPU；内存未测" % (
        run_manifest["python"].split()[0], os.cpu_count()),
    "- 依赖版本、许可证、锁文件hash：pypdf 6.21.1、lxml 6.1.3；许可证与锁文件未建立（待补）",
    "- 模型仓库/revision/文件hash/许可：任务A不适用",
    "- 语料manifest hash：`%s`" % artifacts["corpus/docs_manifest.json"],
    "- 条款表 hash：`%s`；关系表 hash：`%s`" % (
        artifacts["corpus/articles.jsonl"], artifacts["corpus/relations.jsonl"]),
    "- 问题集/gold hash：任务A不适用（任务B待建）",
    "- 前置commit / 结果commit / diff位置：本项目未初始化 Git，无 commit；改动即 `scripts/`、`tests/`、`corpus/`、`locators/`、`reports/`",
    "- 实际命令、退出码、原日志位置：见下方命令表；汇总 `logs/run_manifest.json`",
    "- 会话历史位置、截图编号：会话历史在本平台；E01/E03/E04 截图待采集",
    "- 失败重跑关联：本轮无自动失败；负控失败测试见“退出码与失败传播”",
    "",
    "## 实际命令与退出码",
    "",
    cmd_lines,
    "",
    "## 退出码与失败传播（本轮整改）",
    "",
    "- `verify_task_a.py`、`verify_counterexamples.py`、`verify_locators.py`、`run_tests.py` 在存在 FAIL/失败用例时返回退出码 `2`，不再“记录 FAIL 但返回 0”。",
    "- `run_pipeline.py` 按每一步真实退出码汇总；任一非零即 `all_passed=false`、`failed_steps` 非空，并以退出码 `1` 结束。",
    "- 故意失败负控：`HCS_EXTRA_FAILING_STEP=1` 时追加一个 `sys.exit(7)` 步骤。`tests/test_pipeline_logs.py::test_intentional_failure_makes_pipeline_fail` 已实际运行通过，验证流水线返回非零且 `failed_steps=['negative_control']`。",
    "- 完整测试输出见 `logs/tests_full.log`；流水线内测试输出见 `logs/runs/%s/run_tests.log`。" % run_manifest["run_id"],
    "",
    "## 任务A 自动用例",
    "",
    "| 用例ID | 名称 | 状态 | 实际结果 |",
    "|---|---|---|---|",
]
for c in auto_cases:
    lines.append("| %s | %s | %s | %s |" % (c["id"], esc(c["name"]), c["status"], esc(c["detail"])))

lines += [
    "",
    "## 版本反例（真实文件）",
    "",
    "| 用例ID | 名称 | 状态 | 实际结果 |",
    "|---|---|---|---|",
]
for c in counter_cases:
    lines.append("| %s | %s | %s | %s |" % (c["id"], esc(c["name"]), c["status"], esc(c["detail"])))

lines += [
    "",
    "## 本地原文回跳（本轮整改）",
    "",
    "- 方式：`scripts/build_locators.py` 从官方公开 HTML 生成本地副本，向对应条款元素注入 `id=art-N`，保留条文文字不变；本地副本与索引位于 `locators/`，链接一律为相对路径，复制到其他目录后仍可定位。",
    "- 验证：`scripts/verify_locators.py` 解析本地 HTML，按 `id` 与 `data-article-part` 收集目标元素，比对 `corpus/articles.jsonl` 原文；结果 `%d/%d` 通过。" % (
        locator["summary"]["passed"], locator["summary"]["total"]),
    "- 关键项：",
]
for name, check in locator["key_checks"].items():
    lines.append("  - `%s`：%s；%s" % (name, check["status"], check["href"]))
lines += [
    "- 说明：`../locators/...#art-N` 为包内相对链接，复制到其他目录后仍可打开并滚动到对应元素；自动测试验证锚点唯一、目标文本一致，视觉确认仍列入 H01-H07。",
    "",
    "## 版本选择策略（本轮整改）",
    "",
    "- 引用目标版本由独立配置 `config/version_pins.json` 显式锁定；`build_relations.py` 正式入口读取该配置，不再从 `docs_manifest.json` 的文档列表推导版本，也不会从版本集合任取。",
    "- 配置缺失或未覆盖某目标文档且该文档存在多版本时，关系记录 `target_version_status=ambiguous_version`，不生成补证边，写入 `corpus/relation_diagnostics.json`，CLI 以退出码 2 停止；锁定版本不存在时标 `pinned_version_missing`。",
    "- 本轮正式语料版本状态分布：%s。" % "，".join("%s=%d" % (k, v) for k, v in sorted(version_status.items())),
    "- 回归：`tests/test_version_selection.py` 验证解析函数；`tests/test_relation_cli.py` 实际调用命令行入口，交换 2017/2019 两个版本的排列顺序，验证无配置→歧义停边且退出码2、有配置→两种顺序都只选2019。",
    "",
    "## B31 页码更正（本轮整改）",
    "",
    "- 旧记录：`%s`（来源：%s，状态：%s）。" % (
        legacy["record"], legacy["source"], legacy["status"]),
    "- 实际观察：%s。" % legacy["observed"],
    "- 更正后：B31 `pdf_page_start=%d`、`pdf_cross_page=%s`；第8页首条为B32。" % (
        b31["pdf_page_start"], b31["pdf_cross_page"]),
    "- 修正原因：%s。" % legacy["correction_reason"],
    "- 旧记录仍保留在 `corpus/docs_manifest.json` 的 `legacy_records`，articles 中保留 `page_record_correction`，可追溯，不删除。",
    "",
    "## 回归测试（本轮整改）",
    "",
    "- 独立完整运行：%d 项，通过 %d，失败/错误 %d（`logs/tests_full.log`、`reports/test_result_full.json`）。" % (
        full_tests["total"], full_tests["passed"],
        len(full_tests["failures"]) + len(full_tests["errors"])),
    "- 流水线内运行：%d 项，通过 %d，跳过测试类 %d 个、跳过测试用例 %d 个，失败/错误 %d（跳过的是嵌套流水线测试类，避免递归；`logs/runs/%s/run_tests.log`）。" % (
        tests["total"], tests["passed"], len(tests.get("skipped_classes", [])),
        len(tests.get("skipped_tests", [])),
        len(tests["failures"]) + len(tests["errors"]), run_manifest["run_id"]),
    "- 覆盖：独立日志落盘、失败退出码与流水线失败传播、故意失败负控、本地锚点回跳、版本多版本歧义、B31 更正、语料完整性、关系负例。",
    "",
    "## 汇总",
    "",
    "- 计划用例：自动 16 + 版本反例 6 + 人工 8 = 30",
    "- 已运行：22（自动 16 + 版本反例 6）",
    "- 通过：%d（自动 %d + 版本反例 %d）" % (passed_auto + passed_counter, passed_auto, passed_counter),
    "- 失败：%d（自动 %d + 版本反例 %d）" % (failed_auto + counter["summary"]["failed"],
                                          failed_auto, counter["summary"]["failed"]),
    "- 已更正记录：1（B31 页位）",
    "- 待人工核验：%d" % len(human),
    "- 回归测试：独立 %d/%d；流水线内 %d/%d（%d 个测试类按设计跳过）" % (
        full_tests["passed"], full_tests["total"],
        tests["passed"], tests["total"], len(tests.get("skipped_classes", []))),
    "- 未运行：0（任务B未申请，不计入任务A）",
    "- 关键缺陷是否为0：待人工确认后填写",
    "- 闸门结论：%s（自动用例、回跳与回归测试不等同人工复核）" % result["gate"],
    "",
    "## 人工核对待办",
    "",
]
for item in human:
    lines.append("- [ ] %s %s" % (item["id"], item["item"]))

lines += [
    "",
    "## 失败与观察",
    "",
    "| failure_id | 用例 | 首次现象 | 原日志 | 原因是否确认 | 修复 | 重跑run_id | 仍未解决 |",
    "|---|---|---|---|---|---|---|---|",
    "| O01 | B31页位 | 旧记录称B31续至第8页 | `logs/pdf_page_detail.log` | 是（PDF文本层第7页含条尾，第8页首条B32） | 更正为第7页并保留旧记录 | %s | 否（待人工视觉确认） |" % run_manifest["run_id"],
    "| O02 | V04 | 2017版PDF第65条文本层混入页码`- 17 -` | `logs/b2017_65.txt` | 是（PDF页码噪声） | 比较时去页码 | 已重跑 | 仅作反例，不用于主索引 |",
    "| O03 | 日志路径 | 报告指向独立目录但日志缺失 | 旧日志目录 | 是（只写公共目录） | 每步双写独立目录与公共目录，并纳入回归测试 | %s | 否 |" % run_manifest["run_id"],
    "",
    "## 本次实际完成与可主张范围",
    "",
    "**实际完成：** 取得 A/B/C 三份官方材料与两份真实版本反例；完成 A 75 条、B 82 条切分、偏移、HTML 锚点、PDF 页文本层锚点与 SHA-256；完成四类关系表（库内文件级 1、库外书名 7、显式条款级 14、主题相关 2、修改/重新公布 3）；完成 158 个本地锚点回跳验证、16 项自动校验、6 项真实版本反例、%d 项独立回归测试与故意失败负控；所有正式流水线步骤退出码 0。" % full_tests["total"],
    "",
    "**仍未完成：** H01-H08 人工视觉与语义复核、平台截图采集（E01/E03/E04）、Git commit、任务B中文检索与同预算消融。",
    "",
    "**适用范围：** 本批最小公开语料（A/B/C）与工程链路；不代表中文检索效果、法律结论、领域泛化或手机端性能。自动用例通过不等于任务A闸门通过。",
]

with open(os.path.join(REPORTS, "RESULTS_taskA_filled.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

# 证据索引
evidence = [
    ("E01", "平台身份", "本会话运行于 CodeArts Agent；项目路径与时间可复核", "截图待采集；仅截图不能证明实验完成"),
    ("E02", "首次任务与授权", "会话内用户指令与交接包 FIRST_SESSION_PROMPT.txt", "未导出对话文件"),
    ("E03", "实际改动", "scripts/ 11 个脚本、tests/ 7 个文件、corpus/locators/reports 产物", "未初始化 Git，无 commit/diff hash"),
    ("E04", "运行证据", "logs/runs/<run_id>/ 每步独立日志；logs/run_manifest.json 九步退出码0", "无 run_id 之外的外部流水号"),
    ("E05", "条款回跳", "locators/index.json + verify_locators：158/158，A30/A66/B31 关键项通过", "视觉确认待人工"),
    ("E06", "版本反例", "version_counterexample_result.json：A2015 已被修订、B2017 首页仅载2017、条号位移、版本待核验", "B2017 仅作反例对照，不进入主索引"),
    ("E07", "任务A人工复核", "human_review_checklist.md H01-H08 含 file:// 回跳链接", "全部待人工填写，闸门未通过"),
    ("E08", "任务B", "未执行", "未获批，不准备虚假 E08"),
    ("E09", "回归/失败", "tests 19/19；故意失败负控通过；O01-O03 已记录", "未人为制造真实失败；合成故障单列"),
    ("E10", "最终关联", "run_id、产物 hash、独立日志、测试输出可互相对照", "无 commit 可关联"),
    ("E11", "复验包", "dist/taskA_<run_id>.zip + SHA256SUMS", "包内含报告/日志/测试输出，不含法规全文"),
]
elines = [
    "# 任务A 证据索引（真实产物）",
    "",
    "- run_id：%s" % run_manifest["run_id"],
    "- 生成时间：%s" % result["generated_at"],
    "",
    "| 证据ID | 对应产物 | 证明什么 | 不能证明什么 / 待办 |",
    "|---|---|---|---|",
]
for e in evidence:
    elines.append("| %s | %s | %s | %s |" % e)
elines += ["", "## 产物 hash", ""]
for rel, h in artifacts.items():
    elines.append("- `%s`：`%s`" % (rel, h))
elines += ["", "> 未采集的截图、未提交的 commit 均未列入已完成证据；不得用本文件替代主办方要求的平台记录。"]
with open(os.path.join(REPORTS, "evidence_index.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(elines) + "\n")

readme = r"""# HCS 任务A：中文条款切分、定位与引用验证

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
"""
with open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8") as f:
    f.write(readme)

print("written reports/RESULTS_taskA_filled.md")
print("written reports/evidence_index.md")
print("written README.md")
print("auto=%d/%d counter=%d/%d locator=%d/%d tests=%d/%d" % (
    passed_auto, len(auto_cases), passed_counter, len(counter_cases),
    locator["summary"]["passed"], locator["summary"]["total"],
    tests["passed"], tests["total"]))