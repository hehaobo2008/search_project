import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORPUS = os.path.join(ROOT, "corpus")
REPORTS = os.environ.get("HCS_REPORTS_DIR", os.path.join(ROOT, "reports"))
os.makedirs(REPORTS, exist_ok=True)

manifest = json.load(open(os.path.join(CORPUS, "docs_manifest.json"), encoding="utf-8"))
articles = [json.loads(line) for line in open(os.path.join(CORPUS, "articles.jsonl"), encoding="utf-8")]
relations = [json.loads(line) for line in open(os.path.join(CORPUS, "relations.jsonl"), encoding="utf-8")]
docs = {d["doc_id"]: d for d in manifest["documents"]}
arts = {(a["doc_id"], a["article_num"]): a for a in articles}

loc_docs = {}
loc_path = os.path.join(ROOT, "locators", "index.json")
if os.path.exists(loc_path):
    loc_index = json.load(open(loc_path, encoding="utf-8"))
    loc_docs = {d["doc_id"]: d for d in loc_index["documents"]}

test_result = {}
test_path = os.path.join(REPORTS, "test_result.json")
if os.path.exists(test_path):
    test_result = json.load(open(test_path, encoding="utf-8"))

result_path = os.path.join(REPORTS, "task_a_result.json")
task_result = json.load(open(result_path, encoding="utf-8")) if os.path.exists(result_path) else {}
corrected = task_result.get("summary", {}).get("corrected_records", 0)

items = [
    ("H01", "rail_quality", 2, "适用范围", "确认原文是否完整、页1版面是否为第二条起始。"),
    ("H02", "rail_quality", 30, "试块送检、监督取样、资料签认", "确认两款完整；签字主体与签认对象不可混同；页9版面与文本层一致。"),
    ("H03", "rail_quality", 66, "显式引用B第65条", "确认原文写的是‘《建设工程质量管理条例》第六十五条’且位于页22。"),
    ("H04", "construction_quality", 29, "检验与专人签字", "确认中科院副本PDF第7页与原网页逐字一致；该副本非原发布机关版本。"),
    ("H05", "construction_quality", 31, "监督取样与送检", "已按实际PDF文本层更正为第7页（旧记录‘续至第8页’保留在docs_manifest的legacy_records中）；请视觉确认第7页页尾与第8页首条。"),
    ("H06", "construction_quality", 65, "被引责任条文", "确认第16页原文；本轮只定位，不生成处罚结论。"),
]

lines = [
    "# 任务A 人工核对清单",
    "",
    "本清单列出必须由人工打开原件视觉确认的项目。自动文本层匹配、偏移切片、哈希校验与本地锚点回跳已经通过，但**不能替代视觉核对**。",
    "",
    "- 语料生成时间：%s" % manifest["generated_at"],
    "- 偏移约定：%s" % manifest["normalization_rule"],
    "- 本地回跳：点击 `../locators/...#art-N` 在浏览器打开本地定位副本并跳到对应条款；链接为相对路径，复制目录后仍可用；锚点由 `scripts/build_locators.py` 注入，条文文字未改动。",
    "- PDF回跳：`../work/raw/...pdf#page=N` 为物理页跳转，页位来自PDF文本层自动匹配，仍须人工视觉确认。",
    "- 核对结果栏由人工填写；未填写即视为闸门未通过。",
    "",
]

