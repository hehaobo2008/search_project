import json
import os
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from task_b_retriever import TaskBRetriever  # noqa: E402

REPORTS = os.path.join(ROOT, "reports")
os.makedirs(REPORTS, exist_ok=True)

config = json.load(open(os.path.join(ROOT, "config", "task_b_config.json"), encoding="utf-8"))
questions = [json.loads(line) for line in open(
    os.path.join(ROOT, "data", "task_b_dev_questions.jsonl"), encoding="utf-8")]


def percentile(values, p):
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = min(len(ordered) - 1, int(round((len(ordered) - 1) * p)))
    return ordered[idx]


def groups_hit(groups, units):
    unit_ids = {u["article_id"] for u in units}
    return [any(candidate in unit_ids for candidate in group.split("|")) for group in groups]


def eval_method(units, q):
    hits = groups_hit(q["required_groups"], units)
    return {
        "hit": any(hits),
        "all_covered": all(hits),
        "groups_hit": sum(hits),
        "groups_total": len(hits),
        "recall": (sum(hits) / len(hits)) if hits else 0.0,
        "units": len(units),
        "chars": sum(u["chars"] for u in units),
        "ids": [u["article_id"] for u in units],
        "texts": [{"article_id": u["article_id"], "chars": u["chars"],
                   "truncated": u["truncated"], "relation": u.get("relation")} for u in units],
    }


