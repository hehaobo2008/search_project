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
RAW = os.path.join(ROOT, "work", "raw")
CORPUS = os.path.join(ROOT, "corpus")
os.makedirs(CORPUS, exist_ok=True)

CN_DIGITS = {
    "零": 0, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
    "六": 6, "七": 7, "八": 8, "九": 9,
}
CN_UNITS = {"十": 10, "百": 100}


def cn_to_int(text):
    total, current = 0, 0
    for ch in text:
        if ch in CN_DIGITS:
            current = CN_DIGITS[ch]
        elif ch in CN_UNITS:
            unit = CN_UNITS[ch]
            if current == 0:
                current = 1
            total += current * unit
            current = 0
        else:
            raise ValueError("unexpected chinese numeral: %r" % text)
    return total + current


def norm(text):
    return " ".join(text.split())


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def retrieved_at(path):
    ts = datetime.fromtimestamp(os.path.getmtime(path)).astimezone()
    return ts.isoformat()


def read_blocks(path):
    doc = LH.fromstring(open(path, "rb").read())
    blocks = []
    for el in doc.iter():
        if not isinstance(el.tag, str) or el.tag not in ("p", "h2", "h3", "h4"):
            continue
        text = norm(el.text_content())
        if text:
            blocks.append({"tag": el.tag, "text": text})
    return blocks


def find_index(blocks, predicate, start=0):
    for i in range(start, len(blocks)):
        if predicate(blocks[i]["text"]):
            return i
    raise LookupError("block boundary not found")


def build_document(doc_id, version_id, blocks, begin, end_inclusive):
    slice_blocks = blocks[begin:end_inclusive + 1]
    full_text = ""
    offsets = []
    for b in slice_blocks:
        if full_text:
            full_text += "\n"
        offsets.append((len(full_text), len(full_text) + len(b["text"]), b))
        full_text += b["text"]
    return {
        "doc_id": doc_id,
        "version_id": version_id,
        "blocks": slice_blocks,
        "offsets": offsets,
        "full_text": full_text,
    }


ARTICLE_RE = re.compile(r"^第([一二三四五六七八九十百零]+)条(?:\s|$)")
CHAPTER_RE = re.compile(r"^第([一二三四五六七八九十百零]+)章(?:\s|$)")
SECTION_RE = re.compile(r"^第([一二三四五六七八九十百零]+)节(?:\s|$)")


def parse_articles(doc, source_url, anchor_prefix):
    articles = []
    current = None
    chapter = ""
    section = ""
    for start, end, block in doc["offsets"]:
        text = block["text"]
        if CHAPTER_RE.match(text):
            chapter = text
            section = ""
            current = None
            continue
        if SECTION_RE.match(text):
            section = text
            current = None
            continue
        m = ARTICLE_RE.match(text)
        if m:
            number = cn_to_int(m.group(1))
            current = {
                "doc_id": doc["doc_id"],
                "version_id": doc["version_id"],
                "article_id": "%s:art-%d" % (doc["doc_id"], number),
                "article_no": "第%s条" % m.group(1),
                "article_num": number,
                "chapter": chapter,
                "section": section,
                "paragraphs": [],
                "text": "",
                "start": start,
                "end": end,
                "source_url": source_url,
                "anchor": "%s%d" % (anchor_prefix, number),
                "pdf_page_start": None,
                "pdf_pages_all": [],
                "review_status": "pending_human",
            }
            articles.append(current)
        if current is None:
            continue
        current["paragraphs"].append({
            "text": text,
            "start": start,
            "end": end,
        })
        current["end"] = end
    for art in articles:
        art["text"] = "\n".join(p["text"] for p in art["paragraphs"])
        art["sha256"] = hashlib.sha256(art["text"].encode("utf-8")).hexdigest()
        art["span_check"] = doc["full_text"][art["start"]:art["end"]] == art["text"]
        art["para_count"] = len(art["paragraphs"])
    return articles


def pdf_page_texts(path):
    reader = PdfReader(path)
    return ["".join((page.extract_text() or "").split()) for page in reader.pages]


def locate_in_pdf(article, pages, step=16, min_frag=8):
    compact = "".join(article["text"].split())
    probe = compact[:24]
    page_start = None
    for idx, page in enumerate(pages, start=1):
        if probe in page:
            page_start = idx
            break
    if page_start is None:
        return None, []
    pages_all = [page_start]
    cursor = page_start
    for k in range(step, len(compact), step):
        frag = compact[k:k + step]
        if len(frag) < min_frag:
            continue
        for idx in range(cursor, len(pages) + 1):
            if frag in pages[idx - 1]:
                if idx != cursor:
                    cursor = idx
                    pages_all.append(idx)
                break
    return page_start, pages_all