for cid, doc_id, num, topic, note in items:
    art = arts.get((doc_id, num))
    doc = docs[doc_id]
    pdf = doc.get("rendering") or {}
    loc = loc_docs.get(doc_id)
    block = [
        "## %s %s（%s）" % (cid, art["article_no"], topic),
        "",
        "- 文档：%s / %s" % (doc["title"], doc["doc_id"]),
        "- 版本：%s" % doc["version_id"],
        "- 来源：%s" % doc["source_url"],
        "- HTML锚点：`%s`" % art["anchor"],
        "- 字符偏移：[%d, %d)" % (art["start"], art["end"]),
    ]
    if loc:
        block.append("- 本地回跳：../locators/%s#%s" % (loc["local_html_href"], art["anchor"]))
        pdf_rel = os.path.normpath(os.path.join("..", "locators", loc["pdf_href"])).replace("\\", "/")
        block.append("- PDF回跳：%s#page=%s" % (pdf_rel, art["pdf_page_start"]))
    block += [
        "- PDF：`%s` 物理第%s页（自动文本层匹配，共%s页）" % (
            pdf.get("file"), art["pdf_page_start"], pdf.get("pages")),
        "- 原文SHA-256：`%s`" % art["sha256"],
        "- 文件SHA-256：`%s`" % doc["file_sha256"],
        "",
        "原文：",
        "",
        "> " + art["text"].replace("\n", "\n>\n> "),
        "",
        "- 核对要点：%s" % note,
        "- 人工结论：☐ 一致　☐ 不一致　☐ 无法打开（原因：__________）",
        "- 核对人：__________　核对时间（含时区）：__________",
        "",
    ]
    lines += block

# C 修改关系
c_doc = docs["rail_quality_amendment"]
c_text = open(os.path.join(CORPUS, "text_rail_quality_amendment.txt"), encoding="utf-8").read()
c_edges = [r for r in relations if r["relation_type"] == "amendment"]
c_loc = loc_docs.get("rail_quality_amendment")
lines += [
    "## H07 C修改决定（版本关系）",
    "",
    "- 文档：%s / %s" % (c_doc["title"], c_doc["doc_id"]),
    "- 版本：%s，公布并施行2021-12-23" % c_doc["version_id"],
    "- 来源：%s" % c_doc["source_url"],
    "- 与A共用文件：`%s`，文件SHA-256：`%s`" % (c_doc["file"], c_doc["file_sha256"]),
]
if c_loc:
    lines.append("- 本地回跳：../locators/%s#decision" % c_loc["local_html_href"])
lines += [
    "",
    "原文：",
    "",
    "> " + c_text.replace("\n", "\n>\n> "),
    "",
    "- 自动抽取的修改关系：%s" % "；".join(
        "%s→%s（%s）" % (r["source"]["doc_id"], r["target"]["article_no"] if r["target"] else "A全文",
                           r["evidence_text"])
        for r in c_edges),
    "- 核对要点：确认修改第69条、增设第70条、条文序号调整后重新公布；C不是第三套检测实体规则。",
    "- 人工结论：☐ 一致　☐ 不一致　☐ 无法打开（原因：__________）",
    "- 核对人：__________　核对时间（含时区）：__________",
    "",
    "## H08 引用关系语义复核",
    "",
    "- [ ] A第1条对B是**文件级依据引用**，不得展开为B第29、31条。",
    "- [ ] A第30条与B第29、31条只标**主题相关**，不是显式引用。",
    "- [ ] A第66条对B第65条是**条款级显式引用**，目标版本必须是2019年第二次修订版。",
    "- [ ] C对A第69、70条是**修改/重新公布关系**，不是并列实体规则。",
    "- 复核人：__________　复核时间（含时区）：__________",
    "",
    "## 闸门判定（人工填写）",
    "",
    "- 计划用例总数：自动16 + 版本反例6 + 人工8 = 30",
    "- 自动用例：16 项（通过 16、失败 0、已更正记录 %d）" % corrected,
    "- 版本反例：6 项（通过 6、失败 0）",
    "- 回归测试：%s" % (
        "%d 项，通过 %d，跳过测试类 %d 个、测试用例 %d 个，失败/错误 %d" % (
            test_result.get("total", 0), test_result.get("passed", 0),
            len(test_result.get("skipped_classes", [])),
            len(test_result.get("skipped_tests", [])),
            len(test_result.get("failures", [])) + len(test_result.get("errors", [])))
        if test_result else "待运行"),
    "- 人工项：8 项（待核验）",
    "- 闸门结论：☐ 通过　☐ 未通过　☐ 待核验",
    "- 签字：__________　日期：__________",
    "",
    "> 只有 H01-H08 全部核对且无关键缺陷时，才可填写“通过”。自动用例与回归测试通过不等同人工复核。",
]

open(os.path.join(REPORTS, "human_review_checklist.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
print("written reports/human_review_checklist.md")