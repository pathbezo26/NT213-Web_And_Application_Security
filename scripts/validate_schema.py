"""Kiem tra schema 7 cot cho cac file CSV du lieu T05.
Dung: python scripts/validate_schema.py <file.csv> [<file2.csv> ...]
"""
import sys
import pandas as pd

COLUMNS = ["payload_id", "input_text", "label", "source", "category", "group_id", "notes"]
SOURCES = {"payloadsallthethings", "commix", "handwritten", "csic"}


def check(path):
    # dtype=str + keep_default_na=False: chuoi nhu "NA", "null" khong bi pandas bien thanh NaN
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    errors = []
    if list(df.columns) != COLUMNS:
        return df, [f"cot sai hoac sai thu tu: {list(df.columns)}"]
    if (df["payload_id"].str.strip() == "").any():
        errors.append("co payload_id rong")
    if df["payload_id"].duplicated().any():
        errors.append("payload_id trung: " + ", ".join(df.loc[df["payload_id"].duplicated(), "payload_id"]))
    if (df["input_text"].str.strip() == "").any():
        errors.append("co input_text rong")
    if not df["label"].isin(["0", "1"]).all():
        errors.append("label phai la 0 hoac 1")
    bad = df.loc[~df["source"].isin(SOURCES), "source"].unique()
    if len(bad):
        errors.append(f"source la: {list(bad)} (cho phep: {sorted(SOURCES)})")
    for col in ("category", "group_id"):
        if (df[col].str.strip() == "").any():
            errors.append(f"co {col} rong")
    return df, errors


failed = False
for path in sys.argv[1:]:
    df, errors = check(path)
    if errors:
        failed = True
        print(f"[FAIL] {path}")
        for e in errors:
            print("       -", e)
    else:
        print(f"[OK]   {path}: {len(df)} dong, 7 cot dung thu tu")
        print("       label:", df["label"].value_counts().sort_index().to_dict())
sys.exit(1 if failed else 0)
