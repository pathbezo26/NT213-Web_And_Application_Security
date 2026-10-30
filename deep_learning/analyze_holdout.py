"""
Phan tich ket qua holdout: model phat hien tot/kem o nhom payload nao.

Ghep file du doan holdout voi dataset goc theo payload_id, roi tinh ty le phat hien
(recall) theo vai dac diem BE MAT cua payload, theo do dai, va theo phan bo
P(doc hai). Chi in/ghi so lieu tong hop, khong in payload.

GIOI HAN (ghi vao bao cao): day la phan tich TUONG QUAN. Cac dac diem di kem nhau
(vd. payload co 'sleep' thuong dai hon, co if/fi), nen ty le phat hien cao o mot nhom
KHONG chung minh model dua vao dac diem do. Muon biet nguyen nhan can thu nghiem co
kiem soat hoac SHAP/LIME.

Dung:
    python deep_learning/analyze_holdout.py \
        --holdout deep_learning/results/exp3_dl_holdout_commix_cnn1d_holdout.csv \
        --dataset data/processed/dataset_all.csv
Ket qua ghi them ra <ten file holdout>_phan_tich_dac_diem.csv va _phan_tich_do_dai.csv
"""
import argparse
import math
from pathlib import Path

import pandas as pd

# Dac diem be mat theo cau truc shell thong thuong
FEATURES = {
    "co 'sleep'": lambda s: s.str.contains("sleep", case=False),
    "co '$((' (phep tinh)": lambda s: s.str.contains(r"\$\(\(", regex=True),
    "co '$(' hoac backtick": lambda s: s.str.contains(r"\$\(|`", regex=True),
    "co 'echo'": lambda s: s.str.contains("echo", case=False),
    "co 'if'/'fi'": lambda s: s.str.contains(r"\bif\b|\bfi\b", regex=True),
    "co xuong dong that": lambda s: s.str.contains("\n", regex=False),
    "co '\\n' dang chu": lambda s: s.str.contains("\\n", regex=False),
}


def wilson(k, n, z=1.96):
    """Khoang tin cay Wilson 95% cho ty le k/n (tinh bang %)."""
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(max(0, c - h) * 100, 1), round(min(1, c + h) * 100, 1))


def summarize(sub, name, min_n):
    n = len(sub)
    k = int(sub["prediction"].sum())
    lo, hi = wilson(k, n)
    return {"nhom": name, "so_dong": n, "phat_hien": k,
            "ty_le_%": round(k / n * 100, 1) if n else float("nan"),
            "KTC95_%": f"{lo}-{hi}", "it_mau": "x" if n < min_n else ""}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--holdout", required=True, help="File *_holdout.csv do train.py ghi")
    ap.add_argument("--dataset", required=True, help="dataset_all.csv (de lay cot payload)")
    ap.add_argument("--min-n", type=int, default=30, help="Nhom it hon so dong nay bi danh dau 'it_mau'")
    args = ap.parse_args()

    pred = pd.read_csv(args.holdout, dtype=str, keep_default_na=False)
    data = pd.read_csv(args.dataset, dtype=str, keep_default_na=False)[["payload_id", "payload", "source"]]
    df = pred.merge(data, on="payload_id", how="left", indicator=True)
    n_miss = int((df["_merge"] != "both").sum())
    if n_miss:
        raise SystemExit(f"Dung: {n_miss} dong trong file holdout khong co payload_id trong dataset. "
                         f"Co the dataset da chia lai sau khi train — train lai roi chay lai.")

    df["prediction"] = df["prediction"].astype(int)
    df["true_label"] = df["true_label"].astype(int)
    conf = pd.to_numeric(df["confidence"], errors="coerce")
    # train.py tu 28/10/2026 ghi confidence = P(doc hai). File cu ghi xac suat lop DUOC DU DOAN
    # (luon >= 0,5). Tu nhan biet: dong du doan 0 ma confidence >= 0,5 -> kieu cu -> doi ve P(doc hai).
    old_style = (conf[df["prediction"] == 0] >= 0.5).all() and (df["prediction"] == 0).any()
    if old_style:
        print("(File kieu cu: confidence = xac suat lop du doan -> da doi ve P(doc hai))")
        df["p_mal"] = conf.where(df["prediction"] == 1, 1 - conf)
    else:
        df["p_mal"] = conf

    mal = df[df["true_label"] == 1].copy()
    n = len(mal)
    k = int(mal["prediction"].sum())
    lo, hi = wilson(k, n)
    print(f"Tong malicious trong holdout: {n} | phat hien: {k} ({k / max(n, 1) * 100:.1f}%, KTC95 {lo}-{hi}%)")
    print(f"(Nhom duoi {args.min_n} dong danh dau 'x' o cot it_mau: ty le khong on dinh)")

    # ---- Dac diem be mat ----
    rows, skipped = [], []
    for name, fn in FEATURES.items():
        has = fn(mal["payload"])
        share = has.mean()
        if share > 0.99 or share < 0.01:
            skipped.append(f"{name} ({share * 100:.1f}% dong co)")
            continue
        rows.append(summarize(mal[has], f"{name}: co", args.min_n))
        rows.append(summarize(mal[~has], f"{name}: khong", args.min_n))
    feat = pd.DataFrame(rows)
    print("\n===== Ty le phat hien theo dac diem be mat =====")
    print(feat.to_string(index=False) if len(feat) else "(khong co dac diem nao co nhom so sanh)")
    if skipped:
        print("Bo qua vi gan nhu toan bo dong cung co/cung khong (khong co nhom so sanh): " + "; ".join(skipped))

    # ---- Do dai ----
    mal["len"] = mal["payload"].str.len()
    bins = [0, 20, 40, 60, 100, 100000]
    labels = ["<=20", "21-40", "41-60", "61-100", ">100"]
    mal["nhom_dai"] = pd.cut(mal["len"], bins=bins, labels=labels)
    length = pd.DataFrame([summarize(g, f"do dai {lab}", args.min_n)
                           for lab, g in mal.groupby("nhom_dai", observed=True)])
    print("\n===== Ty le phat hien theo do dai payload =====")
    print(length.to_string(index=False))

    # ---- P(doc hai) ----
    print("\n===== P(doc hai) do model du doan =====")
    for lab, grp in [("phat hien (pred=1)", mal[mal.prediction == 1]), ("bo sot (pred=0)", mal[mal.prediction == 0])]:
        c = grp["p_mal"].dropna()
        if len(c):
            print(f"{lab:20} n={len(c):5d} | trung binh={c.mean():.3f} | trung vi={c.median():.3f} "
                  f"| min={c.min():.3f} max={c.max():.3f}")
    missed = mal[mal.prediction == 0]["p_mal"].dropna()
    if len(missed):
        print(f"Trong cac dong bo sot: {(missed < 0.1).mean() * 100:.1f}% co P(doc hai) < 0,1 "
              f"(model TU TIN la benign), {((missed >= 0.3) & (missed < 0.5)).mean() * 100:.1f}% nam trong 0,3-0,5 (sat nguong)")

    # ---- Ghi file ----
    stem = Path(args.holdout).with_suffix("")
    feat.to_csv(f"{stem}_phan_tich_dac_diem.csv", index=False, encoding="utf-8")
    length.to_csv(f"{stem}_phan_tich_do_dai.csv", index=False, encoding="utf-8")
    print(f"\nDa ghi: {stem}_phan_tich_dac_diem.csv, {stem}_phan_tich_do_dai.csv")
    print("Nhac: day la phan tich tuong quan, khong chung minh model dua vao dac diem nao.")


if __name__ == "__main__":
    main()