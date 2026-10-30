"""Train CharCNN-1D cho phan loai payload CI, co dinh seed, ghi schema chung.

Hai che do (chay tu thu muc goc repo):
  python deep_learning/train.py                 # test set chuan (giong classical_ml/train.py)
  python deep_learning/train.py --cross-source  # bo nguon payloadsallthethings khi train,
                                                # do recall tren nguon la (giong classical_ml/cross_source.py)
"""
import argparse
import json
import os
import random
import sys
import time

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

sys.path.insert(0, os.path.dirname(__file__))
from model_cnn1d import CharCNN1D  # noqa: E402
from tokenizer import MAX_LEN, build_vocab, encode  # noqa: E402

SEED = 42
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPLITS = os.path.join(ROOT, "data", "splits")
OUT_CKPT = os.path.join(ROOT, "deep_learning", "checkpoints")
OUT_RESULTS = os.path.join(ROOT, "deep_learning", "results")
HELD_OUT = "payloadsallthethings"
EPOCHS, BATCH, LR = 8, 64, 1e-3


def set_seed(s=SEED):
    random.seed(s)
    np.random.seed(s)
    torch.manual_seed(s)


def load(name):
    df = pd.read_csv(os.path.join(SPLITS, f"{name}.csv"), keep_default_na=False)
    df["input_text"] = df["input_text"].astype(str)
    return df


def to_tensor(texts, vocab):
    return torch.tensor([encode(t, vocab) for t in texts], dtype=torch.long)


@torch.no_grad()
def predict_proba(model, X):
    model.eval()
    out = []
    for i in range(0, len(X), 512):
        out.append(torch.softmax(model(X[i:i + 512]), dim=1)[:, 1])
    return torch.cat(out).numpy()


def metrics(y, p):
    y, p = np.asarray(y), np.asarray(p)
    tp = int(((p == 1) & (y == 1)).sum()); fp = int(((p == 1) & (y == 0)).sum())
    fn = int(((p == 0) & (y == 1)).sum()); tn = int(((p == 0) & (y == 0)).sum())
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    return {"TP": tp, "FP": fp, "FN": fn, "TN": tn, "precision": round(prec, 4), "recall": round(rec, 4),
            "f1": round(2 * prec * rec / (prec + rec), 4) if prec + rec else 0.0,
            "fpr": round(fp / (fp + tn), 4) if fp + tn else 0.0, "fnr": round(fn / (fn + tp), 4) if fn + tp else 0.0}


def train_model(tr_texts, tr_y, va_texts, va_y):
    """Train CharCNN1D, chon epoch co F1 val cao nhat. Vocab chi xay tu TRAIN."""
    vocab = build_vocab(tr_texts)
    Xtr, Xva = to_tensor(tr_texts, vocab), to_tensor(va_texts, vocab)
    ytr = torch.tensor(np.asarray(tr_y), dtype=torch.long)
    g = torch.Generator().manual_seed(SEED)
    dl = DataLoader(TensorDataset(Xtr, ytr), batch_size=BATCH, shuffle=True, generator=g)
    model = CharCNN1D(vocab_size=len(vocab) + 2)  # +2 cho padding (0) va unknown (1)
    opt = torch.optim.Adam(model.parameters(), lr=LR)
    loss_fn = nn.CrossEntropyLoss()
    best_f1, best_state, best_ep = -1, None, 0
    for ep in range(1, EPOCHS + 1):
        model.train(); t0 = time.time(); total = 0.0
        for xb, yb in dl:
            opt.zero_grad(); loss = loss_fn(model(xb), yb); loss.backward(); opt.step()
            total += loss.item() * len(xb)
        f1 = metrics(va_y, (predict_proba(model, Xva) >= 0.5).astype(int))["f1"]
        print(f"  epoch {ep}: loss={total / len(Xtr):.4f}  val F1={f1:.4f}  ({time.time() - t0:.0f}s)")
        if f1 > best_f1:
            best_f1, best_ep = f1, ep
            best_state = {k: v.clone() for k, v in model.state_dict().items()}
    model.load_state_dict(best_state)
    print(f"  -> chon epoch {best_ep} (val F1={best_f1:.4f}), vocab={len(vocab)} ky tu, MAX_LEN={MAX_LEN}")
    return model, vocab, best_ep


def run_standard():
    tr, va, te = load("train"), load("val"), load("test")
    print(f"[test chuan] train={len(tr)} val={len(va)} test={len(te)}")
    model, vocab, ep = train_model(tr.input_text.tolist(), tr.label, va.input_text.tolist(), va.label)
    proba = predict_proba(model, to_tensor(te.input_text.tolist(), vocab))
    pred = (proba >= 0.5).astype(int)
    m = metrics(te.label, pred)
    by_cat = {}
    for cat in sorted(te[te.label == 0].category.unique()):
        mask = ((te.label == 0) & (te.category == cat)).values
        by_cat[cat] = {"N": int(mask.sum()), "FP": int(pred[mask].sum()), "fpr": round(float(pred[mask].mean()), 4)}
    os.makedirs(OUT_CKPT, exist_ok=True); os.makedirs(OUT_RESULTS, exist_ok=True)
    torch.save({"state": model.state_dict(), "vocab": vocab}, os.path.join(OUT_CKPT, "cnn1d.pt"))
    pd.DataFrame({"payload_id": te.payload_id, "model": "cnn1d", "prediction": pred, "confidence": proba.round(4),
                  "true_label": te.label, "category": te.category, "exp": "test_chuan"}
                 ).to_csv(os.path.join(OUT_RESULTS, "pred_test_cnn1d.csv"), index=False)
    return {"best_epoch": ep, "test": m, "fpr_by_category": by_cat}


def run_cross_source():
    trval = pd.concat([load("train"), load("val")], ignore_index=True)
    te = load("test")
    allx = pd.concat([trval, te], ignore_index=True)
    pool = trval[trval.source != HELD_OUT].sample(frac=1.0, random_state=SEED)
    n_val = int(len(pool) * 0.15)  # tach val noi bo de chon epoch, khong dung nguon la
    va, tr = pool.iloc[:n_val], pool.iloc[n_val:]
    held = allx[(allx.source == HELD_OUT) & (allx.label == 1)]
    ben = te[te.label == 0]
    print(f"[cross-source] train={len(tr)} val={len(va)} | payload nguon la={len(held)} | benign test={len(ben)}")
    model, vocab, ep = train_model(tr.input_text.tolist(), tr.label, va.input_text.tolist(), va.label)
    ph = (predict_proba(model, to_tensor(held.input_text.tolist(), vocab)) >= 0.5).astype(int)
    pb = (predict_proba(model, to_tensor(ben.input_text.tolist(), vocab)) >= 0.5).astype(int)
    return {"best_epoch": ep, "recall_nguon_la": round(float(ph.mean()), 4), "TP": int(ph.sum()), "N": len(held),
            "fpr_benign_test": round(float(pb.mean()), 4)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cross-source", action="store_true")
    args = ap.parse_args()
    set_seed()
    torch.set_num_threads(max(1, os.cpu_count() or 1))
    res = run_cross_source() if args.cross_source else run_standard()
    name = "cross_source_cnn1d.json" if args.cross_source else "summary_cnn1d.json"
    os.makedirs(OUT_RESULTS, exist_ok=True)
    with open(os.path.join(OUT_RESULTS, name), "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2, ensure_ascii=False)
    print("\n========== KET QUA (chup man hinh phan nay) ==========")
    print(json.dumps(res, indent=2, ensure_ascii=False))
    print(f"Da ghi deep_learning/results/{name}")


if __name__ == "__main__":
    main()