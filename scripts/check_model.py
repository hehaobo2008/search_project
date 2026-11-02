import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(ROOT, "work", "models", "bge-small-zh-v1.5")
_MANIFEST_CANDIDATES = [
    os.path.join(ROOT, "docs", "bge-small-zh-v1.5-MODEL_MANIFEST.json"),
    os.path.join(MODEL_DIR, "MODEL_MANIFEST.json"),
]
manifest_path = next((p for p in _MANIFEST_CANDIDATES if os.path.exists(p)), None)
if manifest_path is None:
    print("MODEL_MANIFEST.json not found in docs/ or work/models/")
    sys.exit(2)
manifest = json.load(open(manifest_path, encoding="utf-8"))

failures = []
for item in manifest["files"]:
    path = os.path.join(MODEL_DIR, item["file"])
    if not os.path.exists(path):
        failures.append((item["file"], "missing", None, item["sha256"]))
        continue
    import hashlib
    digest = hashlib.sha256(open(path, "rb").read()).hexdigest()
    size = os.path.getsize(path)
    if digest != item["sha256"] or size != item["bytes"]:
        failures.append((item["file"], "hash_or_size", digest, item["sha256"]))

print("manifest=%s model_dir=%s files=%d license=%s" % (
    os.path.relpath(manifest_path, ROOT), os.path.relpath(MODEL_DIR, ROOT),
    len(manifest["files"]), manifest["license"]))
print("runtime=%s max_length=%s pooling=%s" % (
    manifest["runtime"], manifest["max_length"], manifest["pooling"]))
for f in failures:
    print("MISMATCH", f)
print("model_check failures=%d" % len(failures))
sys.exit(0 if not failures else 2)