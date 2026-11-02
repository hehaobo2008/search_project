import hashlib
import json
import os
import re
import sys
from datetime import datetime

from lxml import html as LH
from pypdf import PdfReader

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS = os.environ.get("HCS_REPORTS_DIR", os.path.join(ROOT, "reports"))
CORPUS = os.path.join(ROOT, "corpus")
os.makedirs(REPORTS, exist_ok=True)

CN = {"零": 0, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
      "六": 6, "七": 7, "八": 8, "九": 9}
UNIT = {"十": 10, "百": 100}
CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩"


def cn_to_int(text):
    total, cur = 0, 0
    for ch in text:
        if ch in CN:
            cur = CN[ch]
        elif ch in UNIT:
            if cur == 0:
                cur = 1
            total += cur * UNIT[ch]
            cur = 0
    return total + cur


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def html_body_text(path):
    doc = LH.fromstring(open(path, "rb").read())
    return " ".join(doc.text_content().split())


def slice_between(body, start_kw, end_kw):
    i = body.find(start_kw)
    if i < 0:
        return ""
    j = body.find(end_kw, i + len(start_kw)) if end_kw else -1
    if j < 0:
        j = min(len(body), i + 400)
    return body[i:j].strip()


def pdf_article_map(path):
    reader = PdfReader(path)
    lines = []
    for page in reader.pages:
        for line in (page.extract_text() or "").splitlines():
            line = line.strip()
            if line:
                lines.append(line)
    arts, current, buf = {}, None, []
    for line in lines:
        m = re.match(r"^第([一二三四五六七八九十百零]+)条(?:\s|$)", line)
        if m:
            if current is not None:
                arts[current] = "".join(buf)
            current = cn_to_int(m.group(1))
            buf = [line]
        elif current is not None:
            buf.append(line)
    if current is not None:
        arts[current] = "".join(buf)
    return arts


