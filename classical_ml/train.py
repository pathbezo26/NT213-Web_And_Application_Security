"""Train + tune ML co dien (SVM, RandomForest) tren dataset_all.csv (Tuan 3).

Luong: doc cot split CO SAN -> dac trung (features.py: TF-IDF char n-gram + 5 dac trung
thu cong) -> tune tung model tren tap VAL -> luu model .pkl vao models/ -> ghi du doan
theo schema chung vao results/.

Nguyen tac bat buoc (giong mang DL de so sanh duoc):
  - KHONG chia lai (khong train_test_split): dung dung cot split do scripts/split.py tao,
    de ML va DL do tren CUNG mot tap va khong ro ri theo khuon.
  - Moi phep fit (TF-IDF, scaler, model) chi tren train. Chon tham so theo F1 tren val.
    KHONG dung tap test o day.
  - Seed co dinh (mac dinh 42).
  - Cot confidence = P(doc hai) = xac suat model gan cho label 1, voi MOI dong.
    SVM tuyen tinh khong co xac suat -> boc bang CalibratedClassifierCV (sigmoid, 3 fold
    tren chinh tap train).

Dung:
    python classical_ml/train.py --input data/processed/dataset_all.csv
    python classical_ml/train.py --input data/processed/dataset_all.csv --models svm
    python classical_ml/train.py --input data/processed/dataset_all.csv \
        --holdout-source "command_exec|command-execution-unix" --exp exp3_ml_holdout_patt
    # Thi nghiem bo dac trung thu cong (nho doi --exp de khong ghi de):
    python classical_ml/train.py --input data/processed/dataset_all.csv --no-handcrafted \
        --holdout-source "commix" --exp exp3_ml_nohand_holdout_commix
"""
import argparse
import itertools
import re
import sys
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from features import build_features  # noqa: E402

SEED = 42
BASELINE_RE = re.compile(r"[;|&$`(){}<>]")  # cung regex voi deep_learning/diagnose_val.py


def parse_list(text, cast):
    return [cast(x) for x in text.split(",") if x.strip()]


def parse_ngram(text):
    a, b = text.split("-")
    return (int(a), int(b))


def parse_depth(x):
    return None if x.strip().lower() == "none" else int(x)


def make_model(name, params, seed, n_jobs):
    if name == "svm":
        base = LinearSVC(C=params["C"], random_state=seed, max_iter=20000)
        return CalibratedClassifierCV(base, method="sigmoid", cv=3)
    if name == "rf":
        return RandomForestClassifier(n_estimators=params["n_estimators"], max_depth=params["max_depth"],
                                      random_state=seed, n_jobs=n_jobs)
    raise ValueError(name)


def grid_for(name, args):
    """Danh sach cau hinh, xep tu don gian den phuc tap (hoa thi giu cau hinh don gian hon)."""
    ngrams = parse_list(args.ngram_grid, parse_ngram)
    if name == "svm":
        return [{"ngram": g, "C": c} for g, c in itertools.product(ngrams, parse_list(args.svm_c_grid, float))]
    return [{"ngram": g, "n_estimators": n, "max_depth": d}
            for g, n, d in itertools.product(ngrams, parse_list(args.rf_n_grid, int),
                                             parse_list(args.rf_depth_grid, parse_depth))]


def metrics(y, pred):
    return {"accuracy": accuracy_score(y, pred), "precision": precision_score(y, pred, zero_division=0),
            "recall": recall_score(y, pred, zero_division=0), "f1": f1_score(y, pred, zero_division=0)}


