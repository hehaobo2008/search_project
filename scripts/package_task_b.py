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
manifest = json.load(open(os.path.join(ROOT, "logs", "task_b", "run_manifest.json"), encoding="utf-8"))
run_id = manifest["run_id"]
out_dir = os.path.join(DIST, "taskB_%s" % run_id)
if os.path.exists(out_dir):
    shutil.rmtree(out_dir)
os.makedirs(out_dir)


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def copy(rel):
    src = os.path.join(ROOT, rel)
    if not os.path.exists(src):
        return False
    dst = os.path.join(out_dir, rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)
    return True


included = []
for folder, exts in [("scripts", (".py",)), ("tests", (".py",)), ("config", (".json",)),
                     ("data", (".jsonl",))]:
    for name in sorted(os.listdir(os.path.join(ROOT, folder))):
        if name.endswith(exts):
            rel = "%s/%s" % (folder, name)
            if copy(rel):
                included.append(rel)

for rel in [
    "README.md",
    "reports/task_b_dev_report.md",
    "reports/task_b_dev_results.json",
    "reports/task_b_freeze_protocol.md",
    "reports/task_b_test_result.json",
    "reports/RESULTS_taskB_filled.md",
    "reports/task_b_evidence_index.md",
    "work/models/bge-small-zh-v1.5/MODEL_MANIFEST.json",
    "logs/task_b/run_manifest.json",
]:
    if copy(rel):
        included.append(rel)

run_log_dir = os.path.join(ROOT, "logs", "task_b", "runs", run_id)
for name in sorted(os.listdir(run_log_dir)):
    rel = "logs/task_b/runs/%s/%s" % (run_id, name)
    if copy(rel):
        included.append(rel)

model = json.load(open(os.path.join(ROOT, "work", "models", "bge-small-zh-v1.5",
                                    "MODEL_MANIFEST.json"), encoding="utf-8"))
onnx = next(f for f in model["files"] if f["file"] == "onnx/model.onnx")
notes = """# HCS 任务B 复验包说明（开发集探索）

- 打包时间：%s
- run_id：`%s`
- 闸门状态：任务A人工核验 H01-H08 **尚未签字**；任务B冻结测试 **未标注、未运行**。本包不声明任务B独立测试成绩。

## 包含

- `scripts/`：检索、评估、模型校验、任务B流水线、打包脚本
- `tests/`：任务A与任务B回归测试
- `config/`：任务B配置与任务A版本锁定
- `data/`：18 道开发题（含 gold 草案）、20 道冻结候选（unlabeled）
- `reports/`：开发集报告、逐题结果、冻结协议、任务B测试结果、RESULTS、证据索引
- `logs/task_b/runs/%s/`：check_model、eval_dev、run_tests、check_freeze 四步独立日志与 run_manifest
- `work/models/bge-small-zh-v1.5/MODEL_MANIFEST.json`：模型文件 hash、来源、许可

## 未包含

- 模型权重（约95MB）与缓存：需从 ModelScope 重新下载并核对 hash
- 法规原文、`corpus/articles.jsonl`、`corpus/text_*.txt`、locators 全文副本

## 模型获取与复验

1. 从 `https://www.modelscope.cn/models/Xenova/bge-small-zh-v1.5` 下载以下文件到 `work/models/bge-small-zh-v1.5/`：
   - `onnx/model.onnx`（SHA-256 `%s`）
   - `tokenizer.json`、`config.json`、`tokenizer_config.json`、`special_tokens_map.json`、`vocab.txt`
2. 运行 `python scripts/check_model.py`，确认文件 hash 与 `MODEL_MANIFEST.json` 一致。
3. 运行 `python scripts/task_b_pipeline.py`；确认四步退出码与 `logs/task_b/runs/<run_id>/` 日志。
4. 运行 `python scripts/run_task_b_tests.py`，对照 `reports/task_b_test_result.json`。
5. 冻结测试前，按 `reports/task_b_freeze_protocol.md` 人工标注 20 道候选；未标注前不得报告独立测试成绩。

## 边界

- 开发集 gold 由本次会话构造，尚未双人独立标注；报告仅作探索。
- 补证组与 Top7 开发集 Hit 相同，未观察到额外收益；样本小。
- 未做端侧转换、手机性能、真实用户试用、显著性检验。
""" % (datetime.now().astimezone().isoformat(), run_id, run_id, onnx["sha256"])
with open(os.path.join(out_dir, "PACKAGE_NOTES.md"), "w", encoding="utf-8") as f:
    f.write(notes)
included.append("PACKAGE_NOTES.md")

sums = ["%s  %s" % (sha(os.path.join(out_dir, rel)), rel.replace("\\", "/"))
        for rel in sorted(included)]
with open(os.path.join(out_dir, "SHA256SUMS.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(sums) + "\n")

zip_path = shutil.make_archive(os.path.join(DIST, "taskB_%s" % run_id), "zip",
                               root_dir=DIST, base_dir="taskB_%s" % run_id)
zip_hash = sha(zip_path)
with open(zip_path + ".sha256", "w", encoding="utf-8") as f:
    f.write("%s  %s\n" % (zip_hash, os.path.basename(zip_path)))
print("package_dir=%s" % os.path.relpath(out_dir, ROOT))
print("files=%d" % len(included))
print("zip=%s" % os.path.relpath(zip_path, ROOT))
print("zip_sha256=%s" % zip_hash)
print("zip_bytes=%d" % os.path.getsize(zip_path))