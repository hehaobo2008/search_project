import hashlib
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS = os.path.join(ROOT, "reports")
LOGS = os.path.join(ROOT, "logs", "task_b")

METHODS = ["bm25_top7", "dense_top7", "hybrid_top7", "hybrid_top5_supplement", "hybrid_top5"]
LABELS = {
    "bm25_top7": "纯BM25 Top7",
    "dense_top7": "纯语义 Top7",
    "hybrid_top7": "混合 Top7",
    "hybrid_top5_supplement": "混合 Top5+≤2补证",
    "hybrid_top5": "混合 Top5（辅助）",
}


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
model = load(os.path.join(ROOT, "docs", "bge-small-zh-v1.5-MODEL_MANIFEST.json"))
config = load(os.path.join(ROOT, "config", "task_b_config.json"))
onnx = next(f for f in model["files"] if f["file"] == "onnx/model.onnx")
hashes = {
    "config/task_b_config.json": sha(os.path.join(ROOT, "config", "task_b_config.json")),
    "data/task_b_dev_questions.jsonl": sha(os.path.join(ROOT, "data", "task_b_dev_questions.jsonl")),
    "data/task_b_module_questions.jsonl": sha(os.path.join(ROOT, "data", "task_b_module_questions.jsonl")),
    "data/task_b_rewrite_candidates.jsonl": sha(os.path.join(ROOT, "data", "task_b_rewrite_candidates.jsonl")),
    "reports/task_b_dev_results.json": sha(os.path.join(REPORTS, "task_b_dev_results.json")),
    "logs/task_b/run_manifest.json": sha(os.path.join(LOGS, "run_manifest.json")),
}
start = run_manifest["steps"][0]["started_at"]
end = run_manifest["steps"][-1]["ended_at"]
cmds = "\n".join("%d. `%s` → exit=%d，%.3fs，日志 `%s`（%d bytes）" % (
    i + 1, s["command"], s["exit_code"], s["duration_sec"], s["log"], s["log_bytes"])
    for i, s in enumerate(run_manifest["steps"]))
s = dev["summary"]
N = dev["N"]

lines = [
    "# 任务B 实际运行记录（开发集端到端，dev_gold_v2）",
    "",
    "> **边界：** 本记录是 13 道开发检索题的端到端工程评测，**不是产品准确率，也不是独立冻结测试**。gold 为 `dev_gold_v2`，由本次会话按信息需求重标，仍待人工复核。20 道同语料改写候选未标注、未运行，不能宣称跨主题泛化。",
    "",
    "## 一次运行身份",
    "",
    "- 流水线 run_id：%s" % run_manifest["run_id"],
    "- 任务与状态：B / 开发集端到端评测；模块测试单列；改写测试未运行",
    "- 平台：当前 CodeArts Agent 会话，项目 `search_project`（截图待采集）",
    "- 实际开始/结束及UTC偏移：%s 至 %s（UTC+08:00）" % (start, end),
    "- 运行时：Python %s；onnxruntime 1.31.0 CPUExecutionProvider；tokenizers 0.23.3；jieba 0.42.1；rank_bm25 0.2.2；numpy 2.5.1" % run_manifest["python"].split()[0],
    "- 模型：BAAI/bge-small-zh-v1.5，ONNX 分发仓库 Xenova/bge-small-zh-v1.5（ModelScope）",
    "- 模型 revision / hash：`onnx/model.onnx` SHA-256 `%s`（%d bytes）" % (onnx["sha256"], onnx["bytes"]),
    "- 模型许可：%s" % model["license"],
    "- 配置 hash：`%s`（运行前冻结）" % hashes["config/task_b_config.json"],
    "- 开发问题集 hash：`%s`；模块题 hash：`%s`；改写候选 hash：`%s`" % (
        hashes["data/task_b_dev_questions.jsonl"], hashes["data/task_b_module_questions.jsonl"],
        hashes["data/task_b_rewrite_candidates.jsonl"]),
    "- commit：项目未初始化 Git，无 commit",
    "",
    "## 实际命令与退出码",
    "",
    cmds,
    "",
    "## 统一入口与数据隔离",
    "",
    "- 被测系统：`TaskBSystem.answer(question, method)`，只接收自然语言问题与方法名，不读取 qid、题型、standard answer 或预标条款对。",
    "- 评分器：`task_b_eval.py` 读取问题集与 gold，调用 `answer(question, method)`，再按信息需求评分。",
    "- 版本/引用歧义：`module_version_check`、`module_relation_check` 只做模块测试，不进入端到端成绩。",
    "",
    "## 证据标注 v2",
    "",
    "每题按信息需求拆分 requirement；每个 requirement 允许多个可接受证据。",
    "- D01/D16：监督取样主体（A30 或 B31）+ 记录签字依据（A30 或 B29）。A30 单条可同时覆盖两项；B31+B29 也构成一套充分组合。",
    "- D17：A65 与 A66 两个独立需求。",
    "- D03/D04/D18：A66/A67 只是入口，不替代被引条例原文。",
    "",
    "## 同预算对照（开发集 N=%d）" % N,
    "",
    "| 方法 | Hit | 全证据 | 需求命中/总需求 | 宏Recall | 微Recall | 单元均值 | 字符均值 | 查询p50/p95 ms |",
    "|---|---|---|---|---|---|---|---|---|",
]
for method in METHODS:
    m = s[method]
    lines.append("| %s | %d/%d | %d/%d | %d/%d | %.4f | %.4f | %.2f | %.2f | %.2f/%.2f |" % (
        LABELS[method], m["hit"], N, m["full"], N, m["aspects_hit"], m["aspects_total"],
        m["macro_recall"], m["micro_recall"], m["units_mean"], m["chars_mean"],
        m["answer_ms_p50"], m["answer_ms_p95"]))