def results_frame(df, pred, p_mal, model_name, exp):
    return pd.DataFrame({"payload_id": df["payload_id"].values, "model": model_name, "prediction": pred,
                         "confidence": np.round(p_mal, 6), "true_label": df["label"].values, "exp": exp})


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", default="data/processed/dataset_all.csv")
    ap.add_argument("--models", default="svm,rf", help="svm, rf hoac svm,rf")
    ap.add_argument("--ngram-grid", default="1-3,2-4", help="Khoang char n-gram, vd 1-3,2-4")
    ap.add_argument("--svm-c-grid", default="0.1,1,10")
    ap.add_argument("--rf-n-grid", default="200")
    ap.add_argument("--rf-depth-grid", default="None,30", help="None = khong gioi han")
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--n-jobs", type=int, default=-1)
    ap.add_argument("--exp", default="exp3_ml", help="Ten gan vao cot exp va ten file ket qua")
    ap.add_argument("--output-dir", default=str(HERE / "results"))
    ap.add_argument("--models-dir", default=str(HERE / "models"))
    ap.add_argument("--no-handcrafted", action="store_true",
                    help="Chi dung TF-IDF, bo 5 dac trung thu cong (thi nghiem kiem chung)")
    ap.add_argument("--holdout-source", default=None,
                    help="Regex khop cot source: dong khop bi LOAI khoi train/val va chi dung de do rieng")
    args = ap.parse_args()

    df = pd.read_csv(args.input, dtype=str, keep_default_na=False)
    for col in ("payload_id", "payload", "label", "split"):
        if col not in df.columns:
            raise SystemExit(f"Thieu cot '{col}' - dung dataset_all.csv da qua scripts/split.py.")
    df["label"] = df["label"].astype(int)

    holdout_df = None
    if args.holdout_source:
        text = df["source"].astype(str)
        if "family" in df.columns:
            text = text + " " + df["family"].astype(str)
        hmask = text.str.contains(args.holdout_source, case=False, regex=True)
        holdout_df = df[hmask & (df["split"] != "test")].reset_index(drop=True)  # tap test van khoa
        df = df[~hmask].reset_index(drop=True)
        if holdout_df.empty:
            raise SystemExit("Regex --holdout-source khong khop dong nao — kiem tra gia tri cot source.")
        print(f"Holdout nguon '{args.holdout_source}': {len(holdout_df)} dong (da loai khoi train/val) "
              f"| nhan: {holdout_df['label'].value_counts().to_dict()}")

    train = df[df["split"] == "train"].reset_index(drop=True)
    val = df[df["split"] == "val"].reset_index(drop=True)
    print(f"train: {len(train)} dong | val: {len(val)} dong")

    use_hand = not args.no_handcrafted
    print("Dac trung: " + ("TF-IDF char n-gram + 5 dac trung thu cong" if use_hand
                           else "CHI TF-IDF char n-gram (--no-handcrafted)"))
    base_pred = val["payload"].map(lambda s: int(bool(BASELINE_RE.search(s))))
    print(f"Tham chieu - baseline 1 dong regex tren val: F1 = {f1_score(val['label'], base_pred):.4f}")

    out_dir, models_dir = Path(args.output_dir), Path(args.models_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    models_dir.mkdir(parents=True, exist_ok=True)
    tune_log = []

    for name in parse_list(args.models, str):
        print(f"\n================ {name.upper()} ================")
        best = None
        for params in grid_for(name, args):
            t0 = time.time()
            pipe = Pipeline([("features", build_features(ngram_range=params["ngram"], use_handcrafted=use_hand)),
                             ("clf", make_model(name, params, args.seed, args.n_jobs))])
            pipe.fit(train["payload"], train["label"])
            p_val = pipe.predict_proba(val["payload"])[:, 1]
            m = metrics(val["label"], (p_val >= 0.5).astype(int))
            shown = {k: (f"{v[0]}-{v[1]}" if k == "ngram" else v) for k, v in params.items()}
            print(f"  {shown} | val F1={m['f1']:.4f} P={m['precision']:.4f} R={m['recall']:.4f} "
                  f"| {time.time() - t0:.0f}s")
            tune_log.append({"model": name, "handcrafted": use_hand, **shown, **{f"val_{k}": round(v, 4) for k, v in m.items()}})
            if best is None or m["f1"] > best["f1"]:  # hoa -> giu cau hinh don gian hon (xep truoc)
                best = {"f1": m["f1"], "params": shown, "pipe": pipe, "p_val": p_val}

        print(f"-> Cau hinh tot nhat {name}: {best['params']} | val F1={best['f1']:.4f}")

        model_path = models_dir / f"{args.exp}_{name}.pkl"
        joblib.dump({"pipeline": best["pipe"], "params": best["params"], "seed": args.seed,
                     "handcrafted": use_hand}, model_path)
        print(f"Da luu model: {model_path}")

        pred = (best["p_val"] >= 0.5).astype(int)
        m = metrics(val["label"], pred)
        print("Metrics tren VAL (KHONG dung tap test o day): "
              + ", ".join(f"{k}={v:.4f}" for k, v in m.items()))
        res_path = out_dir / f"{args.exp}_{name}.csv"
        results_frame(val, pred, best["p_val"], name, args.exp).to_csv(res_path, index=False, encoding="utf-8")
        print(f"Da ghi ket qua (schema chung; confidence = P(doc hai)): {res_path}")

        if "category" in val.columns:
            va = val.assign(pred=pred, dung=pred == val["label"].values)
            print("Ty le dung theo category (VAL):")
            print(va.groupby("category")["dung"].agg(so_dong="size", so_sai=lambda s: int((~s).sum()),
                                                     ty_le_dung="mean").to_string())
            wrong = va[~va["dung"]]
            for _, r in wrong.head(20).iterrows():
                print(f"  SAI [{r['category']}] that={r['label']} doan={r['pred']} | {r['payload'][:90]!r}")

        if holdout_df is not None:
            p_h = best["pipe"].predict_proba(holdout_df["payload"])[:, 1]
            pred_h = (p_h >= 0.5).astype(int)
            n_mal = int((holdout_df["label"] == 1).sum())
            det = int(((pred_h == 1) & (holdout_df["label"].values == 1)).sum())
            print(f"HOLDOUT '{args.holdout_source}' (model CHUA thay nguon nay): "
                  f"phat hien {det}/{n_mal} = {det / max(n_mal, 1):.1%}")
            h_path = out_dir / f"{args.exp}_{name}_holdout.csv"
            results_frame(holdout_df, pred_h, p_h, name, f"{args.exp}_holdout").to_csv(
                h_path, index=False, encoding="utf-8")
            print(f"Da ghi: {h_path}")

    log_path = out_dir / f"{args.exp}_tune_log.csv"
    pd.DataFrame(tune_log).to_csv(log_path, index=False, encoding="utf-8")
    print(f"\nDa ghi bang tune: {log_path}")


if __name__ == "__main__":
    main()