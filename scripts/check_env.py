"""Kiem tra moi truong T05 va ghi bang chung vao reports/env_check.txt.

Chay: python scripts/check_env.py
Moi muc in [OK] hoac [THIEU]. File ket qua dung lam minh chung cho bao cao Tuan 1.
"""
import datetime
import platform
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
lines = []


def log(msg):
    print(msg)
    lines.append(msg)


def cmd_version(name, args):
    if not shutil.which(name):
        log(f"[THIEU] {name}: chua cai hoac khong co trong PATH")
        return False
    out = subprocess.run([name, *args], capture_output=True, text=True)
    log(f"[OK]    {name}: {(out.stdout or out.stderr).strip().splitlines()[0]}")
    return True


log(f"T05 env check - {datetime.datetime.now():%Y-%m-%d %H:%M}")
log(f"OS: {platform.platform()}")
log(f"Python: {sys.version.split()[0]} ({sys.executable})")
in_venv = sys.prefix != sys.base_prefix
log(f"[{'OK' if in_venv else 'CANH BAO'}]    virtualenv: {'dang bat' if in_venv else 'KHONG dung venv'}")
log("")

# 1) ML co dien: train nhanh 1 SVM tren vai payload de chac chan sklearn chay
try:
    import sklearn
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.svm import LinearSVC

    X = ["127.0.0.1", "8.8.8.8", "127.0.0.1; cat /etc/passwd",
         "8.8.8.8 | whoami", "google.com", "1.1.1.1 && id"]
    y = [0, 0, 1, 1, 0, 1]
    vec = TfidfVectorizer(analyzer="char", ngram_range=(1, 3))
    clf = LinearSVC().fit(vec.fit_transform(X), y)
    clf.predict(vec.transform(["10.0.0.1; ls"]))
    log(f"[OK]    scikit-learn {sklearn.__version__}: char n-gram TF-IDF + LinearSVC train + predict OK")
except Exception as e:  # noqa: BLE001
    log(f"[THIEU] scikit-learn: {e}")

for mod in ("numpy", "pandas", "matplotlib"):
    try:
        m = __import__(mod)
        log(f"[OK]    {mod} {m.__version__}")
    except Exception as e:  # noqa: BLE001
        log(f"[THIEU] {mod}: {e}")

# 2) DL: forward 1 batch qua CNN-1D muc ky tu
try:
    import torch
    import torch.nn as nn

    emb = nn.Embedding(128, 32)
    conv = nn.Conv1d(32, 64, kernel_size=3)
    x = torch.randint(0, 128, (4, 200))           # 4 payload, do dai 200 ky tu
    h = conv(emb(x).transpose(1, 2)).max(dim=2).values
    dev = "CUDA" if torch.cuda.is_available() else "CPU"
    log(f"[OK]    PyTorch {torch.__version__} ({dev}): CNN-1D forward OK, output {tuple(h.shape)}")
except Exception as e:  # noqa: BLE001
    log(f"[THIEU] PyTorch: {e}")

log("")
# 3) Cong cu ngoai
cmd_version("semgrep", ["--version"])
cmd_version("git", ["--version"])
if cmd_version("docker", ["--version"]):
    ok = subprocess.run(["docker", "info"], capture_output=True).returncode == 0
    log(f"[{'OK' if ok else 'THIEU'}]    docker daemon: {'dang chay' if ok else 'chua chay (mo Docker Desktop / sudo service docker start)'}")

out = ROOT / "reports" / "env_check.txt"
out.parent.mkdir(exist_ok=True)
out.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"\nDa ghi minh chung: {out.relative_to(ROOT)}")
