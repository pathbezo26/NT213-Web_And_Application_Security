"""Tao data/processed/malicious.csv tu PayloadsAllTheThings (Command Injection/Intruder).
Chi xu ly van ban tren file co san, khong chay payload.
Dung: python scripts/build_malicious.py
"""
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "data/raw/payloadsallthethings/repo/Command Injection/Intruder"
OUT = ROOT / "data/processed/malicious.csv"
COLUMNS = ["payload_id", "input_text", "label", "source", "category", "group_id", "notes"]

HTML_ENTITY = re.compile(r"&(?:lt|gt|quot|amp|apos|nbsp|#\d+|#x[0-9a-fA-F]+);")
OPERATOR = re.compile(r"[;|&`$]|%0a", re.I)
WORD = re.compile(r"[A-Za-z]{2,}")


def categorize(text):
    # Nhan tho theo cau truc, uu tien:
    # newline_encoded > substitution > variable_expansion > pipe > separator
    if re.search(r"%0a", text, re.I):
        return "newline_encoded"
    if "`" in text or "$(" in text:
        return "substitution"
    if "$" in text:  # $IFS, ${...} - mo rong bien, khong phai thay the lenh
        return "variable_expansion"
    if "|" in text:
        return "pipe"
    return "separator"  # ; hoac &


def load_lines():
    # Bo trung theo chuoi khop hoan toan tren ca hai file, giu lan xuat hien dau
    seen, rows = set(), []
    for path in sorted(SRC_DIR.glob("*.txt")):
        text = path.read_text(encoding="utf-8", errors="replace")
        for line in text.split("\n"):
            line = line.rstrip("\r\n")  # khong strip khoang trang
            if not line.strip() or line in seen:
                continue
            seen.add(line)
            rows.append((line, path.name))
    return rows


def keep(text):
    return (
        len(text) > 3
        and not HTML_ENTITY.search(text)
        and OPERATOR.search(text) is not None
        and WORD.search(text) is not None
    )


def main():
    rows = [(t, f) for t, f in load_lines() if keep(t)]
    df = pd.DataFrame(
        {
            "payload_id": [f"m{i:04d}" for i in range(1, len(rows) + 1)],
            "input_text": [t for t, _ in rows],
            "label": "1",
            "source": "payloadsallthethings",
            "category": [categorize(t) for t, _ in rows],
            "group_id": "pending",
            "notes": [f for _, f in rows],
        },
        columns=COLUMNS,
        dtype=str,
    )
    df.to_csv(OUT, index=False, lineterminator="\n")

    # Doc lai de chac chan input_text khong bi bien doi khi ghi CSV
    back = pd.read_csv(OUT, dtype=str, keep_default_na=False)
    assert back["input_text"].tolist() == df["input_text"].tolist(), "input_text sai khi doc lai"
    print(f"Da ghi {OUT.relative_to(ROOT)}: {len(df)} dong")
    print(df["category"].value_counts().to_dict())


if __name__ == "__main__":
    main()