lines += [
    "",
    "> 耗时：模型/文档向量只加载一次；各方法各自调用 `answer()` 独立查询。表中为每方法独立查询 p50/p95，不把同一轮共享检索耗时复制成多个方法的独立速度成绩。",
    "",
    "## 失败统计（保留全部失败题）",
    "",
    "| 方法 | Hit失败 | 全证据失败 | 有答案却被拒绝 | 无答案却出结果 | 错误补证单元 | 补证单元总数 |",
    "|---|---|---|---|---|---|---|",
]
for method in METHODS:
    m = s[method]
    na = dev["no_answer"][method]
    lines.append("| %s | %d | %d | %d/%d | %d/%d | %d | %d |" % (
        LABELS[method], m["hit_fail"], m["full_fail"], m["answerable_refused"], N,
        na["wrong_evidence"], na["n"], m["wrong_supplements"], m["supplements_total"]))

lines += [
    "",
    "## 配对变化",
    "",
    "| 比较 | A独有成功 | B独有成功 | 均成功 | 均失败 |",
    "|---|---|---|---|---|",
]
for key, label in [("hybrid_top7_vs_supplement", "混合Top7 vs 补证"),
                   ("bm25_vs_hybrid", "纯BM25 vs 混合Top7"),
                   ("dense_vs_hybrid", "纯语义 vs 混合Top7")]:
    c = dev["comparisons"][key]
    lines.append("| %s | %d | %d | %d | %d |" % (label, c["a_only"], c["b_only"],
                                                c["both"], c["neither"]))

lines += ["", "## 模块测试（不计端到端）", "",
          "| 用例 | 类型 | 期望 | 实际 | 结论 |", "|---|---|---|---|---|"]
for r in dev["module_tests"]["rows"]:
    lines.append("| %s | %s | %s | %s | %s |" % (
        r["qid"], r["group"], r["expected"], r["state"], "通过" if r["correct"] else "失败"))

lines += ["", "## 逐题结果（方法 Hit / 全证据）", "",
          "| qid | 需求组 | 纯BM25 | 纯语义 | 混合 | 补证 |",
          "|---|---|---|---|---|---|"]
for r in dev["retrieval_rows"]:
    cells = []
    for method in ("bm25_top7", "dense_top7", "hybrid_top7", "hybrid_top5_supplement"):
        m = r["methods"][method]
        cells.append("%s/%s" % (m["hit"], m["full"]))
    lines.append("| %s | %d | %s |" % (r["qid"], len(r["requirements"]), " | ".join(cells)))