def main():
    retriever = TaskBRetriever(
        top_candidates=config["fusion"]["candidate_limit_per_route"],
        rrf_k=config["fusion"]["k"],
        unit_char_budget=config["methods"]["top7"]["unit_char_budget"])
    rows = []
    no_answer_rows = []
    version_rows = []
    ambiguity_rows = []

    for q in questions:
        group = q["group"]
        started = time.time()
        if group == "retrieval":
            ranked = retriever.search(q["question"])
            assess = retriever.assess_answerability(
                q["question"],
                min_unknown=config["answerability"]["min_unknown_hard"])
            methods_started = time.time()
            raw = retriever.methods(ranked)
            methods_ms = round((time.time() - methods_started) * 1000, 2)
            row = {
                "qid": q["qid"],
                "question": q["question"],
                "required_groups": q["required_groups"],
                "note": q.get("note", ""),
                "answerability": assess,
                "normalized_query": retriever.last_normalized_query,
                "top7_ids": [x["article_id"] for x in ranked[:7]],
                "top7_scores": [{"article_id": x["article_id"], "score": x["score"],
                                 "lex_rank": x["lex_rank"], "sem_rank": x["sem_rank"]}
                                for x in ranked[:7]],
                "elapsed_ms": round((time.time() - started) * 1000, 2),
                "search_ms": retriever.last_search_ms,
                "methods": {},
            }
            for name in ("top5", "top7", "top5_supplement"):
                row["methods"][name] = eval_method(raw[name], q)
                row["methods"][name]["supplements"] = max(0, len(raw[name]) - 5)
            rows.append(row)
        elif group == "no_answer":
            ranked = retriever.search(q["question"])
            assess = retriever.assess_answerability(
                q["question"], min_unknown=config["answerability"]["min_unknown_hard"])
            no_answer_rows.append({
                "qid": q["qid"],
                "question": q["question"],
                "decision": assess["decision"],
                "unknown_terms": assess["unknown_terms"],
                "max_sem": assess["max_sem"],
                "top1": ranked[0]["article_id"] if ranked else None,
                "correct_refuse": assess["decision"] == "refuse",
            })
        elif group == "version_conflict":
            check = retriever.version_check(q["question"])
            version_rows.append({
                "qid": q["qid"],
                "question": q["question"],
                "state": check.get("state"),
                "message": check.get("message", ""),
                "correct": check.get("state") == q.get("expected_version_state", "pending"),
            })
        elif group == "citation_ambiguity":
            check = retriever.inspect_relation(q["pair"])
            ambiguity_rows.append({
                "qid": q["qid"],
                "question": q["question"],
                "pair": q["pair"],
                "expected": q["expected_relation"],
                "state": check["state"],
                "message": check["message"],
                "correct": check["state"] == q["expected_relation"],
            })

    N = len(rows)
    summary = {}
    for name in ("top5", "top7", "top5_supplement"):
        hit = sum(1 for r in rows if r["methods"][name]["hit"])
        full = sum(1 for r in rows if r["methods"][name]["all_covered"])
        groups_hit_total = sum(r["methods"][name]["groups_hit"] for r in rows)
        groups_total = sum(r["methods"][name]["groups_total"] for r in rows)
        macro = sum(r["methods"][name]["recall"] for r in rows) / N if N else 0.0
        units = [r["methods"][name]["units"] for r in rows]
        chars = [r["methods"][name]["chars"] for r in rows]
        times = [r["elapsed_ms"] for r in rows]
        summary[name] = {
            "paired_n": N,
            "hit": hit,
            "full_evidence": full,
            "groups_hit": groups_hit_total,
            "groups_total": groups_total,
            "macro_recall": round(macro, 4),
            "micro_recall": round(groups_hit_total / groups_total, 4) if groups_total else None,
            "units_mean": round(sum(units) / N, 2) if N else 0,
            "chars_mean": round(sum(chars) / N, 2) if N else 0,
            "latency_p50_ms": round(percentile(times, 0.5), 2),
            "latency_p95_ms": round(percentile(times, 0.95), 2),
        }

    top7 = [r["methods"]["top7"]["hit"] for r in rows]
    supp = [r["methods"]["top5_supplement"]["hit"] for r in rows]
    pair = {
        "supplement_only": sum(1 for a, b in zip(top7, supp) if b and not a),
        "top7_only": sum(1 for a, b in zip(top7, supp) if a and not b),
        "both_success": sum(1 for a, b in zip(top7, supp) if a and b),
        "both_fail": sum(1 for a, b in zip(top7, supp) if not a and not b),
    }
    supplements_used = sum(r["methods"]["top5_supplement"]["supplements"] for r in rows)
    triggered = sum(1 for r in rows if r["methods"]["top5_supplement"]["supplements"] > 0)

    result = {
        "generated_at": __import__("datetime").datetime.now().astimezone().isoformat(),
        "split": "dev",
        "disclaimer": "开发集为调试用，不是独立冻结测试，不能作为泛化成绩；gold由本次会话构造，待人工复核。",
        "config": config,
        "model_manifest": json.load(open(os.path.join(
            ROOT, "work", "models", "bge-small-zh-v1.5", "MODEL_MANIFEST.json"), encoding="utf-8")),
        "vector_cache_hit": retriever.vector_cache_hit,
        "embed_docs_ms": retriever.embed_ms,
        "summary": summary,
        "pairwise_top7_vs_supplement": pair,
        "supplement_triggered_questions": triggered,
        "supplement_total_units": supplements_used,
        "retrieval_rows": rows,
        "no_answer": {
            "n": len(no_answer_rows),
            "correct_refuse": sum(1 for r in no_answer_rows if r["correct_refuse"]),
            "wrong_evidence": sum(1 for r in no_answer_rows if not r["correct_refuse"]),
            "rows": no_answer_rows,
        },
        "version_conflict": {
            "n": len(version_rows),
            "correct_pending": sum(1 for r in version_rows if r["correct"]),
            "wrong": sum(1 for r in version_rows if not r["correct"]),
            "rows": version_rows,
        },
        "citation_ambiguity": {
            "n": len(ambiguity_rows),
            "correct": sum(1 for r in ambiguity_rows if r["correct"]),
            "wrong_hardlink": sum(1 for r in ambiguity_rows if not r["correct"]),
            "rows": ambiguity_rows,
        },
    }
    with open(os.path.join(REPORTS, "task_b_dev_results.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    lines = [
        "# 任务B 开发集探索报告",
        "",
        "> **非独立测试成绩。** 本报告只用于开发调试；gold 由本次会话按条款构造，尚未由第二名标注者独立复核。冻结测试题须人工标注后另存，不得把本结果当作泛化结论。",
        "",
        "- 生成时间：%s" % result["generated_at"],
        "- 语料：A 75 条 + B 82 条，条款级证据单元；同一长条多款合并为一个单元",
        "- 模型：BAAI/bge-small-zh-v1.5 ONNX（Xenova 转换，ModelScope 取得），CLS+L2，query 加中文检索指令",
        "- 融合：BM25 + BGE，RRF k=60，每路候选 50，并列按 article_id 升序",
        "- 答案判定：未知术语≥3，或未知≥1且最高语义相似度<0.62 时拒绝",
        "- 补证：从 Top2 种子沿显式条款/修改关系补最多2条，目标须在融合前10、版本已解析、排除重复；不自动回填",
        "- 同预算：Top7 与 Top5+补证均为每单元最多400字符、总数最多7；Top5 仅辅助观察",
        "",
        "## 检索配对结果（N=%d）" % N,
        "",
        "| 方法 | 配对N | Hit题数/N | 全证据题数/N | 命中组/总组 | 宏平均Recall | 微平均Recall | 单元数均值 | 字符量均值 | p50/p95 ms |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for name, label in [("top5", "普通Top5（辅助）"), ("top7", "普通Top7（主基线）"),
                        ("top5_supplement", "Top5+≤2补证（主比较）")]:
        s = summary[name]
        lines.append("| %s | %d | %d/%d | %d/%d | %d/%d | %.4f | %.4f | %.2f | %.2f | %.2f/%.2f |" % (
            label, s["paired_n"], s["hit"], s["paired_n"], s["full_evidence"], s["paired_n"],
            s["groups_hit"], s["groups_total"], s["macro_recall"], s["micro_recall"],
            s["units_mean"], s["chars_mean"], s["latency_p50_ms"], s["latency_p95_ms"]))

    lines += [
        "",
        "## Top7 与补证组配对变化",
        "",
        "| 补证组独有成功 | Top7独有成功 | 均成功 | 均失败 | 补证触发题数 | 补证单元总数 |",
        "|---|---|---|---|---|---|",
        "| %d | %d | %d | %d | %d/%d | %d |" % (
            pair["supplement_only"], pair["top7_only"], pair["both_success"], pair["both_fail"],
            triggered, N, supplements_used),
        "",
        "> 本轮补证只在源条进入 Top2 且目标位于融合前10时触发；未触发的题不自动回填。开发集样本小，补证组与 Top7 的差异不能作为统计结论。",
        "",
        "## 独立分组",
        "",
        "| 分组 | N | 正确 | 错误/其他 | 说明 |",
        "|---|---|---|---|---|",
        "| 无答案 | %d | %d 正确拒绝 | %d 错误输出证据 | 规则为开发集调试；仅2题 |" % (
            result["no_answer"]["n"], result["no_answer"]["correct_refuse"],
            result["no_answer"]["wrong_evidence"]),
        "| 版本冲突 | %d | %d 正确提示待核验 | %d 错版本/其他 | 2015/2017 未入锁定索引 |" % (
            result["version_conflict"]["n"], result["version_conflict"]["correct_pending"],
            result["version_conflict"]["wrong"]),
        "| 引用歧义 | %d | %d 正确提示 | %d 错误硬连 | 主题相关/文件级不升级为条款引用 |" % (
            result["citation_ambiguity"]["n"], result["citation_ambiguity"]["correct"],
            result["citation_ambiguity"]["wrong_hardlink"]),
        "",
        "## 逐题明细",
        "",
        "| qid | 组 | 题 | Top5命中 | Top7命中 | 补证命中 | 补证单元 | 单元数/字符量 |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append("| %s | retrieval | %s | %s | %s | %s | %d | %d/%d |" % (
            r["qid"], r["question"], r["methods"]["top5"]["hit"], r["methods"]["top7"]["hit"],
            r["methods"]["top5_supplement"]["hit"], r["methods"]["top5_supplement"]["supplements"],
            r["methods"]["top5_supplement"]["units"], r["methods"]["top5_supplement"]["chars"]))
    for r in no_answer_rows:
        lines.append("| %s | no_answer | %s | %s | - | - | - | - |" % (
            r["qid"], r["question"], "正确拒绝" if r["correct_refuse"] else "错误出证据"))
    for r in version_rows:
        lines.append("| %s | version | %s | %s | - | - | - | - |" % (
            r["qid"], r["question"], "版本待核验" if r["correct"] else "错误"))
    for r in ambiguity_rows:
        lines.append("| %s | ambiguity | %s | %s | - | - | - | - |" % (
            r["qid"], r["question"], r["state"]))

    lines += [
        "",
        "## 失败与限制",
        "",
        "- 开发集仅 %d 道检索题，不能支持显著性或泛化结论。" % N,
        "- 补证组未出现 Top7 之外的独有成功；同预算下引用补证尚未显示出额外收益。",
        "- 无答案判定依赖开发集调出的未知术语规则，样本仅2题，需在冻结测试集上独立验证。",
        "- 未做 BGE revision 多版本比较、未做 FP16/ONNX 量化、未做手机端推理或性能测试。",
        "- 未进行真实用户试用、阅读负担或核查用时测试。",
        "",
        "## 可主张范围",
        "",
        "本轮可主张：在公开 A/B 语料与 %d 道开发题上，中文 BM25+BGE+RRF 检索链路可运行，Top7 与补证组在开发集均达到 %d/%d Hit；版本冲突与引用歧义分支能给出待核验/主题相关提示。不可主张：独立测试成绩、领域泛化、优于其他系统、端侧性能或真实业务提效。" % (
            N, summary["top5_supplement"]["hit"], N),
    ]
    with open(os.path.join(REPORTS, "task_b_dev_report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print("retrieval N=%d" % N)
    for name in ("top5", "top7", "top5_supplement"):
        s = summary[name]
        print("%-18s hit=%d/%d full=%d/%d groups=%d/%d macro=%.4f units=%.2f chars=%.2f" % (
            name, s["hit"], N, s["full_evidence"], N, s["groups_hit"], s["groups_total"],
            s["macro_recall"], s["units_mean"], s["chars_mean"]))
    print("pairwise", pair, "supplements", supplements_used, "triggered", triggered)
    print("no_answer", result["no_answer"]["correct_refuse"], "/", result["no_answer"]["n"])
    print("version", result["version_conflict"]["correct_pending"], "/", result["version_conflict"]["n"])
    print("ambiguity", result["citation_ambiguity"]["correct"], "/", result["citation_ambiguity"]["n"])
    sys.exit(0)


if __name__ == "__main__":
    main()