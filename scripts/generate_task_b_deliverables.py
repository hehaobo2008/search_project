import hashlib
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS = os.path.join(ROOT, "reports")
LOGS = os.path.join(ROOT, "logs", "task_b")


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def esc(text):
    return str(text).replace("|", "\\|").replace("\n", " ")


run_manifest = load(os.path.join(LOGS, "run_manifest.json"))
dev = load(os.path.join(REPORTS, "task_b_dev_results.json"))
tests = load(os.path.join(REPORTS, "task_b_test_result.json"))
model = load(os.path.join(ROOT, "work", "models", "bge-small-zh-v1.5", "MODEL_MANIFEST.json"))
config = load(os.path.join(ROOT, "config", "task_b_config.json"))

model_onnx = next(f for f in model["files"] if f["file"] == "onnx/model.onnx")
hashes = {
    "config/task_b_config.json": sha(os.path.join(ROOT, "config", "task_b_config.json")),
    "data/task_b_dev_questions.jsonl": sha(os.path.join(ROOT, "data", "task_b_dev_questions.jsonl")),
    "data/task_b_freeze_candidates.jsonl": sha(os.path.join(ROOT, "data", "task_b_freeze_candidates.jsonl")),
    "corpus/docs_manifest.json": sha(os.path.join(ROOT, "corpus", "docs_manifest.json")),
    "reports/task_b_dev_results.json": sha(os.path.join(REPORTS, "task_b_dev_results.json")),
    "logs/task_b/run_manifest.json": sha(os.path.join(LOGS, "run_manifest.json")),
}
start = run_manifest["steps"][0]["started_at"]
end = run_manifest["steps"][-1]["ended_at"]
cmds = "\n".join("%d. `%s` → exit=%d，%.3fs，日志 `%s`（%d bytes）" % (
    i + 1, s["command"], s["exit_code"], s["duration_sec"], s["log"], s["log_bytes"])
    for i, s in enumerate(run_manifest["steps"]))
s = dev["summary"]

lines = [
    "# 任务B 实际运行记录（开发集探索）",
    "",
    "> **重要边界：** 任务A人工闸门 H01-H08 尚未签字；本记录是在用户指令下开展的任务B开发集探索，**不是独立冻结测试成绩**，不用于宣称泛化或优于其他系统。冻结候选 20 题仍为 `unlabeled`，未运行。",
    "",
    "## 一次运行身份",
    "",
    "- 流水线 run_id：%s" % run_manifest["run_id"],
    "- 任务与状态：B / 开发集探索已运行；冻结测试未标注、未运行",
    "- 平台：当前 CodeArts Agent 会话，项目 `search_project`（截图待采集）",
    "- 实际开始/结束及UTC偏移：%s 至 %s（UTC+08:00）" % (start, end),
    "- 运行时：Python %s；onnxruntime 1.31.0 CPUExecutionProvider；tokenizers 0.23.3；jieba 0.42.1；rank_bm25 0.2.2；numpy 2.5.1" % run_manifest["python"].split()[0],
    "- 模型：BAAI/bge-small-zh-v1.5；分发仓库 Xenova/bge-small-zh-v1.5（ModelScope ONNX 转换）",
    "- 模型 revision：`master` 分支下载；`onnx/model.onnx` SHA-256 `%s`（%d bytes）" % (
        model_onnx["sha256"], model_onnx["bytes"]),
    "- 模型许可：%s" % model["license"],
    "- 运行时配置：max_length=%s；pooling=%s；query 指令=`%s`" % (
        model["max_length"], model["pooling"], model["query_instruction"]),
    "- 语料：A 75 条 + B 82 条，条款级证据单元；不含 C 与旧版",
    "- 配置 hash：`%s`" % hashes["config/task_b_config.json"],
    "- 开发问题集 hash：`%s`；冻结候选 hash：`%s`" % (
        hashes["data/task_b_dev_questions.jsonl"], hashes["data/task_b_freeze_candidates.jsonl"]),
    "- 语料 manifest hash：`%s`" % hashes["corpus/docs_manifest.json"],
    "- gold hash：包含在开发问题集与 `task_b_dev_results.json` 中，未独立冻结",
    "- commit：项目未初始化 Git，无 commit",
    "- 会话历史：本平台；截图待采集",
    "",
    "## 实际命令与退出码",
    "",
    cmds,
    "",
    "## 方法配置（开发集调试，未冻结）",
    "",
    "- 词法：jieba `cut_for_search`，保护第X条/第X章/书名号/数字/英文；BM25Okapi",
    "- 语义：BGE-small-zh-v1.5 ONNX，CLS pooling + L2；query 加中文检索指令，文档不加",
    "- 融合：RRF k=60，每路候选 50；并列按 article_id 升序",
    "- 输出预算：Top7 与 Top5+补证均每单元最多 400 字符、最多 7 单元（总上限 2800 字符）；Top5 辅助",
    "- 补证：从 Top2 种子沿显式条款/修改关系补最多 2 条；目标须在融合前 10、版本已解析、排除重复；不自动回填；主题相关不混入",
    "- 无答案：未知术语≥3，或未知≥1且最高语义相似度<0.62 时拒绝",
    "",
    "## 检索结果（开发集 N=%d）" % s["top7"]["paired_n"],
    "",
    "| 方法 | 配对N | Hit | 全证据 | 命中组/总组 | 宏Recall | 微Recall | 单元均值 | 字符均值 | p50/p95 ms |",
    "|---|---|---|---|---|---|---|---|---|---|",
]
for key, label in [("top5", "普通Top5（辅助）"), ("top7", "普通Top7（主基线）"),
                   ("top5_supplement", "Top5+≤2补证（主比较）")]:
    m = s[key]
    lines.append("| %s | %d | %d/%d | %d/%d | %d/%d | %.4f | %.4f | %.2f | %.2f | %.2f/%.2f |" % (
        label, m["paired_n"], m["hit"], m["paired_n"], m["full_evidence"], m["paired_n"],
        m["groups_hit"], m["groups_total"], m["macro_recall"], m["micro_recall"],
        m["units_mean"], m["chars_mean"], m["latency_p50_ms"], m["latency_p95_ms"]))