for r in dev["no_answer_rows"]:
    decision = r["methods"]["hybrid_top7"]["decision"]
    lines.append("| %s | no_answer | %s | %s | %s | %s |" % (
        r["qid"], decision, decision, decision, decision))

lines += ["", "## 失败明细", ""]
if dev["failures"]:
    for f in dev["failures"]:
        lines.append("- `%s` / %s：%s %s" % (
            f["qid"], f["method"], f["failure"], f.get("detail", "")))
else:
    lines.append("- 无失败项；不人为制造失败。")

lines += [
    "",
    "## 回归测试",
    "",
    "- 任务B测试：%d 项，通过 %d，失败 %d，错误 %d（`logs/task_b/runs/%s/run_tests.log`）。" % (
        tests["total"], tests["passed"], len(tests["failures"]), len(tests["errors"]),
        run_manifest["run_id"]),
    "",
    "## 失败与限制",
    "",
    "- 开发集仅 13 道检索题；BM25/语义/混合/补证结果只能说明该开发集上的工程表现。",
    "- 补证组与混合 Top7 的 Hit 相同，没有展示出额外收益；D03 在补证组成功、在纯语义与混合 Top5 失败。",
    "- 有答案却被拒绝 0、无答案却出结果 0、错误补证 0（按本开发集与被测规则）。这不代表在其他问题上不会发生。",
    "- 同语料改写候选 20 题未标注、未运行；F05/F07/F08/F10 与开发题高度接近，只能作为同语料改写测试。",
    "- 未做端侧转换、手机性能、真实用户试用、显著性检验。",
    "",
    "## 可主张范围",
    "",
    "本轮可主张：统一入口在 13 道开发检索题上可运行；纯BM25、纯语义、混合、混合+补证在同一输出预算下完成了对照；失败题、拒绝/误出证据、错误补证均有逐题记录。不可主张：产品准确率、跨主题泛化、独立冻结测试成绩、补证已被证明有效、端侧性能或真实业务提效。",
]

with open(os.path.join(REPORTS, "RESULTS_taskB_filled.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

elines = [
    "# 任务B 证据索引（开发集端到端）",
    "",
    "- run_id：%s" % run_manifest["run_id"],
    "- 生成时间：%s" % dev["generated_at"],
    "",
    "| 证据ID | 对应产物 | 证明什么 | 不能证明什么 / 待办 |",
    "|---|---|---|---|",
    "| B01 | 平台与会话 | 本次运行发生在 CodeArts Agent 会话 | 截图待采集 |",
    "| B02 | 模型 manifest | 来源、许可、revision、文件 hash | 非 BAAI 原始权重逐字节一致；许可需人工复核 |",
    "| B03 | 配置 hash | 运行前冻结的方法、预算、补证与答案判定 | 开发集配置，不是行业标准 |",
    "| B04 | 独立日志 | logs/task_b/runs/%s 四步日志与退出码0 | 不代表任务A闸门通过 |" % run_manifest["run_id"],
    "| B05 | 开发集结果 | 13 题逐题逐方法结果、失败题、拒绝/误出证据/错误补证 | 非产品准确率；非独立测试 |",
    "| B06 | 同语料改写候选 | 20 题 unlabeled，未运行；含重叠家族 | 不是独立冻结测试；不宣称跨主题泛化 |",
    "| B07 | 模块测试 | 版本/引用歧义 3/3 通过 | 不计入端到端成绩 |",
    "| B08 | 回归测试 | 任务B 9/9 通过 | 只验证工程规则 |",
    "",
    "## 产物 hash",
    "",
]
for rel, h in hashes.items():
    elines.append("- `%s`：`%s`" % (rel, h))
elines += ["", "> 模型权重约 95MB，未纳入本记录；hash 见 docs/bge-small-zh-v1.5-MODEL_MANIFEST.json。"]
with open(os.path.join(REPORTS, "task_b_evidence_index.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(elines) + "\n")

print("written reports/RESULTS_taskB_filled.md")
print("written reports/task_b_evidence_index.md")
print("N=%d methods=%s" % (N, {m: s[m]["hit"] for m in METHODS}))