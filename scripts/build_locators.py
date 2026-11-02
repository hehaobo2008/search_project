import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from lxml import html as LH
from lxml.html import fragment_fromstring

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORPUS = os.path.join(ROOT, "corpus")
LOCATORS = os.path.join(ROOT, "locators")
os.makedirs(LOCATORS, exist_ok=True)


def norm(text):
    return " ".join(text.split())


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def load_articles():
    return [json.loads(line) for line in open(os.path.join(CORPUS, "articles.jsonl"), encoding="utf-8")]


def find_block(doc, text):
    wanted = norm(text)
    matches = [el for el in doc.iter()
               if isinstance(el.tag, str) and el.tag in ("p", "h2", "h3", "h4")
               and norm(el.text_content()) == wanted]
    return matches[-1] if matches else None, len(matches)


def annotate(html_path, out_path, article_groups, doc_label):
    parser = LH.HTMLParser(remove_comments=False)
    doc = LH.parse(html_path, parser).getroot()
    for script in doc.xpath("//script"):
        script.getparent().remove(script)
    head = doc.xpath("//head")
    if head:
        style = fragment_fromstring('<style>:target{background:#fff2a8;outline:2px solid #d9a400;}'
                            'html{scroll-behavior:smooth;}body{max-width:1100px;margin:0 auto;'
                            'padding:16px;line-height:1.7;font-family:serif;}'
                            '.hcs-locator-banner{background:#eef4ff;border:1px solid #9bb7e0;'
                            'padding:8px 12px;margin:0 0 12px 0;font-family:sans-serif;font-size:14px;}'
                            '</style>')
        head[0].append(style)
    body = doc.xpath("//body")
    if body:
        banner = fragment_fromstring(
            '<div class="hcs-locator-banner">HCS 本地原文定位副本：%s。本副本仅用于回跳核对，'
            '正文来自公开官方页面，未改动条文文字；页面中的 id/data 属性由生成脚本注入。</div>' % doc_label)
        body[0].insert(0, banner)

    anchors = []
    errors = []
    for article in article_groups:
        anchor = article["anchor"]
        first_used = False
        for idx, para in enumerate(article["paragraphs"]):
            el, match_count = find_block(doc, para["text"])
            if el is None:
                errors.append("paragraph not found: %s #%d" % (article.get("article_no"), idx + 1))
                continue
            if match_count > 1:
                errors.append("ambiguous block match: %s #%d matched=%d, used last" % (
                    article.get("article_no"), idx + 1, match_count))
            if not first_used:
                if el.get("id") and el.get("id") != anchor:
                    errors.append("id conflict: existing=%s wanted=%s" % (el.get("id"), anchor))
                el.set("id", anchor)
                el.set("data-article-id", article.get("article_id") or anchor)
                first_used = True
            else:
                el.set("data-article-part", anchor)
        anchors.append({
            "anchor": anchor,
            "doc_id": article.get("doc_id"),
            "version_id": article.get("version_id"),
            "article_id": article.get("article_id"),
            "article_no": article.get("article_no"),
            "kind": "article",
            "text_sha256": article.get("sha256"),
            "pdf_page": article.get("pdf_page_start") if article.get("article_id") else None,
        })

    out_bytes = LH.tostring(doc, encoding="utf-8", method="html", doctype="<!DOCTYPE html>")
    with open(out_path, "wb") as f:
        f.write(out_bytes)
    return anchors, errors


