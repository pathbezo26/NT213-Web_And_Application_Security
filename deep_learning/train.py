"""Train & tune CharCNN1D (model_cnn1d.py) tren dataset_all.csv.

Dien noi dung con thieu trong khung train.py goc cua nhom (Tuan 3):
    doc split -> build_vocab (tokenizer.py) -> DataLoader -> train CharCNN1D
    -> luu checkpoint -> ghi results/*.csv dung schema chung (xem results/README.md)

Cot confidence trong results/*.csv = P(doc hai) = xac suat model gan cho label=1, voi
MOI dong (ke ca dong du doan 0). Dung truc tiep de ve ROC / tinh PR-AUC. (Ban truoc
28/10/2026 ghi xac suat cua lop duoc du doan — file cu can doi: p = conf neu pred=1, 1-conf neu pred=0.)

Nguyen tac bat buoc:
    - vocab + max_len CHI xay tu tap train (khong ro ri).
    - Cac cau hinh (max_len, embedding dim) duoc chon theo F1 tren tap VAL.
    - KHONG dung tap test o day — tap test chi dung mot lan cuoi, o Tuan danh gia cuoi.
    - Seed co dinh (mac dinh 42), ghi lai cau hinh trong ten checkpoint/log.

Dung (1 cau hinh):
    python deep_learning/train.py --input dataset/processed/dataset_all.csv

Dung (tune luoi nhieu cau hinh, tu chon cau hinh tot nhat theo F1 tren val):
    python deep_learning/train.py --input dataset/processed/dataset_all.csv \
        --max-len-grid 50,100,200 --emb-dim-grid 16,32,64 --epochs 20

Dung (kiem tra cheo nguon — loai han 1 nguon khoi train/val, do rieng tren nguon do):
    python deep_learning/train.py --input dataset/processed/dataset_all.csv \
        --holdout-source "command_exec|command-execution-unix" --exp exp3_dl_holdout_patt
    -> Neu model chi "thuoc khuon" Commix, ty le phat hien tren nguon bi loai se thap.
"""
import argparse
import itertools
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from torch.utils.data import DataLoader, TensorDataset

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from tokenizer import build_vocab, encode  # noqa: E402
from model_cnn1d import CharCNN1D  # noqa: E402

SEED = 42


def set_seed(seed):
    torch.manual_seed(seed)
    np.random.seed(seed)


def make_tensors(df, vocab, max_len):
    X = torch.tensor([encode(p, vocab, max_len) for p in df["payload"]], dtype=torch.long)
    y = torch.tensor(df["label"].to_numpy(), dtype=torch.long)
    return X, y


def train_one_config(train_df, val_df, vocab, max_len, emb_dim, n_filters,
                      epochs, batch_size, lr, seed, device):
    """Train 1 cau hinh (max_len, emb_dim); giu lai trong so cua epoch co F1-val tot nhat
    (tranh overfit o epoch cuoi), tra ve model + F1 tot nhat."""
    set_seed(seed)
    X_train, y_train = make_tensors(train_df, vocab, max_len)
    X_val, y_val = make_tensors(val_df, vocab, max_len)

    train_loader = DataLoader(TensorDataset(X_train, y_train), batch_size=batch_size, shuffle=True)

    model = CharCNN1D(vocab_size=len(vocab) + 2, emb_dim=emb_dim, n_filters=n_filters).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    loss_fn = nn.CrossEntropyLoss()

    best_val_f1, best_state = -1.0, None
    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0.0
        for xb, yb in train_loader:
            xb, yb = xb.to(device), yb.to(device)
            opt.zero_grad()
            logits = model(xb)
            loss = loss_fn(logits, yb)
            loss.backward()
            opt.step()
            total_loss += loss.item() * xb.size(0)
        train_loss = total_loss / len(train_df)

        model.eval()
        with torch.no_grad():
            val_pred = model(X_val.to(device)).argmax(dim=1).cpu().numpy()
        val_f1 = f1_score(y_val.numpy(), val_pred, zero_division=0)
        print(f"  epoch {epoch:3d}/{epochs} | train_loss={train_loss:.4f} | val_F1={val_f1:.4f}")

        if val_f1 > best_val_f1:
            best_val_f1 = val_f1
            best_state = {k: v.clone() for k, v in model.state_dict().items()}

    model.load_state_dict(best_state)
    return model, best_val_f1


