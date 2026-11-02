import hashlib
import json
import os
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "work", "raw")
MODEL_DIR = os.path.join(ROOT, "work", "models", "bge-small-zh-v1.5")
os.makedirs(RAW, exist_ok=True)

manifest = json.load(open(os.path.join(ROOT, "corpus", "docs_manifest.json"), encoding="utf-8"))
docs = {d["doc_id"]: d for d in manifest["documents"]}

RENDERING_URLS = {
    "work/raw/A_spec.pdf": "https://xxgk.mot.gov.cn/gz/202201/W020220110598772795306.pdf",
    "work/raw/B_copy_cas.pdf": "https://ic.cas.cn/yqjj/zcfg/202309/P020230908644966677848.pdf",
}

sources = {}
for doc_id, doc in docs.items():
    rel = doc["file"]
    sources[rel] = {"url": doc["source_url"], "sha256": doc["file_sha256"], "role": doc_id}
    rendering = doc.get("rendering")
    if rendering:
        sources[rendering["file"]] = {
            "url": RENDERING_URLS.get(rendering["file"], doc["source_url"]),
            "sha256": rendering["sha256"],
            "role": doc_id + " rendering",
        }

counter_path = os.path.join(ROOT, "reports", "version_counterexample_result.json")
if os.path.exists(counter_path):
    for item in json.load(open(counter_path, encoding="utf-8"))["counterexamples"]:
        sources[item["file"]] = {"url": item["source_url"], "sha256": item["sha256"],
                                 "role": "version counterexample"}

model_manifest_path = os.path.join(ROOT, "docs", "bge-small-zh-v1.5-MODEL_MANIFEST.json")
if not os.path.exists(model_manifest_path):
    model_manifest_path = os.path.join(ROOT, "work", "models", "bge-small-zh-v1.5",
                                       "MODEL_MANIFEST.json")
model_manifest = json.load(open(model_manifest_path, encoding="utf-8")) if os.path.exists(
    model_manifest_path) else None
MODEL_BASE = "https://www.modelscope.cn/models/Xenova/bge-small-zh-v1.5/resolve/master/"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url, path):
    request = urllib.request.Request(url, headers={"User-Agent": "HCS-repro/1.0"})
    with urllib.request.urlopen(request, timeout=120) as response, open(path, "wb") as out:
        while True:
            chunk = response.read(65536)
            if not chunk:
                break
            out.write(chunk)


def ensure(rel, url, expected_sha, role):
    path = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path):
        actual = sha256(path)
        if actual == expected_sha:
            print("OK       %s (%s)" % (rel, role))
            return True
        print("MISMATCH %s 现有文件与锁定版本不一致（可能来源已更新）" % rel)
        return False
    print("DOWNLOAD %s (%s)" % (rel, role))
    try:
        download(url, path)
    except Exception as exc:
        print("FAILED   %s: %s" % (rel, exc))
        return False
    actual = sha256(path)
    if actual != expected_sha:
        print("MISMATCH %s\n  期望 %s\n  实际 %s\n  不得静默替换锁定版本" % (rel, expected_sha, actual))
        return False
    print("OK       %s" % rel)
    return True


def main():
    include_model = "--model" in sys.argv
    ok = True
    for rel, spec in sorted(sources.items()):
        ok = ensure(rel, spec["url"], spec["sha256"], spec["role"]) and ok
    if include_model:
        if not model_manifest:
            print("MODEL MANIFEST MISSING")
            return 2
        for item in model_manifest["files"]:
            rel = os.path.join("work", "models", "bge-small-zh-v1.5", item["file"])
            url = MODEL_BASE + item["file"]
            ok = ensure(rel, url, item["sha256"], "bge-small-zh-v1.5") and ok
    else:
        print("模型权重未下载；需要时加 --model。清单见 MODEL_MANIFEST。")
    print("source_check all_ok=%s" % ok)
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())