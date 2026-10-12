# T05 — Phát hiện OS Command Injection: Semgrep vs ML cổ điển vs CNN-1D

Đồ án môn **Bảo mật Web & Ứng dụng (NT213)**. Đồ án so sánh ba hướng phát hiện
OS Command Injection (CWE-78):

| Hướng | Kỹ thuật | Đầu vào | Thư mục |
| --- | --- | --- | --- |
| 1. Phân tích tĩnh (SAST) | Semgrep, rule taint-mode | Mã nguồn PHP | [`semgrep/`](semgrep/) |
| 2. Học máy cổ điển | TF-IDF char n-gram + đặc trưng thủ công, SVM / RandomForest | Chuỗi payload | [`classical_ml/`](classical_ml/) |
| 3. Học sâu | CNN-1D mức ký tự | Chuỗi payload | [`deep_learning/`](deep_learning/) |

> **Phạm vi:** đồ án phát hiện ở mức payload, tức là phân loại chuỗi đầu vào. Kết quả
> không chứng minh mô hình hiểu được ngữ cảnh thực thi lệnh.
>
> **An toàn:** mọi thử nghiệm tấn công và né tránh chỉ chạy trong lab Docker **cách ly**
> (mạng `internal`, không map cổng ra host).

---

## Mục lục

