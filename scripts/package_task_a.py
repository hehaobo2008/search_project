import hashlib
import json
import os
import shutil
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "dist")
os.makedirs(DIST, exist_ok=True)

manifest = json.load(open(os.path.join(ROOT, "logs", "run_manifest.json"), encoding="utf-8"))
run_id = manifest["run_id"]
out_dir = os.path.join(DIST, "taskA_%s" % run_id)
if os.path.exists(out_dir):
    shutil.rmtree(out_dir)
os.makedirs(out_dir)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def copy_file(rel):
    src = os.path.join(ROOT, rel)
    if not os.path.exists(src):
        return False
    dst = os.path.join(out_dir, rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)
    return True


included = []
for pattern_dir, exts in [
    ("scripts", (".py",)),
    ("tests", (".py",)),
    ("reports", (".md", ".json")),
]:
    for name in sorted(os.listdir(os.path.join(ROOT, pattern_dir))):
        if name.endswith(exts):
            rel = "%s/%s" % (pattern_dir, name)
            if copy_file(rel):
                included.append(rel)

for rel in ["README.md", "config/version_pins.json", "corpus/docs_manifest.json", "corpus/relations.jsonl",
            "corpus/relation_diagnostics.json", "locators/index.json", "locators/index.html",
            "logs/run_manifest.json", "logs/tests_full.log"]:
    if copy_file(rel):
        included.append(rel)

run_log_dir = os.path.join(ROOT, "logs", "runs", run_id)
for name in sorted(os.listdir(run_log_dir)):
    rel = "logs/runs/%s/%s" % (run_id, name)
    if copy_file(rel):
        included.append(rel)

# 排除全文的文件只记录 hash，便于确认可重建
excluded_hashes = {}
for rel in ["corpus/articles.jsonl", "corpus/text_rail_quality.txt",
            "corpus/text_construction_quality.txt", "corpus/text_rail_quality_amendment.txt",
            "locators/rail_quality.locator.html", "locators/construction_quality.locator.html",
            "locators/rail_quality_amendment.locator.html"]:
    path = os.path.join(ROOT, rel)
    if os.path.exists(path):
        excluded_hashes[rel] = {"sha256": sha256(path), "bytes": os.path.getsize(path)}
with open(os.path.join(out_dir, "corpus", "excluded_text_hashes.json"), "w", encoding="utf-8") as f:
    json.dump({
        "note": "以下文件含法规全文或派生的全文副本，未随复验包分发；hash用于确认从官方来源重建后与本次一致。",
        "files": excluded_hashes,
    }, f, ensure_ascii=False, indent=2)
included.append("corpus/excluded_text_hashes.json")

sources = []
for doc in json.load(open(os.path.join(ROOT, "corpus", "docs_manifest.json"), encoding="utf-8"))["documents"]:
    sources.append("- %s / %s：%s（文件SHA-256 `%s`）" % (
        doc["doc_id"], doc["version_id"], doc["source_url"], doc["file_sha256"]))

notes = """# HCS 任务A 复验包说明

- 打包时间：%s
- 流水线 run_id：`%s`
- 语言/运行时：Python；依赖 pypdf、lxml（版本见 `logs/runs/%s/env_check.log`）
- 任务A闸门状态：**未通过（待人工 H01-H08）**；本包不声明闸门通过。

## 包含

- `config/version_pins.json`：引用目标版本显式锁定配置（正式入口读取）
- `scripts/`：语料构建、定位页生成、关系抽取、四类校验、测试运行、打包脚本
- `tests/`：17 项回归测试（日志、退出码、负控、回跳、版本歧义、B31、语料与关系）
- `reports/`：任务A结果、回跳结果、版本反例结果、测试汇总、人工清单、证据索引、RESULTS
- `logs/runs/%s/`：本次运行每一步的独立日志与 `run_manifest.json`
- `logs/tests_full.log`：独立完整测试输出
- `locators/index.json`、`locators/index.html`：本地锚点索引（HTML 副本本身含全文，未打包）

## 未包含（合规）

法规原文、`corpus/articles.jsonl`、`corpus/text_*.txt`、`locators/*.locator.html` 含全文或全文派生内容，未随包分发。`corpus/excluded_text_hashes.json` 记录其 SHA-256，便于确认从官方来源重建后一致。

## 复验步骤

1. 从以下官方入口重新取得原文，保存在 `work/raw/`，核对 `corpus/docs_manifest.json` 中的 SHA-256。若 hash 不同，记录为来源更新，不得静默替换锁定版本。
%s
2. 运行 `python scripts/build_corpus.py && python scripts/build_locators.py && python scripts/build_relations.py`。
3. 运行 `python scripts/run_pipeline.py`；确认每一步退出码与 `logs/runs/<run_id>/` 日志。
4. 运行 `python -m unittest discover -s tests -v`；对照 `logs/tests_full.log`。
5. 打开 `reports/human_review_checklist.md` 中的 `../locators/...#art-N` 链接，完成 H01-H08 人工核对并签字。

## 证据边界

- 自动用例、回跳校验和回归测试通过，不等于人工闸门通过。
- 报告不包含虚构截图、成绩或 commit；本目录未初始化 Git。
- 任务B（中文检索与同预算消融）未执行。
""" % (datetime.now().astimezone().isoformat(), run_id, run_id, run_id, "\n".join(sources))
with open(os.path.join(out_dir, "PACKAGE_NOTES.md"), "w", encoding="utf-8") as f:
    f.write(notes)
included.append("PACKAGE_NOTES.md")

sums = []
for rel in sorted(included):
    path = os.path.join(out_dir, rel)
    sums.append("%s  %s" % (sha256(path), rel.replace("\\", "/")))
with open(os.path.join(out_dir, "SHA256SUMS.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(sums) + "\n")

zip_base = os.path.join(DIST, "taskA_%s" % run_id)
zip_path = shutil.make_archive(zip_base, "zip", root_dir=DIST, base_dir="taskA_%s" % run_id)
zip_hash = sha256(zip_path)
with open(zip_path + ".sha256", "w", encoding="utf-8") as f:
    f.write("%s  %s\n" % (zip_hash, os.path.basename(zip_path)))

print("package_dir=%s" % os.path.relpath(out_dir, ROOT))
print("files=%d" % len(included))
print("zip=%s" % os.path.relpath(zip_path, ROOT))
print("zip_sha256=%s" % zip_hash)
print("zip_bytes=%d" % os.path.getsize(zip_path))