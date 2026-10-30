"""
Chia dataset theo quy trình sau:
  1) loại trùng đúng, cảnh báo nhãn xung đột
  2) gom nhóm gần trùng bằng TF-IDF char 3-gram + cosine > ngưỡng -> group_id
     (xử lý THEO KHỐI bằng ma trận thưa, tránh ma trận đặc O(n^2) khi > ~10k dòng)
  3) chia 70/15/15 theo group_id — GREEDY CÂN BẰNG NHÃN (không chỉ cân bằng số
     lượng dòng như GroupShuffleSplit thuần): sắp group theo kích thước giảm
     dần, mỗi group được gán vào tập (train/val/test). Dùng khi data có vài
     group rất lớn (vd. truy vấn tìm kiếm gần giống nhau) lệch hẳn về 1 nhãn —
     GroupShuffleSplit thuần dễ dồn các group đó lệch hẳn vào 1 tập, làm %
     malicious khác nhau nhiều giữa train/val/test dù tổng số dòng vẫn đúng
     70/15/15.

  (mặc định) GOM NHÓM THEO KHUÔN cho dòng malicious: trước khi tính cosine, che
     chuỗi ngẫu nhiên do bộ sinh payload tạo ra — chuỗi IN HOA >= 5 ký tự (marker
     Commix như RPJJIB, $IFSBTAEIF) -> "X", dãy chữ số (vd. $((13+69))) -> "0".
     Lý do: wordlist Commix thực chất ~644 khuôn, chỉ khác marker/số ngẫu nhiên;
     không che thì cosine < 0.9 giữa các payload cùng khuôn -> cùng khuôn rải khắp
     train/val/test -> rò rỉ mức khuôn, F1 val cao giả (kiểm chứng: train không có
     PayloadsAllTheThings thì chỉ phát hiện 2.9% payload của nguồn đó).
     CHỈ che dòng malicious: che benign sẽ gộp mọi IP thành 0.0.0.0 dù là giá trị khác nhau thật.
     Tắt bằng --no-mask-template (chỉ để so sánh với cách cũ).

Dùng:
    py scripts/split-v5.py --input data/processed/dataset_all.csv \
        --output data/processed/dataset_all.csv --seed 42
"""
import argparse
import re

import numpy as np
import pandas as pd
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from sklearn.feature_extraction.text import TfidfVectorizer


_UPPER_MARKER = re.compile(r"[A-Z]{5,}")
_DIGITS = re.compile(r"\d+")
_SEP_QUOTE_SPACE = re.compile(r"[;|&'\"`\s]")


def mask_template(text):
    """Chỉ dùng để gom nhóm (không đổi payload): che marker/số ngẫu nhiên và bỏ dấu
    nối/dấu nháy/khoảng trắng, để các biến thể chỉ khác nhau ở đó
    (vd. '| ls -laR /etc', '; ls -laR /etc', '&& ls -laR /etc', 'sleep 5'/'sleep 10')
    rơi vào cùng một nhóm, không bị rải sang train/val/test."""
    t = _DIGITS.sub("0", _UPPER_MARKER.sub("X", text))
    return _SEP_QUOTE_SPACE.sub("", t)


def build_group_id(payloads, threshold=0.9, block_size=2000):
    """Connected components trên đồ thị tương đồng cosine, tính theo khối để
    tránh giữ ma trận NxN đặc trong bộ nhớ (N lớn hơn ~10k thì dense sẽ rất nặng)."""
    vec = TfidfVectorizer(analyzer="char", ngram_range=(3, 3))
    X = vec.fit_transform(payloads)  # TfidfVectorizer mặc định L2-normalize từng dòng
    n = X.shape[0]

    rows, cols, data = [], [], []
    for start in range(0, n, block_size):
        end = min(start + block_size, n)
        # Vì các dòng đã L2-normalize, tích vô hướng = cosine similarity.
        # X thưa nên phép nhân X_block . X^T cho kết quả thưa, không tạo ma trận đặc.
        block_sim = (X[start:end] @ X.T).tocoo()
        mask = block_sim.data > threshold
        rows.extend(block_sim.row[mask] + start)
        cols.extend(block_sim.col[mask])
        data.extend(block_sim.data[mask])
        print(f"  đã xử lý khối {start}-{end}/{n}", end="\r")
    print()

    adj = coo_matrix((data, (rows, cols)), shape=(n, n))
    n_comp, labels = connected_components(adj, directed=False)
    return labels, n_comp


