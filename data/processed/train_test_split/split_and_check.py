"""Chia 70/15/15 THEO group_id va kiem tra khong ro ri du lieu (Tuan 2).

Nguyen tac: moi ho payload (cung group_id) chi nam o MOT tap -> tranh data leakage.
Chay (tu thu muc goc):
    python data/processed/train_test_split/split_and_check.py
"""
import csv
import hashlib
from pathlib import Path

SEED = 42
ROOT = Path(__file__).resolve().parents[3]
PROC = ROOT / "data" / "processed"
OUT = Path(__file__).resolve().parent
FILES = ["malicious.csv", "benign_handwritten.csv", "benign_csic_selected.csv"]


def load_rows():
    rows = []
    for f in FILES:
        p = PROC / f
        if not p.exists():
            continue
        with p.open(encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                if not r.get("payload_id") or r["payload_id"].startswith("#"):
                    continue
                rows.append(r)
    return rows


def bucket(group_id):
    """Chia on dinh theo hash(group_id) -> cung group luon cung tap."""
    h = int(hashlib.md5(f"{SEED}:{group_id}".encode()).hexdigest(), 16) % 100
    return "train" if h < 70 else "val" if h < 85 else "test"


def main():
    rows = load_rows()
    if not rows:
        print("Chua co du lieu that trong data/processed/ (moi la vi du). "
              "Dien du lieu o Tuan 2 roi chay lai.")
        return
    splits = {"train": [], "val": [], "test": []}
    for r in rows:
        splits[bucket(r.get("group_id", r["payload_id"]))].append(r)

    for name, part in splits.items():
        out = OUT / f"{name}.csv"
        with out.open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=rows[0].keys())
            w.writeheader()
            w.writerows(part)
        print(f"{name}: {len(part)} mau -> {out.name}")

    # kiem tra ro ri: khong group_id nao xuat hien o >1 tap
    seen = {}
    leak = []
    for name, part in splits.items():
        for r in part:
            g = r.get("group_id", r["payload_id"])
            if g in seen and seen[g] != name:
                leak.append((g, seen[g], name))
            seen[g] = name
    # kiem tra trung input_text y hệt giua cac tap
    texts = {}
    dup = []
    for name, part in splits.items():
        for r in part:
            t = r["input_text"]
            if t in texts and texts[t] != name:
                dup.append((t, texts[t], name))
            texts[t] = name

    print("\n[Kiem tra ro ri]")
    print("  group_id tran tap:", "KHONG" if not leak else leak)
    print("  input_text trung tap:", "KHONG" if not dup else dup[:5])
    if not leak and not dup:
        print("  OK - khong phat hien ro ri.")


if __name__ == "__main__":
    main()
