import json
import locale
import os
import platform
import sys
from datetime import datetime, timezone, timedelta

info = {
    "python": sys.version,
    "executable": sys.executable,
    "platform": platform.platform(),
    "machine": platform.machine(),
    "cpu_count": os.cpu_count(),
    "default_encoding": locale.getpreferredencoding(False),
    "now_utc": datetime.now(timezone.utc).isoformat(),
    "now_local": datetime.now().astimezone().isoformat(),
    "tz": str(datetime.now().astimezone().tzinfo),
}
for mod in ["pdfplumber", "pypdf", "bs4", "lxml", "jieba", "hashlib"]:
    try:
        m = __import__(mod)
        info[mod] = getattr(m, "__version__", "installed")
    except Exception as e:
        info[mod] = "MISSING: %s" % e
print(json.dumps(info, ensure_ascii=False, indent=2))