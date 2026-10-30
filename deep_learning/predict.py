"""Chay CNN-1D da train (checkpoint .pt) tren mot file CSV bat ky (Tuan 4: tap FPR, tap Exp.5).

KHONG train lai. Vocab, max_len, emb_dim, n_filters lay tu checkpoint do train.py luu.
Ghi ket qua theo schema chung:
    payload_id, model, prediction, confidence, true_label, exp     (confidence = P(doc hai))

Dung:
    python deep_learning/predict.py --checkpoint deep_learning/best_cnn1d.pt \
        --input data/fpr/benign_hard.csv --exp exp4_fpr
    python deep_learning/predict.py --checkpoint deep_learning/best_cnn1d.pt \
        --input data/processed/dataset_all.csv --split val --exp exp4_fpr_val
"""
import argparse
import sys
from pathlib import Path

import pandas as pd
import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from tokenizer import encode  # noqa: E402
from model_cnn1d import CharCNN1D  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--checkpoint", default=str(HERE / "best_cnn1d.pt"))
    ap.add_argument("--input", required=True, help="CSV co cot payload_id, payload, label")
    ap.add_argument("--split", default=None, help="Chi lay dong co split nay (vd val). Mac dinh: tat ca")
    ap.add_argument("--exp", required=True, help="Ten thi nghiem, vd exp4_fpr")
    ap.add_argument("--output", default=None, help="Mac dinh: deep_learning/results/<exp>_cnn1d.csv")
    ap.add_argument("--batch-size", type=int, default=512)
    args = ap.parse_args()

    ck = torch.load(args.checkpoint, map_location="cpu", weights_only=False)
    vocab, max_len = ck["vocab"], ck["max_len"]
    model = CharCNN1D(vocab_size=len(vocab) + 2, emb_dim=ck["emb_dim"], n_filters=ck["n_filters"])
    model.load_state_dict(ck["state_dict"])
    model.eval()
    print(f"Nap checkpoint: {args.checkpoint} | max_len={max_len}, emb_dim={ck['emb_dim']}, vocab={len(vocab) + 2}")

    df = pd.read_csv(args.input, dtype=str, keep_default_na=False)
    for col in ("payload_id", "payload", "label"):
        if col not in df.columns:
            raise SystemExit(f"Thieu cot '{col}'. Tap moi phai chay qua scripts/check_new_set.py truoc.")
    if args.split:
        if args.split == "test":
            raise SystemExit("Tap test van khoa o Tuan 4 — chi dung o buoi so sanh cuoi.")
        df = df[df["split"] == args.split].reset_index(drop=True)
    print(f"So dong du doan: {len(df)}")
    unk = sum(c not in vocab for p in df["payload"] for c in p[:max_len])
    if unk:
        print(f"Luu y: {unk} ky tu khong co trong vocab train (ma hoa thanh UNK)")

    X = torch.tensor([encode(p, vocab, max_len) for p in df["payload"]], dtype=torch.long)
    probs = []
    with torch.no_grad():
        for i in range(0, len(X), args.batch_size):
            probs.append(torch.softmax(model(X[i:i + args.batch_size]), dim=1)[:, 1])
    p_mal = torch.cat(probs).numpy() if probs else []
    pred = (p_mal >= 0.5).astype(int)

    out = pd.DataFrame({"payload_id": df["payload_id"], "model": "cnn1d", "prediction": pred,
                        "confidence": p_mal.round(6), "true_label": df["label"].astype(int), "exp": args.exp})
    out_path = Path(args.output) if args.output else HERE / "results" / f"{args.exp}_cnn1d.csv"
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