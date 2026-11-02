import json
import os
import sys

from lxml import html as LH

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORPUS = os.path.join(ROOT, "corpus")
LOCATORS = os.path.join(ROOT, "locators")
REPORTS = os.environ.get("HCS_REPORTS_DIR", os.path.join(ROOT, "reports"))
os.makedirs(REPORTS, exist_ok=True)


def norm(text):
    return " ".join(text.split())


def load_articles():
    return [json.loads(line) for line in open(os.path.join(CORPUS, "articles.jsonl"), encoding="utf-8")]


def collect_elements(doc):
    ordered = []
    ids = {}
    parts = {}
    for pos, el in enumerate(doc.iter()):
        if not isinstance(el.tag, str):
            continue
        ordered.append((pos, el))
        anchor = el.get("id")
        if anchor:
            ids.setdefault(anchor, []).append(pos)
        part = el.get("data-article-part")
        if part:
            parts.setdefault(part, []).append(pos)
    by_pos = dict(ordered)
    return by_pos, ids, parts


def main():
    index = json.load(open(os.path.join(LOCATORS, "index.json"), encoding="utf-8"))
    articles = {(a["doc_id"], a["anchor"]): a for a in load_articles()}
    c_text = open(os.path.join(CORPUS, "text_rail_quality_amendment.txt"), encoding="utf-8").read()
    c_expected = "\n".join(line for line in c_text.splitlines() if line.strip())

    cases = []
    docs_cache = {}
    for doc in index["documents"]:
        local_html = os.path.join(LOCATORS, doc["local_html_href"])
        if not os.path.exists(local_html):
            cases.append({"doc_id": doc["doc_id"], "anchor": None, "status": "FAIL",
                          "detail": "local html missing: %s" % doc["local_html"]})
            continue
        if local_html not in docs_cache:
            root = LH.parse(local_html, LH.HTMLParser()).getroot()
            docs_cache[local_html] = collect_elements(root)
        by_pos, ids, parts = docs_cache[local_html]

        for anchor in doc["anchors"]:
            name = anchor["anchor"]
            positions = sorted(set(ids.get(name, []) + parts.get(name, [])))
            elements = [by_pos[p] for p in positions]
            actual = "\n".join(norm(el.text_content()) for el in elements)
            if name == "decision":
                expected = c_expected
            else:
                article = articles.get((doc["doc_id"], name))
                expected = article["text"] if article else None
            id_count = len(ids.get(name, []))
            href = "%s#%s" % (doc["local_html_href"], name)
            href_ok = (not os.path.isabs(doc["local_html_href"])
                       and not doc["local_html_href"].startswith("file:")
                       and not __import__("re").match(r"^[A-Za-z]:", doc["local_html_href"]))
            pdf_href = doc.get("pdf_href")
            pdf_ok = (pdf_href is None or (not os.path.isabs(pdf_href)
                                           and not pdf_href.startswith("file:")))
            ok = (id_count == 1 and expected is not None and actual == expected
                  and href_ok and pdf_ok)
            cases.append({
                "doc_id": doc["doc_id"],
                "anchor": name,
                "article_no": anchor["article_no"],
                "status": "PASS" if ok else "FAIL",
                "id_count": id_count,
                "parts": len(elements),
                "expected_len": len(expected) if expected else 0,
                "actual_len": len(actual),
                "href": href,
                "local_html": doc["local_html"],
                "pdf_href": pdf_href,
                "detail": "id_count=%d parts=%d text_match=%s" % (
                    id_count, len(elements), actual == expected),
            })

    failed = [c for c in cases if c["status"] == "FAIL"]
    key = {("%s:%s" % (c["doc_id"], c["anchor"])): c for c in cases}
    result = {
        "generated_at": __import__("datetime").datetime.now().astimezone().isoformat(),
        "cases": cases,
        "summary": {"total": len(cases), "passed": len(cases) - len(failed), "failed": len(failed)},
        "key_checks": {name: {
            "status": key.get(name, {}).get("status"),
            "href": key.get(name, {}).get("href"),
            "detail": key.get(name, {}).get("detail"),
        } for name in ["rail_quality:art-2", "rail_quality:art-30", "rail_quality:art-66",
                        "construction_quality:art-29", "construction_quality:art-31",
                        "construction_quality:art-65", "rail_quality_amendment:decision"]},
    }
    with open(os.path.join(REPORTS, "locator_result.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    for name in ["rail_quality:art-2", "rail_quality:art-30", "rail_quality:art-66",
                 "construction_quality:art-29", "construction_quality:art-31",
                 "construction_quality:art-65", "rail_quality_amendment:decision"]:
        c = key.get(name)
        print("%-28s %s | %s" % (name, c["status"] if c else "MISSING", c["detail"] if c else ""))
    print("locator checks total=%d pass=%d fail=%d" % (
        len(cases), result["summary"]["passed"], len(failed)))
    for c in failed[:10]:
        print("FAIL", c["doc_id"], c["anchor"], c.get("detail"))
    sys.exit(0 if not failed else 2)


if __name__ == "__main__":
    main()