p = dev["pairwise_top7_vs_supplement"]
lines += [
    "",
    "## 配对变化与补证触发",
    "",
    "- 补证组独有成功：%d；Top7 独有成功：%d；均成功：%d；均失败：%d" % (
        p["supplement_only"], p["top7_only"], p["both_success"], p["both_fail"]),
    "- 补证触发题数：%d/%d；补证单元总数：%d" % (
        dev["supplement_triggered_questions"], s["top7"]["paired_n"],
        dev["supplement_total_units"]),
    "- 观察：补证组与 Top7 在开发集 Hit 相同；补证组平均使用 %0.2f 个单元、%0.2f 字符，Top7 为 %d 个单元、%0.2f 字符。样本小，不能据此宣称补证更优。" % (
        s["top5_supplement"]["units_mean"], s["top5_supplement"]["chars_mean"],
        s["top7"]["units_mean"], s["top7"]["chars_mean"]),
    "",
    "## 独立分组",
    "",
    "| 分组 | N | 正确 | 错误/其他 |",
    "|---|---|---|---|",
    "| 无答案 | %d | %d 正确拒绝 | %d 错误输出证据 |" % (
        dev["no_answer"]["n"], dev["no_answer"]["correct_refuse"], dev["no_answer"]["wrong_evidence"]),
    "| 版本冲突 | %d | %d 正确提示待核验 | %d 错版本/其他 |" % (
        dev["version_conflict"]["n"], dev["version_conflict"]["correct_pending"],
        dev["version_conflict"]["wrong"]),
    "| 引用歧义 | %d | %d 正确提示 | %d 错误硬连 |" % (
        dev["citation_ambiguity"]["n"], dev["citation_ambiguity"]["correct"],
        dev["citation_ambiguity"]["wrong_hardlink"]),
    "",
    "## 逐题摘要",
    "",
    "| qid | 题型 | 问题 | Top5 | Top7 | 补证 | 单元/字符 |",
    "|---|---|---|---|---|---|---|",
]
for r in dev["retrieval_rows"]:
    lines.append("| %s | retrieval | %s | %s | %s | %s | %d/%d |" % (
        r["qid"], esc(r["question"]), r["methods"]["top5"]["hit"], r["methods"]["top7"]["hit"],
        r["methods"]["top5_supplement"]["hit"], r["methods"]["top5_supplement"]["units"],
        r["methods"]["top5_supplement"]["chars"]))
for r in dev["no_answer"]["rows"]:
    lines.append("| %s | no_answer | %s | %s | - | - | - |" % (
        r["qid"], esc(r["question"]), "正确拒绝" if r["correct_refuse"] else "错误出证据"))