1. [Cài đặt](#cài-đặt)
2. [Lệnh chính](#lệnh-chính)
3. [Trạng thái hiện tại](#trạng-thái-hiện-tại)
4. [Cấu trúc thư mục](#cấu-trúc-thư-mục)
5. [Nguyên tắc dữ liệu](#nguyên-tắc-dữ-liệu)
6. [Tái lập kết quả](#tái-lập-kết-quả)

---

## Cài đặt

Yêu cầu: Python 3.10+, Docker (cho lab), Git. Hướng dẫn chi tiết cho Tuần 1 nằm trong
[`SETUP_TUAN1.md`](SETUP_TUAN1.md).

```bash
# 1) Tạo môi trường ảo
python -m venv .venv
source .venv/bin/activate          # Linux/macOS
# .venv\Scripts\activate           # Windows

# 2) Cài thư viện
pip install -r requirements.txt

# 3) Cài PyTorch bản CPU (tách riêng vì phụ thuộc CPU/GPU)
pip install torch --index-url https://download.pytorch.org/whl/cpu

# 4) Kiểm tra môi trường, lưu minh chứng vào reports/env_check.txt
python scripts/check_env.py

# 5) Khởi động lab DVWA + bWAPP
docker compose up -d
```

---

## Lệnh chính

Chạy tất cả lệnh từ **thư mục gốc** của dự án.

| Việc | Lệnh | Tuần |
| --- | --- | --- |
| Quét Semgrep và chấm điểm Exp.1 | `python semgrep/run_scan.py --version v0` | 1–3 |
| Chia tập và kiểm tra rò rỉ | `python data/processed/train_test_split/split_and_check.py` | 2 |
| Chạy thử trích đặc trưng ML | `python classical_ml/features.py` | 2–3 |
| Train ML cổ điển | `python classical_ml/train.py` | 3 |
| Chạy thử tokenize mức ký tự | `python deep_learning/tokenizer.py` | 2–3 |
| Train CNN-1D | `python deep_learning/train.py` | 3 |
| Giải thích mô hình (SHAP/LIME) | `python deep_learning/explainability/run_shap.py` | 5 |
| Sinh traffic thật trong lab | `python lab_verification/scripts/gen_traffic.py` | 5 |
| Kiểm tra payload né tránh | `python lab_verification/scripts/run_evasion.py` | 5 |
| Dashboard demo | `streamlit run dashboard/app.py` | 6 |

---

## Trạng thái hiện tại

**Đã chạy được**

- `semgrep/`: rule v0 và 12 testcase. Exp.1 đạt **TP=6, FP=0, FN=0, TN=6**.
- `classical_ml/features.py`, `deep_learning/tokenizer.py`
- `data/processed/train_test_split/split_and_check.py`
- `scripts/check_env.py`, `docker-compose.yml`

**Mới có khung (hoàn thiện trong Tuần 2–6)**

- `classical_ml/train.py`
- `deep_learning/train.py`, `deep_learning/explainability/run_shap.py`
- `lab_verification/scripts/*`
- `dashboard/app.py`

Khi chạy, các file khung chỉ in ra `Skeleton...`. Đây là hành vi đúng vì chưa có code thật.

---

## Cấu trúc thư mục

```text
t05-command-injection-detection/
├── data/
│   ├── raw/                     # Dữ liệu gốc (Commix, PayloadsAllTheThings, CSIC 2010), KHÔNG sửa
│   ├── processed/               # Dữ liệu đã chuẩn hóa: malicious, benign, evasion (*.csv)
│   │   └── train_test_split/    # Chia tập theo group_id + kiểm tra rò rỉ
│   └── sqli_xss_testset/        # Test set SQLi/XSS cho Exp.5
├── semgrep/                     # Hướng 1: phân tích tĩnh PHP
│   ├── rules/                   # Rule taint phát hiện CI (CWE-78)
│   ├── testcases_php/           # 6 testcase vulnerable + 6 testcase safe
│   └── run_scan.py              # Quét và chấm TP/FP/FN/TN (Exp.1)
├── classical_ml/                # Hướng 2: SVM / RandomForest
│   ├── features.py              # Trích đặc trưng
│   └── train.py                 # Train model
├── deep_learning/               # Hướng 3: CNN-1D mức ký tự
│   ├── tokenizer.py             # Tokenize mức ký tự
│   ├── model_cnn1d.py           # Kiến trúc CNN-1D
│   ├── train.py                 # Train model
│   └── explainability/          # SHAP/LIME giải thích mô hình
├── lab_verification/            # Kiểm chứng trên lab Docker (traffic thật, né tránh)
├── dashboard/                   # Demo Streamlit
├── notebooks/                   # EDA, biểu đồ, phân tích lỗi
├── report/                      # Đề cương, báo cáo, slide
├── scripts/check_env.py         # Kiểm tra môi trường
├── docker-compose.yml           # Lab DVWA + bWAPP (mạng cách ly)
├── requirements.txt             # Thư viện Python
└── SETUP_TUAN1.md               # Hướng dẫn setup Tuần 1
```

Mỗi hướng (`semgrep/`, `classical_ml/`, `deep_learning/`, `lab_verification/`) có thư
mục `results/` riêng để lưu kết quả khi chạy.

---

## Nguyên tắc dữ liệu

Các nguyên tắc dưới đây giúp tránh kết quả đẹp nhưng sai lệch:

1. **Benign viết tay độc lập.** Không tạo `benign_handwritten.csv` bằng cách xóa ký tự
   khỏi payload độc. Nếu làm vậy, mô hình chỉ học cách phát hiện ký tự bị xóa.
2. **Chia tập theo `group_id`.** Các biến thể gần giống nhau của cùng một payload phải
   nằm chung một tập, không được rơi vào cả train lẫn test.
3. **Đo FPR riêng** trên tập benign "khó" (input hợp lệ có chứa ký tự đặc biệt).
4. **Bypass rate** chỉ tính trên những payload **đã chạy được lệnh** trong lab.
5. **CSIC 2010:** chỉ lấy phần `normal`, sau khi đã đọc tài liệu nhãn. Request
   `anomalous` không đồng nghĩa với Command Injection.

---

## Tái lập kết quả

- Cố định seed (`SEED = 42`) trong mọi script train và chia tập.
- Khóa phiên bản thư viện sau khi môi trường đã ổn định:

  ```bash
  pip freeze > requirements.lock.txt
  ```
