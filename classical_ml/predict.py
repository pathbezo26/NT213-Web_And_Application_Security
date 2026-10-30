"""Chay model ML da train (.pkl) tren mot file CSV bat ky (Tuan 4: tap FPR, tap Exp.5).

KHONG train lai, chi nap model va du doan. Ghi ket qua theo schema chung:
    payload_id, model, prediction, confidence, true_label, exp     (confidence = P(doc hai))

Dung:
    python classical_ml/predict.py --model classical_ml/models/exp3_ml_svm.pkl \
        --input data/fpr/benign_hard.csv --exp exp4_fpr
    # Chay tren dong val cua dataset chinh (chi lay split=val):
    python classical_ml/predict.py --model classical_ml/models/exp3_ml_svm.pkl \
        --input data/processed/dataset_all.csv --split val --exp exp4_fpr_val
"""
import argparse
import sys
from pathlib import Path

import joblib
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))  # de joblib tim thay features.Handcrafted khi nap pipeline


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", required=True, help="File .pkl do classical_ml/train.py luu")
    ap.add_argument("--input", required=True, help="CSV co cot payload_id, payload, label")
    ap.add_argument("--split", default=None, help="Chi lay dong co split nay (vd val). Mac dinh: tat ca")
    ap.add_argument("--exp", required=True, help="Ten thi nghiem, vd exp4_fpr")
    ap.add_argument("--output", default=None, help="Mac dinh: classical_ml/results/<exp>_<ten model>.csv")
    args = ap.parse_args()

    bundle = joblib.load(args.model)
    pipe = bundle["pipeline"]
    name = Path(args.model).stem.split("_")[-1]  # exp3_ml_svm -> svm
    print(f"Nap model: {args.model} | tham so: {bundle.get('params')} | "
          f"dac trung thu cong: {bundle.get('handcrafted', True)}")

    df = pd.read_csv(args.input, dtype=str, keep_default_na=False)
    for col in ("payload_id", "payload", "label"):
        if col not in df.columns:
            raise SystemExit(f"Thieu cot '{col}'. Tap moi phai chay qua scripts/check_new_set.py truoc.")
    if args.split:
        if args.split == "test":
            raise SystemExit("Tap test van khoa o Tuan 4 — chi dung o buoi so sanh cuoi.")
        df = df[df["split"] == args.split].reset_index(drop=True)
    print(f"So dong du doan: {len(df)}")

    p_mal = pipe.predict_proba(df["payload"])[:, 1]
    pred = (p_mal >= 0.5).astype(int)
    out = pd.DataFrame({"payload_id": df["payload_id"], "model": name, "prediction": pred,
                        "confidence": p_mal.round(6), "true_label": df["label"].astype(int), "exp": args.exp})
    out_path = Path(args.output) if args.output else HERE / "results" / f"{args.exp}_{name}.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_path, index=False, encoding="utf-8")

    neg = out["true_label"] == 0
    if neg.any():
        fp = int((out.loc[neg, "prediction"] == 1).sum())
        print(f"Dong nhan 0: {int(neg.sum())} | bao nham doc hai: {fp} = {fp / neg.sum():.1%}")
    if (~neg).any():
        tp = int((out.loc[~neg, "prediction"] == 1).sum())
        print(f"Dong nhan 1: {int((~neg).sum())} | phat hien: {tp} = {tp / (~neg).sum():.1%}")
    print(f"Da ghi: {out_path}")


if __name__ == "__main__":
    main()