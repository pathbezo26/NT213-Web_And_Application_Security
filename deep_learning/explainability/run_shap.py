"""Giải thích dự đoán CharCNN-1D bằng SHAP và LIME ở mức cụm ký tự.

Ví dụ (chạy từ thư mục gốc):
    python deep_learning/explainability/run_shap.py \
      --checkpoint deep_learning/best_cnn1d.pt \
      --input data/processed/dataset_all.csv --split val --method both

Kết quả gồm ``attributions.csv``, ``summary.json`` và heatmap PNG. Điểm dương
làm tăng P(Command Injection); điểm âm làm giảm xác suất đó. LIME được cài đặt
trực tiếp theo thuật toán perturbation + locally weighted Ridge để dùng cùng một
biểu diễn mặt nạ với SHAP và tránh khác biệt tokenizer.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
DL_DIR = HERE.parent
sys.path.insert(0, str(DL_DIR))

# Windows PowerShell cũ thường dùng cp1252 nên argparse/tiến độ tiếng Việt bị lỗi.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

OPERATORS = re.compile(
    r"\$\(|&&|\|\||>>|<<|2>|[;|&`$()<>]|\s+|[A-Za-z0-9_./:\\-]+|.", re.UNICODE
)
REQUIRED_COLUMNS = {"payload_id", "payload", "label"}


@dataclass(frozen=True)
class Explanation:
    payload_id: str
    payload: str
    true_label: int
    prediction: int
    confidence: float
    group: str
    segments: list[str]
    shap_values: np.ndarray | None
    lime_values: np.ndarray | None
    occluded_probabilities: np.ndarray


def segment_payload(payload: str, max_len: int | None = None) -> list[str]:
    """Tách payload nhưng vẫn ghép lại đúng nguyên văn phần CNN nhìn thấy."""
    visible = payload if max_len is None else payload[:max_len]
    return OPERATORS.findall(visible)


def apply_mask(segments: list[str], mask: np.ndarray) -> str:
    """Che segment bằng khoảng trắng cùng độ dài, không làm dính hai token."""
    return "".join(seg if bool(keep) else " " * len(seg) for seg, keep in zip(segments, mask))


def perturbation_predictor(
    segments: list[str], predict_payloads: Callable[[list[str]], np.ndarray]
) -> Callable[[np.ndarray], np.ndarray]:
    def predict(masks: np.ndarray) -> np.ndarray:
        masks = np.atleast_2d(masks)
        texts = [apply_mask(segments, row) for row in masks]
        return np.asarray(predict_payloads(texts), dtype=float)

    return predict


def lime_attributions(
    predict_masks: Callable[[np.ndarray], np.ndarray],
    n_features: int,
    num_samples: int,
    seed: int,
) -> np.ndarray:
    """LIME: perturb, weighted local Ridge, trả hệ số cho từng segment."""
    if n_features == 0:
        return np.array([], dtype=float)
    from sklearn.linear_model import Ridge

    rng = np.random.default_rng(seed)
    n = max(num_samples, 2 * n_features + 2)
    masks = rng.integers(0, 2, size=(n, n_features), dtype=np.int8)
    masks[0] = 1
    masks[1] = 0
    probabilities = predict_masks(masks)
    distances = np.sqrt(((1 - masks) ** 2).sum(axis=1) / n_features)
    weights = np.exp(-(distances**2) / (0.75**2))
    surrogate = Ridge(alpha=1.0, fit_intercept=True)
    surrogate.fit(masks, probabilities, sample_weight=weights)
    return np.asarray(surrogate.coef_, dtype=float)


def shap_attributions(
    predict_masks: Callable[[np.ndarray], np.ndarray], n_features: int, nsamples: int
) -> np.ndarray:
    if n_features == 0:
        return np.array([], dtype=float)
    try:
        import shap
    except ImportError as exc:
        raise SystemExit(
            "Thiếu thư viện SHAP. Cài môi trường dự án bằng: pip install -r requirements.txt"
        ) from exc
    background = np.zeros((1, n_features), dtype=float)
    target = np.ones((1, n_features), dtype=float)
    explainer = shap.KernelExplainer(predict_masks, background)
    values = explainer.shap_values(target, nsamples=nsamples, silent=True)
    if isinstance(values, list):
        values = values[0]
    return np.asarray(values, dtype=float).reshape(-1)


class CNNPredictor:
    def __init__(self, checkpoint: Path, batch_size: int = 512):
        try:
            import torch
        except ImportError as exc:
            raise SystemExit("Thiếu PyTorch; cài bản CPU/GPU theo README.md.") from exc
        from model_cnn1d import CharCNN1D
        from tokenizer import encode

        if not checkpoint.is_file():
            raise SystemExit(
                f"Không tìm thấy checkpoint: {checkpoint}\n"
                "Train theo deep_learning/README.md hoặc truyền --checkpoint tới best_cnn1d.pt."
            )
        ck = torch.load(checkpoint, map_location="cpu", weights_only=False)
        needed = {"state_dict", "vocab", "max_len", "emb_dim", "n_filters"}
        missing = needed - set(ck)
        if missing:
            raise SystemExit(f"Checkpoint thiếu trường bắt buộc: {sorted(missing)}")
        self.torch = torch
        self.encode = encode
        self.vocab = ck["vocab"]
        self.max_len = int(ck["max_len"])
        self.batch_size = batch_size
        self.model = CharCNN1D(
            vocab_size=len(self.vocab) + 2,
            emb_dim=int(ck["emb_dim"]),
            n_filters=int(ck["n_filters"]),
        )
        self.model.load_state_dict(ck["state_dict"])
        self.model.eval()

    def __call__(self, payloads: list[str]) -> np.ndarray:
        if not payloads:
            return np.array([], dtype=float)
        x = self.torch.tensor(
            [self.encode(p, self.vocab, self.max_len) for p in payloads], dtype=self.torch.long
        )
        probabilities = []
        with self.torch.no_grad():
            for start in range(0, len(x), self.batch_size):
                logits = self.model(x[start : start + self.batch_size])
                probabilities.append(self.torch.softmax(logits, dim=1)[:, 1].numpy())
        return np.concatenate(probabilities)


def assign_groups(df: pd.DataFrame, probabilities: np.ndarray, holdout_source: str | None) -> pd.DataFrame:
    selected = df.copy()
    selected["confidence"] = probabilities
    selected["prediction"] = (probabilities >= 0.5).astype(int)
    selected["group"] = "other"
    selected.loc[(selected.label == 1) & (selected.prediction == 1), "group"] = "true_positive"
    selected.loc[(selected.label == 0) & (selected.prediction == 0), "group"] = "true_negative"
    selected.loc[(selected.label == 1) & (selected.prediction == 0), "group"] = "false_negative"
    selected.loc[(selected.label == 0) & (selected.prediction == 1), "group"] = "false_positive"
    if holdout_source and "source" in selected.columns:
        match = selected["source"].astype(str).str.contains(holdout_source, regex=True, na=False)
        selected.loc[match, "group"] = "holdout_source"
    return selected


def choose_samples(df: pd.DataFrame, per_group: int, seed: int) -> pd.DataFrame:
    """Chọn ổn định; ưu tiên TN có confidence cao vì đây là benign khó."""
    frames = []
    order = ["true_positive", "true_negative", "false_negative", "false_positive", "holdout_source"]
    for group in order:
        part = df[df.group == group]
        if part.empty:
            continue
        if group == "true_negative":
            part = part.sort_values("confidence", ascending=False).head(per_group)
        else:
            part = part.sample(n=min(per_group, len(part)), random_state=seed)
        frames.append(part)
    return pd.concat(frames, ignore_index=True) if frames else df.head(0)


def explain_row(row, predictor, method: str, shap_samples: int, lime_samples: int, seed: int) -> Explanation:
    segments = segment_payload(str(row.payload), predictor.max_len)
    predict_masks = perturbation_predictor(segments, predictor)
    full_mask = np.ones((1, len(segments)), dtype=np.int8)
    confidence = float(predict_masks(full_mask)[0]) if segments else float(predictor([""])[0])
    shap_values = shap_attributions(predict_masks, len(segments), shap_samples) if method in {"shap", "both"} else None
    lime_values = lime_attributions(predict_masks, len(segments), lime_samples, seed) if method in {"lime", "both"} else None
    occluded = np.array([
        predict_masks(np.where(np.arange(len(segments)) == i, 0, 1))[0]
        for i in range(len(segments))
    ])
    return Explanation(
        str(row.payload_id), str(row.payload), int(row.label), int(confidence >= 0.5),
        confidence, str(row.group), segments, shap_values, lime_values, occluded,
    )


def explanation_rows(exp: Explanation) -> list[dict]:
    rows = []
    for i, segment in enumerate(exp.segments):
        rows.append({
            "payload_id": exp.payload_id, "group": exp.group, "true_label": exp.true_label,
            "prediction": exp.prediction, "confidence": round(exp.confidence, 8),
            "segment_index": i, "segment": segment,
            "shap_value": np.nan if exp.shap_values is None else exp.shap_values[i],
            "lime_value": np.nan if exp.lime_values is None else exp.lime_values[i],
            "probability_when_hidden": exp.occluded_probabilities[i],
            "occlusion_delta": exp.confidence - exp.occluded_probabilities[i],
        })
    return rows


def save_heatmap(exp: Explanation, output: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    methods = []
    if exp.shap_values is not None:
        methods.append(("SHAP", exp.shap_values))
    if exp.lime_values is not None:
        methods.append(("LIME", exp.lime_values))
    if not methods or not exp.segments:
        return
    width = max(8, min(18, len(exp.segments) * 0.6))
    fig, axes = plt.subplots(len(methods), 1, figsize=(width, 2.2 * len(methods)), squeeze=False)
    labels = [s.replace("\n", "\\n").replace("\t", "\\t") for s in exp.segments]
    for ax, (name, values) in zip(axes[:, 0], methods):
        vmax = max(float(np.abs(values).max()), 1e-9)
        image = ax.imshow(values.reshape(1, -1), cmap="RdBu_r", vmin=-vmax, vmax=vmax, aspect="auto")
        ax.set_yticks([])
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=55, ha="right")
        ax.set_title(f"{name} – {exp.payload_id} – P(malicious)={exp.confidence:.4f}")
        fig.colorbar(image, ax=ax, fraction=0.025, pad=0.02)
    fig.tight_layout()
    fig.savefig(output, dpi=160, bbox_inches="tight")
    plt.close(fig)


def mean_sample_spearman(frame: pd.DataFrame) -> float | None:
    """Tính đồng thuận theo từng payload rồi lấy trung bình, tránh trộn thang điểm."""
    values = []
    valid = frame.dropna(subset=["shap_value", "lime_value"])
    for _, part in valid.groupby("payload_id"):
        if len(part) < 2:
            continue
        value = part["shap_value"].corr(part["lime_value"], method="spearman")
        if not pd.isna(value):
            values.append(float(value))
    return round(float(np.mean(values)), 6) if values else None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--checkpoint", default=str(DL_DIR / "best_cnn1d.pt"))
    parser.add_argument("--input", required=True, help="CSV có payload_id, payload, label")
    parser.add_argument("--split", default=None, help="Chỉ giải thích split này, ví dụ val")
    parser.add_argument("--method", choices=("shap", "lime", "both"), default="both")
    parser.add_argument("--per-group", type=int, default=10)
    parser.add_argument("--holdout-source", default=None, help="Regex nhận diện source cần phân tích riêng")
    parser.add_argument("--shap-samples", type=int, default=256)
    parser.add_argument("--lime-samples", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--batch-size", type=int, default=512)
    parser.add_argument("--output-dir", default=str(DL_DIR / "results" / "explainability"))
    args = parser.parse_args()
    if args.per_group < 1 or args.shap_samples < 2 or args.lime_samples < 2:
        parser.error("--per-group phải >=1; số mẫu SHAP/LIME phải >=2")
    return args


def main() -> None:
    args = parse_args()
    np.random.seed(args.seed)
    input_path = Path(args.input)
    if not input_path.is_file():
        raise SystemExit(f"Không tìm thấy CSV đầu vào: {input_path}")
    df = pd.read_csv(input_path, keep_default_na=False)
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise SystemExit(f"CSV thiếu cột bắt buộc: {sorted(missing)}")
    if args.split:
        if "split" not in df.columns:
            raise SystemExit("Đã truyền --split nhưng CSV không có cột 'split'.")
        df = df[df["split"].astype(str) == args.split].reset_index(drop=True)
    if df.empty:
        raise SystemExit("Không có mẫu nào sau khi lọc dữ liệu.")
    df["label"] = pd.to_numeric(df["label"], errors="raise").astype(int)
    if not set(df.label).issubset({0, 1}):
        raise SystemExit("Cột label chỉ được chứa 0 hoặc 1.")

    predictor = CNNPredictor(Path(args.checkpoint), args.batch_size)
    probabilities = predictor(df["payload"].astype(str).tolist())
    candidates = assign_groups(df, probabilities, args.holdout_source)
    selected = choose_samples(candidates, args.per_group, args.seed)
    if selected.empty:
        raise SystemExit("Không chọn được mẫu thuộc nhóm phân tích nào.")

    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    all_rows = []
    for index, row in selected.iterrows():
        print(f"[{index + 1}/{len(selected)}] {row.payload_id} ({row.group})")
        exp = explain_row(row, predictor, args.method, args.shap_samples, args.lime_samples, args.seed + index)
        all_rows.extend(explanation_rows(exp))
        safe_id = re.sub(r"[^A-Za-z0-9_.-]+", "_", exp.payload_id)[:80]
        save_heatmap(exp, output / f"{safe_id}.png")

    attribution_df = pd.DataFrame(all_rows)
    attribution_path = output / "attributions.csv"
    attribution_df.to_csv(attribution_path, index=False, encoding="utf-8")
    summary = {
        "checkpoint": str(Path(args.checkpoint)), "input": str(input_path), "split": args.split,
        "method": args.method, "seed": args.seed, "samples_explained": int(len(selected)),
        "group_counts": selected["group"].value_counts().to_dict(),
        "mean_per_sample_shap_lime_spearman": mean_sample_spearman(attribution_df),
        "interpretation": "positive attribution increases P(malicious); negative attribution decreases it",
    }
    (output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Đã ghi {attribution_path}, summary.json và heatmap vào {output}")


if __name__ == "__main__":
    main()