def evaluate(model, X, y, device):
    model.eval()
    with torch.no_grad():
        probs = torch.softmax(model(X.to(device)), dim=1).cpu().numpy()
    pred = probs.argmax(axis=1)
    y_np = y.numpy()
    metrics = {
        "accuracy": accuracy_score(y_np, pred),
        "precision": precision_score(y_np, pred, zero_division=0),
        "recall": recall_score(y_np, pred, zero_division=0),
        "f1": f1_score(y_np, pred, zero_division=0),
    }
    return metrics, pred, probs


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", required=True, help="dataset_all.csv (co cot split, payload_id)")
    ap.add_argument("--max-len-grid", default="100",
                     help="Danh sach max_len cach nhau dau phay de tune, vd 50,100,200")
    ap.add_argument("--emb-dim-grid", default="16",
                     help="Danh sach embedding dim cach nhau dau phay de tune, vd 16,32,64")
    ap.add_argument("--n-filters", type=int, default=64)
    ap.add_argument("--epochs", type=int, default=20)
    ap.add_argument("--batch-size", type=int, default=64)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--exp", default="exp3_dl", help="Ten gan vao cot 'exp' trong results/*.csv")
    ap.add_argument("--output-dir", default=str(HERE / "results"))
    ap.add_argument("--checkpoint", default=str(HERE / "best_cnn1d.pt"))
    ap.add_argument("--holdout-source", default=None,
                     help="Regex khop cot source/family: cac dong khop bi LOAI khoi train/val va "
                          "chi dung de do rieng (kiem tra model co tong quat hoa sang nguon moi)")
    args = ap.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    df = pd.read_csv(args.input, dtype=str, keep_default_na=False)
    df["label"] = df["label"].astype(int)
    for col in ("split", "payload_id"):
        if col not in df.columns:
            raise SystemExit(f"Thieu cot '{col}' - chay scripts/split-v5.py truoc.")

    holdout_df = None
    if args.holdout_source:
        text = df["source"].astype(str)
        if "family" in df.columns:
            text = text + " " + df["family"].astype(str)
        hmask = text.str.contains(args.holdout_source, case=False, regex=True)
        # Chi lay phan holdout KHONG thuoc tap test (tap test van khoa, khong dung o day)
        holdout_df = df[hmask & (df["split"] != "test")].reset_index(drop=True)
        df = df[~hmask].reset_index(drop=True)
        print(f"Holdout nguon '{args.holdout_source}': {len(holdout_df)} dong (train+val cua nguon do, "
              f"da loai khoi huan luyen) | nhan: {holdout_df['label'].value_counts().to_dict()}")
        if holdout_df.empty:
            raise SystemExit("Regex --holdout-source khong khop dong nao — kiem tra lai gia tri cot source.")

    train_df = df[df["split"] == "train"].reset_index(drop=True)
    val_df = df[df["split"] == "val"].reset_index(drop=True)
    print(f"train: {len(train_df)} dong | val: {len(val_df)} dong")

    # ---- Vocab CHI xay tu train (khong ro ri) ----
    vocab = build_vocab(train_df["payload"])
    print(f"Vocab size (ke ca PAD/UNK): {len(vocab) + 2}")

    max_lens = [int(x) for x in args.max_len_grid.split(",")]
    emb_dims = [int(x) for x in args.emb_dim_grid.split(",")]

    best_overall = None
    for max_len, emb_dim in itertools.product(max_lens, emb_dims):
        print(f"\n=== Cau hinh: max_len={max_len}, emb_dim={emb_dim} ===")
        model, val_f1 = train_one_config(
            train_df, val_df, vocab, max_len, emb_dim, args.n_filters,
            args.epochs, args.batch_size, args.lr, args.seed, device,
        )
        print(f"-> F1 tot nhat tren val cho cau hinh nay: {val_f1:.4f}")
        if best_overall is None or val_f1 > best_overall["val_f1"]:
            best_overall = {"model": model, "max_len": max_len, "emb_dim": emb_dim, "val_f1": val_f1}

    print(f"\n===== Cau hinh tot nhat: max_len={best_overall['max_len']}, "
          f"emb_dim={best_overall['emb_dim']} | val_F1={best_overall['val_f1']:.4f} =====")

    # ---- Luu checkpoint cua cau hinh tot nhat ----
    torch.save({
        "state_dict": best_overall["model"].state_dict(),
        "vocab": vocab,
        "max_len": best_overall["max_len"],
        "emb_dim": best_overall["emb_dim"],
        "n_filters": args.n_filters,
    }, args.checkpoint)
    print(f"Da luu checkpoint: {args.checkpoint}")

    # ---- Danh gia lai cau hinh tot nhat tren VAL, ghi results/ dung schema chung ----
    X_val, y_val = make_tensors(val_df, vocab, best_overall["max_len"])
    metrics, pred, probs = evaluate(best_overall["model"], X_val, y_val, device)
    print("\nMetrics tren VAL (KHONG dung tap test o day):")
    for k, v in metrics.items():
        print(f"  {k}: {v:.4f}")

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{args.exp}_cnn1d.csv"
    results = pd.DataFrame({
        "payload_id": val_df["payload_id"],
        "model": "cnn1d",
        "prediction": pred,
        "confidence": probs[:, 1],  # P(doc hai) = P(label=1), KHONG phai xac suat lop du doan
        "true_label": val_df["label"],
        "exp": args.exp,
    })
    results.to_csv(out_path, index=False, encoding="utf-8")
    print(f"Da ghi ket qua (schema chung payload_id,model,prediction,confidence,true_label,exp; confidence = P(doc hai)): {out_path}")

    # ---- Phan tich loi theo category tren VAL ----
    if "category" in val_df.columns:
        va = val_df.assign(pred=pred)
        va["dung"] = va["pred"] == va["label"]
        print("\n===== Ty le dung theo category (VAL) =====")
        print(va.groupby("category")["dung"].agg(so_dong="size", so_sai=lambda s: int((~s).sum()),
                                                  ty_le_dung="mean").to_string())
        wrong = va[~va["dung"]]
        if len(wrong):
            print(f"\n{len(wrong)} dong du doan SAI (toi da 30 dong dau):")
            for _, r in wrong.head(30).iterrows():
                print(f"  [{r['category']}] that={r['label']} doan={r['pred']} | {r['payload'][:90]!r}")

    # ---- Do rieng tren nguon bi loai (holdout) ----
    if holdout_df is not None:
        X_h, y_h = make_tensors(holdout_df, vocab, best_overall["max_len"])
        _, pred_h, probs_h = evaluate(best_overall["model"], X_h, y_h, device)
        n_mal = int((holdout_df["label"] == 1).sum())
        detected = int(((pred_h == 1) & (holdout_df["label"].to_numpy() == 1)).sum())
        print(f"\n===== HOLDOUT nguon '{args.holdout_source}' (model CHUA tung thay nguon nay) =====")
        print(f"Ty le phat hien malicious: {detected}/{n_mal} = {detected / max(n_mal, 1):.1%}")
        print("  -> So sanh voi recall tren val: neu thap hon nhieu, model dang thuoc khuon nguon "
              "train hon la hoc pattern command injection chung.")
        h_out = out_dir / f"{args.exp}_cnn1d_holdout.csv"
        pd.DataFrame({
            "payload_id": holdout_df["payload_id"], "model": "cnn1d", "prediction": pred_h,
            "confidence": probs_h[:, 1],  # P(doc hai)
            "true_label": holdout_df["label"], "exp": f"{args.exp}_holdout",
        }).to_csv(h_out, index=False, encoding="utf-8")
        missed = holdout_df[(pred_h == 0) & (holdout_df["label"].to_numpy() == 1)]
        if len(missed):
            print(f"\nVi du payload holdout bi BO SOT (toi da 15):")
            for p in missed["payload"].head(15):
                print(f"  {p[:90]!r}")
        print(f"Da ghi: {h_out}")


if __name__ == "__main__":
    main()