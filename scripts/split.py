"""
Chia dataset theo đúng quy trình mục 4.6 của kế hoạch v5:
  1) loại trùng đúng, cảnh báo nhãn xung đột
  2) gom nhóm gần trùng bằng TF-IDF char 3-gram + cosine > ngưỡng -> group_id
     (xử lý THEO KHỐI bằng ma trận thưa, tránh ma trận đặc O(n^2) khi > ~10k dòng)
  3) chia 70/15/15 theo group_id — GREEDY CÂN BẰNG NHÃN (không chỉ cân bằng số
     lượng dòng như GroupShuffleSplit thuần): sắp group theo kích thước giảm
     dần, mỗi group được gán vào tập (train/val/test) đang "thiếu" cả về số
     dòng lẫn số lượng từng nhãn so với mục tiêu nhất. Dùng khi dataset có vài
     group rất lớn (vd. truy vấn tìm kiếm gần giống nhau) lệch hẳn về 1 nhãn —
     GroupShuffleSplit thuần dễ dồn các group đó lệch hẳn vào 1 tập, làm %
     malicious khác nhau nhiều giữa train/val/test dù tổng số dòng vẫn đúng
     70/15/15.

Dùng:
    python scripts/split.py --input dataset/processed/dataset_all.csv --output dataset/processed/dataset_all.csv --seed 42
"""
import argparse

import numpy as np
import pandas as pd
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from sklearn.feature_extraction.text import TfidfVectorizer


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


def stratified_group_split(df, train_size, val_size, seed):
    """Gán mỗi group_id vào đúng 1 tập (train/val/test), ưu tiên cân bằng CẢ
    số dòng LẪN số lượng từng nhãn so với mục tiêu — khác GroupShuffleSplit
    thuần (chỉ cân bằng số dòng, bỏ qua nhãn).

    Thuật toán: xử lý group lớn nhất trước (ảnh hưởng nhiều nhất tới cân
    bằng). Với mỗi group, so sánh TỶ LỆ ĐÃ LẤP ĐẦY của mỗi tập — TRƯỚC khi
    thêm group đó — trên cả 3 tiêu chí (tổng dòng, số dòng nhãn 0, số dòng
    nhãn 1), rồi gán vào tập đang lấp đầy ÍT NHẤT (tỷ lệ current/target nhỏ
    nhất, tức "thiếu" nhiều nhất so với mục tiêu riêng của tập đó).

    LƯU Ý: không dùng độ lệch SAU khi thêm, vì ((current+size-target)/target)^2
    bị thiên vị theo kích thước target — cùng một lượng tuyệt đối thêm vào
    luôn làm tập có target NHỎ (val/test) "cải thiện" (tiến gần 0) nhanh hơn
    tập có target LỚN (train), nên công thức đó liên tục dồn group vào
    val/test, bỏ train lại sau cùng (đã phát hiện qua kiểm thử dữ liệu giả).
    Dùng tỷ lệ current/target (trước khi thêm) thì loại được thiên vị này,
    vì mọi tập đều bắt đầu từ 0/target = 0, ngang nhau.
    """
    rng = np.random.default_rng(seed)
    test_size = 1.0 - train_size - val_size

    group_sizes = df.groupby("group_id").size()
    label_counts = df.groupby(["group_id", "label"]).size().unstack(fill_value=0)
    for lbl in (0, 1):
        if lbl not in label_counts.columns:
            label_counts[lbl] = 0

    n_total = len(df)
    n0_total = int((df["label"] == 0).sum())
    n1_total = int((df["label"] == 1).sum())

    targets = {
        "train": {"n": n_total * train_size, 0: n0_total * train_size, 1: n1_total * train_size},
        "val":   {"n": n_total * val_size,   0: n0_total * val_size,   1: n1_total * val_size},
        "test":  {"n": n_total * test_size,  0: n0_total * test_size,  1: n1_total * test_size},
    }
    current = {s: {"n": 0, 0: 0, 1: 0} for s in targets}

    # Sắp theo kích thước giảm dần; tie-break ngẫu nhiên (seed) để có thể tái lập
    tie = rng.random(len(group_sizes))
    order = pd.DataFrame({"size": group_sizes.values, "tie": tie}, index=group_sizes.index)
    order = order.sort_values(["size", "tie"], ascending=[False, True]).index

    assignment = {}
    for gid in order:
        size = int(group_sizes[gid])
        n0 = int(label_counts.loc[gid, 0])
        n1 = int(label_counts.loc[gid, 1])
        best_split, best_score = None, None
        for s in targets:
            # Tỷ lệ đã lấp đầy HIỆN TẠI (trước khi thêm group này) trên từng
            # tiêu chí — nhỏ hơn nghĩa là tập này đang "thiếu" nhiều hơn so
            # với mục tiêu riêng của nó, nên nên được ưu tiên nhận group này.
            fill = (
                current[s]["n"] / max(targets[s]["n"], 1)
                + current[s][0] / max(targets[s][0], 1)
                + current[s][1] / max(targets[s][1], 1)
            )
            if best_score is None or fill < best_score:
                best_score, best_split = fill, s
        assignment[gid] = best_split
        current[best_split]["n"] += size
        current[best_split][0] += n0
        current[best_split][1] += n1

    return df["group_id"].map(assignment)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True, help="Ghi đè input nếu trùng đường dẫn, hoặc file mới")
    ap.add_argument("--threshold", type=float, default=0.9)
    ap.add_argument("--block-size", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--train-size", type=float, default=0.70)
    args = ap.parse_args()

    df = pd.read_csv(args.input, dtype=str, keep_default_na=False)
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
    df = df.drop_duplicates(subset=["norm", "label"]).reset_index(drop=True)
    print(f"Sau khi loại trùng đúng: {len(df)} dòng")

    # ---- 2) group_id bằng near-duplicate (theo khối) ----
    print(f"Đang tính group_id (ngưỡng cosine > {args.threshold}, khối {args.block_size})...")
    labels, n_comp = build_group_id(df["norm"], args.threshold, args.block_size)
    df["group_id"] = labels
    sizes = df["group_id"].value_counts()
    print(f"Số group: {n_comp}. Group lớn nhất: {sizes.max()} dòng ({sizes.max()/len(df):.1%} dataset). "
          f"5 group lớn nhất: {sizes.head(5).tolist()}")
    if sizes.max() > 0.3 * len(df):
        print(f"[!] Một group chiếm hơn 30% dataset — rủi ro connected-components bị 'bắc cầu' thành "
              f"một cụm khổng lồ (các cặp A~B~C nối chung dù A không giống C). Nên xem lại ngưỡng "
              f"--threshold hoặc báo lại trước khi chia, vì GroupShuffleSplit sẽ không tách được group này.")

    # ---- 3) chia 70/15/15 theo group_id, cân bằng cả số dòng lẫn nhãn ----
    val_size = (1.0 - args.train_size) / 2
    df["split"] = stratified_group_split(df, args.train_size, val_size, args.seed)

    assert (df.groupby("group_id")["split"].nunique() == 1).all(), "Có group bị tách sang nhiều tập — lỗi logic!"

    df = df.drop(columns=["norm"])
    df.to_csv(args.output, index=False, encoding="utf-8")

    print("\n===== BÁO CÁO =====")
    print(df.groupby(["split", "label"]).size().unstack(fill_value=0).to_string())
    counts = df["split"].value_counts()
    for s in ["train", "val", "test"]:
        n = counts.get(s, 0)
        print(f"{s}: {n} dòng ({n/len(df):.1%})")
    print(f"\nĐã ghi: {args.output}")


if __name__ == "__main__":
    main()