def main():
    A_HTML = os.path.join(RAW, "A_amend.html")
    A_PDF = os.path.join(RAW, "A_spec.pdf")
    B_HTML = os.path.join(RAW, "B_official.html")
    B_PDF = os.path.join(RAW, "B_copy_cas.pdf")

    a_blocks = read_blocks(A_HTML)
    b_blocks = read_blocks(B_HTML)

    a_start = find_index(a_blocks, lambda t: t == "铁路建设工程质量监督管理规定")
    a_end = find_index(a_blocks, lambda t: "相关解读" in t, a_start) - 1
    c_start = find_index(a_blocks, lambda t: t == "交通运输部关于修改《铁路建设工程质量监督管理规定》的决定")
    c_end = find_index(a_blocks, lambda t: "重新公布。" in t, c_start)
    b_start = find_index(b_blocks, lambda t: t == "建设工程质量管理条例")
    b_end = find_index(b_blocks, lambda t: t.startswith("第八十二条"), b_start)

    docs = {
        "A": build_document("rail_quality", "amended_2021_12_23", a_blocks, a_start, a_end),
        "B": build_document("construction_quality", "revised_2019_04_23", b_blocks, b_start, b_end),
        "C": build_document("rail_quality_amendment", "2021_order_35", a_blocks, c_start, c_end),
    }

    source_urls = {
        "A": "https://xxgk.mot.gov.cn/2020/jigou/fgs/202202/t20220225_3643089.html",
        "B": "https://www.samr.gov.cn/zw/zfxxgk/fdzdgknr/bgt/art/2023/art_e42ecef60e9146af83cf9846821fac6c.html",
        "C": "https://xxgk.mot.gov.cn/2020/jigou/fgs/202202/t20220225_3643089.html",
    }
    anchor_prefix = {"A": "art-", "B": "art-", "C": "dec-"}
    pdf_pages = {"A": pdf_page_texts(A_PDF), "B": pdf_page_texts(B_PDF)}

    all_articles = []
    for key in ("A", "B", "C"):
        doc = docs[key]
        arts = parse_articles(doc, source_urls[key], anchor_prefix[key])
        if key in pdf_pages:
            for art in arts:
                page_start, pages_all = locate_in_pdf(art, pdf_pages[key])
                art["pdf_page_start"] = page_start
                art["pdf_pages_all"] = pages_all
                art["pdf_anchor_status"] = "auto_text_layer_match_pending_human_visual"
        all_articles.extend(arts)
        with open(os.path.join(CORPUS, "text_%s.txt" % doc["doc_id"]), "w", encoding="utf-8") as f:
            f.write(doc["full_text"])
        print("%s blocks=%d articles=%d chars=%d span_ok=%d" % (
            key, len(doc["blocks"]), len(arts), len(doc["full_text"]),
            sum(1 for a in arts if a["span_check"])))

    manifest = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "normalization_rule": (
            "正文块按DOM顺序取p/h2/h3/h4；块内连续Unicode空白折叠为单个半角空格并去首尾；"
            "块间以单个换行符连接；不做繁简、大小写或标点转换。偏移单位为Python字符串Unicode码点，"
            "区间左闭右开，基于各文档独立full_text。"
        ),
        "documents": [
            {
                "doc_id": "rail_quality",
                "version_id": "amended_2021_12_23",
                "title": "铁路建设工程质量监督管理规定",
                "role": "实体法规A（2021修正并重新公布正文）",
                "publisher": "交通运输部",
                "published": "2015-03-12",
                "amended": "2021-12-23",
                "effective": "2015-05-01",
                "version_basis": "题注：2015年3月12日交通运输部公布 根据2021年12月23日交通运输部《关于修改〈铁路建设工程质量监督管理规定〉的决定》修正；第七十五条载施行日期",
                "source_url": source_urls["A"],
                "source_type": "official_html_same_page_as_C",
                "file": "work/raw/A_amend.html",
                "file_sha256": sha256_file(A_HTML),
                "retrieved_at": retrieved_at(A_HTML),
                "format": "html",
                "locator_rule": "HTML逻辑锚点art-N + 字符偏移；物理页锚点来自交通运输部规范PDF文本层自动匹配，尚待人工视觉确认",
                "rendering": {
                    "file": "work/raw/A_spec.pdf",
                    "sha256": sha256_file(A_PDF),
                    "pages": len(pdf_pages["A"]),
                    "note": "PDF共25页，与HTML同为2021修正版；页锚点为自动文本层匹配",
                },
                "shared_source_file_with": "rail_quality_amendment",
                "review_status": "pending_human",
            },
            {
                "doc_id": "construction_quality",
                "version_id": "revised_2019_04_23",
                "title": "建设工程质量管理条例",
                "role": "实体法规B（2019第二次修订）",
                "publisher": "国务院",
                "published": "2000-01-30",
                "amended": "2019-04-23",
                "effective": "2000-01-30",
                "version_basis": "题注：2000年1月30日国务院令第279号发布；2017年10月7日第一次修订；2019年4月23日第二次修订；第八十二条载自发布之日起施行",
                "source_url": source_urls["B"],
                "source_type": "official_html",
                "file": "work/raw/B_official.html",
                "file_sha256": sha256_file(B_HTML),
                "retrieved_at": retrieved_at(B_HTML),
                "format": "html",
                "locator_rule": "HTML逻辑锚点art-N + 字符偏移；HTML无固有页码，不编造PDF页码",
                "rendering": {
                    "file": "work/raw/B_copy_cas.pdf",
                    "sha256": sha256_file(B_PDF),
                    "pages": len(pdf_pages["B"]),
                    "note": "中国科学院集成电路创新研究院公开副本，非原发布机关版本，仅作PDF回跳测试；页锚点为自动文本层匹配",
                },
                "review_status": "pending_human",
            },
            {
                "doc_id": "rail_quality_amendment",
                "version_id": "2021_order_35",
                "title": "交通运输部关于修改《铁路建设工程质量监督管理规定》的决定",
                "role": "版本关系材料C（修改决定，非第三套实体规则）",
                "publisher": "交通运输部",
                "published": "2021-12-23",
                "amended": None,
                "effective": "2021-12-23",
                "version_basis": "交通运输部令2021年第35号；正文载2021年12月17日第32次部务会议通过，2021年12月23日公布并施行，修改第69条并增设第70条后重新公布",
                "source_url": source_urls["C"],
                "source_type": "official_html_shared_page_with_A",
                "file": "work/raw/A_amend.html",
                "file_sha256": sha256_file(A_HTML),
                "retrieved_at": retrieved_at(A_HTML),
                "format": "html",
                "locator_rule": "HTML逻辑锚点dec-N + 字符偏移；与A共页，导入时分离决定正文与重新公布正文，不重复计数",
                "shared_source_file_with": "rail_quality",
                "review_status": "pending_human",
            },
        ],
        "artifact_hashes": {
            "work/raw/A_amend.html": sha256_file(A_HTML),
            "work/raw/A_spec.pdf": sha256_file(A_PDF),
            "work/raw/B_official.html": sha256_file(B_HTML),
            "work/raw/B_copy_cas.pdf": sha256_file(B_PDF),
        },
        "counts": {"documents": 3, "distinct_source_files": 4},
    }

    for doc in manifest["documents"]:
        if doc["doc_id"] == "construction_quality":
            doc["legacy_records"] = [{
                "record_id": "B31-page",
                "record": "B29及B31在物理第7页、B31续至第8页",
                "source": "HCS_CODEARTS_HANDOFF_20261102/MATERIALS_MANIFEST.md（2026-11-02整理）",
                "status": "superseded",
                "observed": "CAS副本PDF文本层第7页完整包含B31句尾‘进行检测。’；第8页首条为B32",
                "evidence": "work/raw/B_copy_cas.pdf 第7/8页；logs/pdf_page_detail.log",
                "corrected_at": datetime.now().astimezone().isoformat(),
                "correction_reason": "按实际PDF文本层逐页核对，B31未跨页；保留旧记录与修正原因供复验追溯，旧记录不再作为事实使用",
            }]

    for art in all_articles:
        art["pdf_cross_page"] = len(art["pdf_pages_all"]) > 1
        if art["doc_id"] == "construction_quality" and art["article_num"] == 31:
            art["page_record_correction"] = {
                "legacy_record_id": "B31-page",
                "legacy": "B31续至第8页",
                "actual": "B31完整位于第7页，第8页首条为B32",
                "status": "corrected",
                "evidence": "work/raw/B_copy_cas.pdf 第7页页尾含‘进行检测。’；第8页首行为第三十二条",
                "reason": "旧记录与PDF文本层不符，按实际页位更正并保留旧记录",
            }

    with open(os.path.join(CORPUS, "docs_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    with open(os.path.join(CORPUS, "articles.jsonl"), "w", encoding="utf-8") as f:
        for art in all_articles:
            f.write(json.dumps(art, ensure_ascii=False) + "\n")

    print("manifest documents=%d articles=%d" % (len(manifest["documents"]), len(all_articles)))
    for key, doc in docs.items():
        arts = [a for a in all_articles if a["doc_id"] == doc["doc_id"]]
        nums = [a["article_num"] for a in arts]
        print("%s: first=%s last=%s continuous=%s" % (
            key, nums[0] if nums else None, nums[-1] if nums else None,
            nums == list(range(1, len(nums) + 1))))


if __name__ == "__main__":
    main()