for r in dev["version_conflict"]["rows"]:
    lines.append("| %s | version_conflict | %s | %s | - | - | - |" % (
        r["qid"], esc(r["question"]), "版本待核验" if r["correct"] else "错误"))
for r in dev["citation_ambiguity"]["rows"]:
    lines.append("| %s | citation_ambiguity | %s | %s | - | - | - |" % (
        r["qid"], esc(r["question"]), r["state"]))

lines += [
    "",
    "## 回归测试",
    "",
    "- 任务B测试：%d 项，通过 %d，失败 %d，错误 %d（`logs/task_b/runs/%s/run_tests.log`）。" % (
        tests["total"], tests["passed"], len(tests["failures"]), len(tests["errors"]),
        run_manifest["run_id"]),
    "- 覆盖：检索确定性、三方法预算、补证 base5 不变、D03 补到 B65、无答案/版本/歧义分支、指标函数、模型 hash、冻结候选未标注",
    "",
    "## 失败与限制",
    "",
    "- 任务A人工闸门未签字；任务B正式冻结测试未开始，不得进入“测试成绩”表述。",
    "- 开发集仅 13 道检索题；补证组无 Top7 之外的独有成功；无答案规则样本仅 2 题。",
    "- BGE 使用 ModelScope 的 ONNX 转换版本，非 BAAI 原始 PyTorch 权重逐字节一致；已固定文件 hash，未做转换等价性验证。",
    "- 未做模型 revision 多版本比较、FP16/量化、ONNX 与 PyTorch 输出对比、手机端推理或性能测试。",
    "- 未做真实用户试用、阅读负担、核查用时和岗位收益测试。",
    "",
    "## 可主张范围",
    "",
    "本轮可主张：在公开 A/B 语料与 13 道开发题上，中文 BM25+BGE+RRF 检索链路可运行；Top7 与补证组均达到 13/13 Hit；版本冲突、无答案和引用歧义分支能给出待核验/拒绝/主题相关提示。不可主张：独立测试成绩、领域泛化、优于其他系统、端侧性能、真实业务提效，也不可把开发集结果追认为任务A闸门通过。",
]

with open(os.path.join(REPORTS, "RESULTS_taskB_filled.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

elines = [
    "# 任务B 证据索引（开发集探索）",
    "",
    "- run_id：%s" % run_manifest["run_id"],
    "- 生成时间：%s" % dev["generated_at"],
    "",
    "| 证据ID | 对应产物 | 证明什么 | 不能证明什么 / 待办 |",
    "|---|---|---|---|",
    "| B01 | 平台与会话 | 本次运行发生在 CodeArts Agent 会话 | 截图待采集；不能单独证明实验完成 |",
    "| B02 | 模型 manifest | 来源、许可、revision 与文件 hash | 非 BAAI 原始权重逐字节一致；许可需人工复核 |",
    "| B03 | 配置 hash | 融合、候选、预算、补证、答案判定配置 | 开发集调试配置，未冻结 |",
    "| B04 | 独立运行日志 | logs/task_b/runs/%s 四步日志与退出码0 | 不代表任务A闸门通过 |" % run_manifest["run_id"],
    "| B05 | 开发集结果 | 18 题逐题结果、整数计数、失败与限制 | 非独立测试；样本小 |",
    "| B06 | 冻结候选 | 20 题 unlabeled，未运行 | 尚未标注，不产生成绩 |",
    "| B07 | 任务B测试 | 8/8 通过 | 只验证工程规则，不验证检索泛化 |",
    "| B08 | 边界声明 | 明确未做端侧、用户试用、显著性 | 不能外推 |",
    "",
    "## 产物 hash",
    "",
]
for rel, h in hashes.items():
    elines.append("- `%s`：`%s`" % (rel, h))
elines.append("")
elines.append("> 模型权重约 95MB，未纳入本记录；hash 见 MODEL_MANIFEST.json。")
with open(os.path.join(REPORTS, "task_b_evidence_index.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(elines) + "\n")

print("written reports/RESULTS_taskB_filled.md")
print("written reports/task_b_evidence_index.md")
print("dev N=%d hit top7=%d supp=%d top5=%d" % (
    s["top7"]["paired_n"], s["top7"]["hit"], s["top5_supplement"]["hit"], s["top5"]["hit"]))