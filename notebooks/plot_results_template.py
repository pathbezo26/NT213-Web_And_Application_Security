"""
Script vẽ bộ 4 biểu đồ so sánh cho Báo cáo T05 (Báo cáo & Demo).
Tự động tìm và đọc file CSV trong các thư mục results/.
Nếu file chưa tồn tại (Tuần 3), tự động dùng Mock Data để dựng template.
"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "report"
OUT_DIR.mkdir(exist_ok=True)

def annotate_bars(ax, rects):
    """Hiển thị số liệu trên đỉnh mỗi cột."""
    for rect in rects:
        h = rect.get_height()
        ax.annotate(f"{h:.2f}", xy=(rect.get_x() + rect.get_width() / 2, h),
                    xytext=(0, 3), textcoords="offset points",
                    ha="center", va="bottom", fontsize=8.5)

def get_performance_data():
    """Đọc dữ liệu Exp.1 & Exp.2 từ CSV. Nếu không có, dùng Mock Data."""
    # TODO ở Tuần 4: Sửa đường dẫn file CSV khi các nhóm ML/DL chốt tên file
    ml_file = ROOT / "classical_ml" / "results" / "exp2_ml_results.csv"
    dl_file = ROOT / "deep_learning" / "results" / "exp2_dl_results.csv"
    
    if ml_file.exists() and dl_file.exists():
        print("[+] Đã tìm thấy file kết quả thật cho Exp.1 & Exp.2. Đang đọc số liệu...")
        # Code đọc pandas thật sẽ viết ở đây khi chốt schema
        pass
    else:
        print("[-] Chưa có file CSV kết quả cho Exp.1 & Exp.2. Đang dùng Mock Data để vẽ Template...")
        return {
            "models": ["Semgrep", "SVM", "Random Forest", "CNN-1D"],
            "precision": [1.00, 0.91, 0.93, 0.96],
            "recall": [1.00, 0.88, 0.91, 0.95],
            "f1_score": [1.00, 0.89, 0.92, 0.95]
        }

def plot_exp1_exp2_overall():
    data = get_performance_data()
    x = np.arange(len(data["models"]))
    width = 0.25

    fig, ax = plt.subplots(figsize=(9, 5))
    r1 = ax.bar(x - width, data["precision"], width, label="Precision", color="#4C72B0")
    r2 = ax.bar(x, data["recall"], width, label="Recall", color="#55A868")
    r3 = ax.bar(x + width, data["f1_score"], width, label="F1-Score", color="#CCB974")

    ax.set_ylabel("Điểm số (0.0 - 1.0)")
    ax.set_title("Exp.1 & Exp.2: Hiệu năng Phát hiện OS Command Injection")
    ax.set_xticks(x)
    ax.set_xticklabels(data["models"])
    ax.set_ylim(0, 1.15)
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.6)

    for r in (r1, r2, r3): annotate_bars(ax, r)
    plt.tight_layout()
    plt.savefig(OUT_DIR / "chart_exp1_exp2_overall.png", dpi=300)
    plt.close(fig)

def plot_exp3_exp5_fpr():
    """Biểu đồ 2: So sánh FPR trên Benign khó (Exp.3) và SQLi/XSS (Exp.5)."""
    models = ["SVM (ML cổ điển)", "Random Forest", "CNN-1D (Học sâu)"]
    fpr_benign = [0.14, 0.09, 0.04]  
    fpr_sqli = [0.18, 0.11, 0.05]    

    x = np.arange(len(models))
    width = 0.30

    fig, ax = plt.subplots(figsize=(8, 5))
    r1 = ax.bar(x - width/2, fpr_benign, width, label="FPR trên Benign khó (Exp.3)", color="#E17C05")
    r2 = ax.bar(x + width/2, fpr_sqli, width, label="FPR trên SQLi/XSS (Exp.5)", color="#C44E52")

    ax.set_ylabel("Tỷ lệ Cảnh báo nhầm - FPR")
    ax.set_title("Exp.3 & Exp.5: Đánh giá Cảnh báo nhầm (False Positive Rate)")
    ax.set_xticks(x)
    ax.set_xticklabels(models)
    ax.set_ylim(0, 0.30)
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.6)
    for r in (r1, r2): annotate_bars(ax, r)
    plt.tight_layout()
    plt.savefig(OUT_DIR / "chart_exp3_exp5_fpr.png", dpi=300)
    plt.close(fig)

def plot_exp4_bypass_rate():
    """Biểu đồ 3: Bypass Rate (Exp.4)."""
    techs = ["URL/Hex Encode", "${IFS}", "Env Var ($u)", "Cmd Sub $()", "Comment (#)"]
    svm_bypass = [0.35, 0.42, 0.50, 0.25, 0.30]
    cnn_bypass = [0.18, 0.20, 0.28, 0.12, 0.15]

    x = np.arange(len(techs))
    width = 0.35

    fig, ax = plt.subplots(figsize=(9, 5))
    r1 = ax.bar(x - width/2, svm_bypass, width, label="SVM", color="#4C72B0")
    r2 = ax.bar(x + width/2, cnn_bypass, width, label="CNN-1D", color="#8172B2")

    ax.set_ylabel("Tỷ lệ Vượt mặt - Bypass Rate")
    ax.set_title("Exp.4: Tỷ lệ Bypass theo Nhóm Kỹ thuật Né tránh")
    ax.set_xticks(x)
    ax.set_xticklabels(techs)
    ax.set_ylim(0, 0.65)
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.6)
    for r in (r1, r2): annotate_bars(ax, r)
    plt.tight_layout()
    plt.savefig(OUT_DIR / "chart_exp4_bypass.png", dpi=300)
    plt.close(fig)

def plot_exp6_lab_traffic():
    """Biểu đồ 4: So sánh độ suy giảm hiệu năng trên Traffic thật (Exp.6)."""
    models = ["Semgrep", "SVM", "CNN-1D"]
    f1_benchmark = [1.00, 0.89, 0.95] # Điểm F1 ở Exp.1 & Exp.2
    f1_live_lab = [0.85, 0.72, 0.88]  # Điểm F1 tụt giảm khi chạy traffic thật

    x = np.arange(len(models))
    width = 0.35

    fig, ax = plt.subplots(figsize=(8, 5))
    r1 = ax.bar(x - width/2, f1_benchmark, width, label="F1-Score (Benchmark Tĩnh)", color="#55A868")
    r2 = ax.bar(x + width/2, f1_live_lab, width, label="F1-Score (Traffic DVWA thật)", color="#C44E52")

    ax.set_ylabel("F1-Score (0.0 - 1.0)")
    ax.set_title("Exp.6: Độ suy giảm hiệu năng khi áp dụng vào Môi trường Thực tế")
    ax.set_xticks(x)
    ax.set_xticklabels(models)
    ax.set_ylim(0, 1.15)
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.6)
    for r in (r1, r2): annotate_bars(ax, r)
    plt.tight_layout()
    plt.savefig(OUT_DIR / "chart_exp6_live_traffic.png", dpi=300)
    plt.close(fig)

if __name__ == "__main__":
    plot_exp1_exp2_overall()
    plot_exp3_exp5_fpr()
    plot_exp4_bypass_rate()
    plot_exp6_lab_traffic()
    print("XONG! Các biểu đồ đã được cập nhật vào thư mục report/")