def merge_identical(labels, group_text):
    """Gộp thêm các dòng có chuỗi gom nhóm (sau khi che) GIỐNG HỆT nhau vào cùng group.
    Cần vì chuỗi < 3 ký tự (vd. ';id' -> 'id') không sinh 3-gram nào -> vector TF-IDF
    bằng 0 -> cosine 0 với mọi dòng -> thành group riêng dù giống hệt nhau
    (dữ liệu thật: 16 payload họ 'id' từng bị rải sang cả train và val)."""
    n = len(labels)
    _, first = np.unique(group_text.to_numpy(), return_inverse=True)
    rep = pd.Series(labels).groupby(first).transform("first").to_numpy()
    k = int(labels.max()) + 1
    adj = coo_matrix((np.ones(n), (labels, rep)), shape=(k, k))
    n_comp, comp = connected_components(adj, directed=False)
    return comp[labels], n_comp


def stratified_group_split(df, train_size, val_size, seed):
    """Gán mỗi group_id vào đúng 1 tập (train/val/test), ưu tiên cân bằng CẢ
    số dòng LẪN số lượng từng nhãn so với mục tiêu — khác GroupShuffleSplit
    thuần (chỉ cân bằng số dòng, bỏ qua nhãn).

    Thuật toán ("đổ nước"): xử lý group lớn nhất trước. Với mỗi group, tính
    TỶ LỆ LẤP ĐẦY SAU KHI THÊM group vào từng tập: (current + group) / target,
    chỉ trên các tiêu chí group đó đóng góp (tổng dòng + nhãn mà group có),
    lấy giá trị lớn nhất trong các tiêu chí -> gán vào tập có giá trị NHỎ NHẤT,
    tức tập vẫn "vơi" nhất sau khi nhận group.

    Lịch sử sửa (đã kiểm chứng bằng dữ liệu giả + dữ liệu Commix thật):
      v1  ((proj - target)/target)^2       -> thiên vị dồn group vào val/test (target nhỏ).
      v2  current/target TRƯỚC khi thêm   -> bỏ qua kích thước group: khi gom theo
          khuôn, Commix chỉ còn ~38 group (lớn nhất ~1500 dòng) và group ~1450 dòng
          bị đặt vào val dù val chỉ cần ~880 dòng malicious -> val 89% malicious.
      v3  (current + group)/target SAU khi thêm — group lớn tự rơi vào train vì train
          có target lớn nhất. Nhưng chỉ cân theo NHÃN: group Commix lớn xếp trước lấp
          gần đầy chỗ malicious của train, group PayloadsAllTheThings nhỏ xếp sau bị
          dồn sang val/test (dữ liệu thật: command_exec chỉ 11% ở train).
      v4  (bản hiện tại) cân theo TẦNG: mỗi nguồn malicious (cột source) và mỗi nhóm
          benign (cột category) là một tầng có target 70/15/15 riêng, cộng tổng số dòng
          và từng nhãn. Mỗi nguồn/nhóm vì vậy có ~70% ở train.
    """
    rng = np.random.default_rng(seed)
    test_size = 1.0 - train_size - val_size
    fracs = {"train": train_size, "val": val_size, "test": test_size}

    # Tầng: malicious theo source, benign theo category (nếu có cột), luôn kèm nhãn
    mal_key = df["source"].astype(str) if "source" in df.columns else pd.Series("", index=df.index)
    ben_key = df["category"].astype(str) if "category" in df.columns else pd.Series("", index=df.index)
    stratum = np.where(df["label"] == 1, "mal:" + mal_key, "ben:" + ben_key)
    strat_df = pd.DataFrame({"group_id": df["group_id"].values, "label": df["label"].values,
                             "stratum": stratum})

    group_sizes = strat_df.groupby("group_id").size()
    label_counts = strat_df.groupby(["group_id", "label"]).size().unstack(fill_value=0)
    stratum_counts = strat_df.groupby(["group_id", "stratum"]).size().unstack(fill_value=0)
    for lbl in (0, 1):
        if lbl not in label_counts.columns:
            label_counts[lbl] = 0

    totals = {"n": len(df), 0: int((df["label"] == 0).sum()), 1: int((df["label"] == 1).sum())}
    for st, cnt in pd.Series(stratum).value_counts().items():
        totals[st] = int(cnt)
    dims_all = list(totals)

    targets = {s: {d: totals[d] * f for d in dims_all} for s, f in fracs.items()}
    current = {s: {d: 0 for d in dims_all} for s in fracs}

    # Sắp theo kích thước giảm dần; tie-break ngẫu nhiên (seed) để có thể tái lập
    tie = rng.random(len(group_sizes))
    order = pd.DataFrame({"size": group_sizes.values, "tie": tie}, index=group_sizes.index)
    order = order.sort_values(["size", "tie"], ascending=[False, True]).index

    assignment = {}
    for gid in order:
        add = {"n": int(group_sizes[gid]), 0: int(label_counts.loc[gid, 0]), 1: int(label_counts.loc[gid, 1])}
        row = stratum_counts.loc[gid]
        for st, cnt in row[row > 0].items():
            add[st] = int(cnt)
        dims = [d for d in add if add[d] > 0]
        best_split, best_score = None, None
        for s in fracs:
            # Tỷ lệ lấp đầy SAU khi thêm group, trên các tiêu chí group đóng góp;
            # lấy max để không làm tràn tiêu chí nào. Tie-break: tổng tỷ lệ hiện tại.
            proj = max((current[s][d] + add[d]) / max(targets[s][d], 1) for d in dims)
            tie_break = sum(current[s][d] / max(targets[s][d], 1) for d in dims_all)
            score = (proj, tie_break)
            if best_score is None or score < best_score:
                best_score, best_split = score, s
        assignment[gid] = best_split
        for d, v in add.items():
            current[best_split][d] += v

    return df["group_id"].map(assignment)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True, help="Ghi đè input nếu trùng đường dẫn, hoặc file mới")
    ap.add_argument("--threshold", type=float, default=0.9)
    ap.add_argument("--block-size", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--train-size", type=float, default=0.70)
    ap.add_argument("--no-mask-template", action="store_true",
                    help="Tắt gom nhóm theo khuôn (cách cũ, chỉ để so sánh — có rò rỉ mức khuôn)")
    ap.add_argument("--force-resplit", action="store_true",
                    help="Cho phép chia lại file ĐÃ có cột split (sẽ làm đổi tập test)")
    args = ap.parse_args()

    df = pd.read_csv(args.input, dtype=str, keep_default_na=False)
    if "split" in df.columns and not args.force_resplit:
        raise SystemExit("File đã có cột split -> dừng để không vô tình chia lại (đổi tập test). "
                         "Chỉ khi CHỦ ĐÍCH chia lại mới thêm --force-resplit.")
    df["label"] = df["label"].astype(int)

    # ---- 1) loại trùng đúng, cảnh báo nhãn xung đột ----
    df["norm"] = df["payload"].str.strip()
    conflict = df.groupby("norm")["label"].nunique() > 1
    n_conflict = int(conflict.sum())
    print(f"Chuỗi bị gán nhãn xung đột: {n_conflict}")
    if n_conflict:
        conflict_rows = df[df["norm"].isin(conflict[conflict].index)]
        conflict_rows.to_csv(args.output.replace(".csv", "_label_conflicts.csv"), index=False, encoding="utf-8")
        print(f"  -> đã ghi {len(conflict_rows)} dòng xung đột ra file *_label_conflicts.csv, "
              f"GIẢI QUYẾT BẰNG TAY trước khi chia (kế hoạch yêu cầu bắt buộc).")
        raise SystemExit("Dừng: còn chuỗi xung đột nhãn, giải quyết xong mới chia.")
    df = df.drop_duplicates(subset=["norm", "label"]).reset_index(drop=True)
    print(f"Sau khi loại trùng đúng: {len(df)} dòng")

    # ---- 2) group_id bằng near-duplicate (theo khối) ----
    group_text = df["norm"].copy()
    if not args.no_mask_template:
        mal = df["label"] == 1
        group_text[mal] = group_text[mal].map(mask_template)
        print(f"Gom nhóm theo khuôn: đã che marker/số ngẫu nhiên ở {int(mal.sum())} dòng malicious "
              f"-> còn {group_text[mal].nunique()} khuôn khác nhau.")
    else:
        print("[!] --no-mask-template: gom nhóm KHÔNG che marker — có rò rỉ mức khuôn.")
    print(f"Đang tính group_id (ngưỡng cosine > {args.threshold}, khối {args.block_size})...")
    labels, n_comp = build_group_id(group_text, args.threshold, args.block_size)
    labels, n_comp = merge_identical(labels, group_text)
    df["group_id"] = labels
    sizes = df["group_id"].value_counts()
    print(f"Số group: {n_comp}. Group lớn nhất: {sizes.max()} dòng ({sizes.max()/len(df):.1%} dataset). "
          f"5 group lớn nhất: {sizes.head(5).tolist()}")
    n_mal_groups = df[df["label"] == 1]["group_id"].nunique()
    n_ben_groups = df[df["label"] == 0]["group_id"].nunique()
    print(f"Số group chứa malicious: {n_mal_groups} | chứa benign: {n_ben_groups}")
    if "source" in df.columns:
        print("Số group malicious theo source:")
        print(df[df["label"] == 1].groupby("source")["group_id"].nunique().to_string())
    if sizes.max() > 0.3 * len(df):
        print(f"[!] Một group chiếm hơn 30% dataset — rủi ro connected-components bị 'bắc cầu' thành "
              f"một cụm khổng lồ (các cặp A~B~C nối chung dù A không giống C). Nên xem lại ngưỡng "
              f"--threshold hoặc báo lại trước khi chia, vì GroupShuffleSplit sẽ không tách được group này.")

    # ---- 3) chia 70/15/15 theo group_id, cân bằng cả số dòng lẫn nhãn ----
    val_size = (1.0 - args.train_size) / 2
    df["split"] = stratified_group_split(df, args.train_size, val_size, args.seed)

    assert (df.groupby("group_id")["split"].nunique() == 1).all(), "Có group bị tách sang nhiều tập — lỗi logic!"
    n_leak = int((pd.DataFrame({"g": group_text.values, "s": df["split"].values})
                  .groupby("g")["s"].nunique() > 1).sum())
    print(f"Kiểm tra rò rỉ: khuôn (chuỗi sau khi che) nằm ở >1 tập = {n_leak}")
    assert n_leak == 0, "Có khuôn bị rải sang nhiều tập — lỗi logic!"

    df = df.drop(columns=["norm"])
    df.to_csv(args.output, index=False, encoding="utf-8")

    print("\n===== BÁO CÁO =====")
    print(df.groupby(["split", "label"]).size().unstack(fill_value=0).to_string())
    if "source" in df.columns:
        print("\nMalicious theo source x split:")
        print(df[df["label"] == 1].groupby(["source", "split"]).size().unstack(fill_value=0).to_string())
    if "category" in df.columns:
        print("\nBenign theo category x split:")
        print(df[df["label"] == 0].groupby(["category", "split"]).size().unstack(fill_value=0).to_string())
    counts = df["split"].value_counts()
    for s in ["train", "val", "test"]:
        n = counts.get(s, 0)
        print(f"{s}: {n} dòng ({n/len(df):.1%})")
    print(f"\nĐã ghi: {args.output}")
    print("Nhắc: từ giờ KHÓA file split, không sửa tập test.")


if __name__ == "__main__":
    main()