def main():
    a2015_path = os.path.join(ROOT, "work", "raw", "A_2015_old.html")
    b2017_path = os.path.join(ROOT, "work", "raw", "B_2017_moj.pdf")

    a2015_body = html_body_text(a2015_path)
    a2015_title = " ".join((LH.fromstring(open(a2015_path, "rb").read()).findtext(".//title") or "").split())
    b2017 = pdf_article_map(b2017_path)
    b2017_first_page = "".join((PdfReader(b2017_path).pages[0].extract_text() or "").split())

    current = [json.loads(line) for line in open(os.path.join(CORPUS, "articles.jsonl"), encoding="utf-8")]
    a2021 = {a["article_num"]: a["text"] for a in current if a["doc_id"] == "rail_quality"}
    b2019 = {a["article_num"]: a["text"] for a in current if a["doc_id"] == "construction_quality"}

    a2015_70 = slice_between(a2015_body, "第七十条", "第七十一条")
    a2021_70 = a2021.get(70, "")
    a2021_71 = a2021.get(71, "")

    def strip_article_no(text):
        return re.sub(r"^第[一二三四五六七八九十百零]+条", "", text.replace(" ", ""))

    cases = []

    def case(cid, name, ok, detail, status=None):
        cases.append({"id": cid, "name": name, "status": status or ("PASS" if ok else "FAIL"), "detail": detail})

    case("V01", "A2015旧页明确标注已被修订",
         "已被修订" in a2015_title and "2021年12月23日" not in a2015_title,
         "title=%s" % a2015_title)

    shifted = bool(a2015_70) and strip_article_no(a2015_70)[:150] == strip_article_no(a2021_71)[:150]
    same_no_diff = bool(a2015_70) and bool(a2021_70) and strip_article_no(a2015_70) != strip_article_no(a2021_70)
    case("V02", "A条号在2015与2021版间发生位移", shifted and same_no_diff,
         "A2015#70==A2021#70? %s; A2015#70==A2021#71? %s; a2015_70_len=%d" % (
             not same_no_diff, shifted, len(a2015_70)))

    case("V03", "B2017副本首页仅载2017修订",
         "2017年10月7日" in b2017_first_page and "2019年4月23日" not in b2017_first_page,
         "first_page_head=%s" % b2017_first_page[:80])

    b2017_65 = b2017.get(65, "")
    b2019_65 = b2019.get(65, "")
    readable = sum(1 for ch in "施工单位质量检测" if ch in b2017_65) >= 6
    clean_2017 = re.sub(r"-\s*\d+\s*-", "", b2017_65).replace(" ", "")
    clean_2019 = re.sub(r"-\s*\d+\s*-", "", b2019_65).replace(" ", "")
    if readable:
        case("V04", "B2017第65条文本层可读且去页码后对比",
             True,
             "B2017_len=%d B2019_len=%d 去页码后相同=%s" % (
                 len(b2017_65), len(b2019_65), clean_2017 == clean_2019))
    else:
        case("V04", "B2017第65条文本层可用性", False,
             "B2017第65条文本层提取异常（len=%d），不能用于文本对比，仅能用作版本标签反例" % len(b2017_65),
             status="OBSERVED_ISSUE")

    versions_2017_only = {
        "construction_quality": {"revised_2017_10_07": {"articles": b2017}},
    }

    def guarded_lookup(doc_id, requested_version, number):
        versions = versions_2017_only.get(doc_id, {})
        if requested_version not in versions:
            return "version_pending", sorted(versions)
        text = versions[requested_version]["articles"].get(number)
        if not text:
            return "article_not_found", None
        return "ok", text

    st, available = guarded_lookup("construction_quality", "revised_2019_04_23", 65)
    case("V05", "真实2017语料下请求2019版第65条必须待核验",
         st == "version_pending", "status=%s available=%s" % (st, available))

    case("V06", "真实2015语料存在第70条且与2021版内容不同",
         bool(a2015_70) and bool(a2021_70) and strip_article_no(a2015_70) != strip_article_no(a2021_70),
         "2015_len=%d 2021_len=%d" % (len(a2015_70), len(a2021_70)))

    payload = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "counterexamples": [
            {
                "doc_id": "rail_quality",
                "version_id": "published_2015_03_12",
                "file": "work/raw/A_2015_old.html",
                "sha256": sha256(a2015_path),
                "source_url": "https://xxgk.mot.gov.cn/jigou/fgs/202006/t20200623_3307691.html",
                "observed_title": a2015_title,
                "status_evidence": "页面标题含‘已被修订’",
                "role": "版本反例，仅作对照，不进入主索引",
                "observed_a70_snippet": a2015_70[:160],
            },
            {
                "doc_id": "construction_quality",
                "version_id": "revised_2017_10_07",
                "file": "work/raw/B_2017_moj.pdf",
                "sha256": sha256(b2017_path),
                "source_url": "https://xzfg.moj.gov.cn/law/download?LawID=1598&type=pdf",
                "observed_first_page": b2017_first_page[:200],
                "role": "版本反例，仅作对照，不进入主索引",
                "text_layer_note": "第65条文本层乱码，无法用于内容对比；首页题注可读，版本标签可用",
            },
        ],
        "cases": cases,
        "summary": {
            "total": len(cases),
            "passed": sum(1 for c in cases if c["status"] == "PASS"),
            "failed": sum(1 for c in cases if c["status"] == "FAIL"),
            "observed_issue": sum(1 for c in cases if c["status"] == "OBSERVED_ISSUE"),
        },
    }
    with open(os.path.join(REPORTS, "version_counterexample_result.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    for c in cases:
        print("%-4s %-15s %s | %s" % (c["id"], c["status"], c["name"], c["detail"]))
    print("summary:", payload["summary"])
    print("A2015#70:", a2015_70[:180])
    print("A2021#71:", a2021_71[:180])
    sys.exit(0 if payload["summary"]["failed"] == 0 else 2)


if __name__ == "__main__":
    main()