def main():
    articles = load_articles()
    manifest = json.load(open(os.path.join(CORPUS, "docs_manifest.json"), encoding="utf-8"))
    docs = {d["doc_id"]: d for d in manifest["documents"]}

    a_html = os.path.join(ROOT, "work", "raw", "A_amend.html")
    b_html = os.path.join(ROOT, "work", "raw", "B_official.html")

    result = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "note": "本地定位副本只注入锚点，不改动条文文字；用于验证 file:// 回跳目标与条款文本一致。",
        "documents": [],
    }

    # A
    a_articles = [a for a in articles if a["doc_id"] == "rail_quality"]
    a_out = os.path.join(LOCATORS, "rail_quality.locator.html")
    a_anchors, a_errors = annotate(a_html, a_out, a_articles, "铁路建设工程质量监督管理规定（2021修正）")
    a_pdf = docs["rail_quality"]["rendering"]["file"]
    result["documents"].append({
        "doc_id": "rail_quality",
        "version_id": "amended_2021_12_23",
        "source_url": docs["rail_quality"]["source_url"],
        "local_html": os.path.relpath(a_out, ROOT).replace("\\", "/"),
        "local_html_href": os.path.basename(a_out),
        "local_html_sha256": sha256_file(a_out),
        "pdf_href": os.path.relpath(os.path.join(ROOT, a_pdf), LOCATORS).replace("\\", "/"),
        "anchors": a_anchors,
        "errors": a_errors,
    })

    # B
    b_articles = [a for a in articles if a["doc_id"] == "construction_quality"]
    b_out = os.path.join(LOCATORS, "construction_quality.locator.html")
    b_anchors, b_errors = annotate(b_html, b_out, b_articles, "建设工程质量管理条例（2019第二次修订）")
    b_pdf = docs["construction_quality"]["rendering"]["file"]
    result["documents"].append({
        "doc_id": "construction_quality",
        "version_id": "revised_2019_04_23",
        "source_url": docs["construction_quality"]["source_url"],
        "local_html": os.path.relpath(b_out, ROOT).replace("\\", "/"),
        "local_html_href": os.path.basename(b_out),
        "local_html_sha256": sha256_file(b_out),
        "pdf_href": os.path.relpath(os.path.join(ROOT, b_pdf), LOCATORS).replace("\\", "/"),
        "anchors": b_anchors,
        "errors": b_errors,
    })

    # C（决定正文，无条号）
    c_lines = open(os.path.join(CORPUS, "text_rail_quality_amendment.txt"), encoding="utf-8").read().splitlines()
    c_groups = [{
        "anchor": "decision",
        "doc_id": "rail_quality_amendment",
        "version_id": "2021_order_35",
        "article_id": None,
        "article_no": "修改决定",
        "sha256": hashlib.sha256("\n".join(c_lines).encode("utf-8")).hexdigest(),
        "paragraphs": [{"text": line} for line in c_lines if line.strip()],
    }]
    c_out = os.path.join(LOCATORS, "rail_quality_amendment.locator.html")
    c_anchors, c_errors = annotate(a_html, c_out, c_groups, "交通运输部令2021年第35号修改决定")
    result["documents"].append({
        "doc_id": "rail_quality_amendment",
        "version_id": "2021_order_35",
        "source_url": docs["rail_quality_amendment"]["source_url"],
        "local_html": os.path.relpath(c_out, ROOT).replace("\\", "/"),
        "local_html_href": os.path.basename(c_out),
        "local_html_sha256": sha256_file(c_out),
        "anchors": c_anchors,
        "errors": c_errors,
    })

    for doc in result["documents"]:
        for anchor in doc["anchors"]:
            anchor["href"] = "%s#%s" % (doc["local_html_href"], anchor["anchor"])
            if doc.get("pdf_href") and anchor.get("pdf_page"):
                anchor["pdf_href"] = "%s#page=%s" % (doc["pdf_href"], anchor["pdf_page"])
            else:
                anchor["pdf_href"] = None

    with open(os.path.join(LOCATORS, "index.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    html_lines = [
        "<!DOCTYPE html>",
        "<html lang='zh-CN'><head><meta charset='utf-8'><title>HCS 原文定位索引</title>",
        "<style>body{font-family:sans-serif;max-width:1000px;margin:24px auto;line-height:1.8}"
        "li{margin:4px 0}a{color:#0b57d0}</style></head><body>",
        "<h1>HCS 任务A 原文定位索引</h1>",
        "<p>点击条号打开本地原文副本并跳到对应条款；本地副本由官方公开页面生成，条文文字未改动。</p>",
    ]
    for doc in result["documents"]:
        html_lines.append("<h2>%s / %s</h2><ul>" % (doc["doc_id"], doc["version_id"]))
        for anchor in doc["anchors"]:
            href = doc["local_html_href"] + "#" + anchor["anchor"]
            html_lines.append("<li><a href='%s'>%s</a> (id=%s)</li>" % (
                href, anchor["article_no"] or anchor["anchor"], anchor["anchor"]))
        html_lines.append("</ul>")
    html_lines.append("</body></html>")
    with open(os.path.join(LOCATORS, "index.html"), "w", encoding="utf-8") as f:
        f.write("\n".join(html_lines))

    errors = sum(len(d["errors"]) for d in result["documents"])
    print("locator documents=%d anchors=%d errors=%d" % (
        len(result["documents"]), sum(len(d["anchors"]) for d in result["documents"]), errors))
    for doc in result["documents"]:
        for err in doc["errors"][:5]:
            print("  WARN", doc["doc_id"], err[:160])
    if errors:
        sys.exit(2)


if __name__ == "__main__":
    main()