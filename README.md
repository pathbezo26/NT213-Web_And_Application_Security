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
> **An toàn:** mọi thử nghiệm tấn công và né tránh chỉ chạy trong lab Docker có
> mạng `internal: true`. DVWA và bWAPP không publish cổng ra host. Không đưa payload
> thử nghiệm vào hệ thống bên ngoài lab.

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
docker compose -f lab/docker-compose.yml up -d
```

---

## Lệnh chính

Chạy tất cả lệnh từ **thư mục gốc** của dự án.

| Việc | Lệnh | Tuần |
| --- | --- | --- |
| Quét Semgrep và chấm điểm Exp.1 (rule v0) | `python semgrep/run_scan.py --version v0` | 1–3 |
| Chấm rule v1 trên 12 testcase + T13–T14 | `python semgrep/run_scan.py --version v1 --rules semgrep/truc_rules --extra` | 3 |
| Sinh `malicious.csv` từ PayloadsAllTheThings (cần `data/raw/`) | `python scripts/build_malicious.py` | 2 |
| Sinh lại train/val/test và kiểm tra rò rỉ | `python data/processed/train_test_split/split_and_check.py` | 2 |
| Chạy thử trích đặc trưng ML | `python classical_ml/features.py` | 2–3 |
| Train ML cổ điển | `python classical_ml/train.py` | 3 |
| Chạy thử tokenize mức ký tự | `python deep_learning/tokenizer.py` | 2–3 |
| Train CNN-1D | `python deep_learning/train.py` | 3 |
| Giải thích mô hình (SHAP/LIME) | `python deep_learning/explainability/run_shap.py` | 5 |
| Sinh traffic thật trong lab | `python lab_verification/scripts/gen_traffic.py` | 5 |
| Kiểm tra payload né tránh | `python lab_verification/scripts/run_evasion.py` | 5 |
| Dashboard demo | `streamlit run dashboard/app.py` | 6 |
| Vẽ biểu đồ so sánh (dùng mock data khi chưa có kết quả) | `python notebooks/plot_results_template.py` | 3–6 |

---

## Trạng thái hiện tại

**Đã chạy được**

- `semgrep/`: rule v0 và 12 testcase. Exp.1 đạt **TP=6, FP=0, FN=0, TN=6**.
- `semgrep/truc_rules/php-cmdi-taint-v1.yml`: rule v1 bổ sung source `$_FILES` và sink
  backtick. Trên 12 testcase gốc + T13–T14 (`semgrep/extra_cases/`): v0 đạt
  TP=6, FN=2; v1 đạt **TP=8, FP=0, FN=0, TN=6**. Chi tiết trong
  `report/Danh_gia_semgrep_v0_v1_Tuan3.md`.
- `report/tom_tat_tai_lieu_tuan_1.md`: bảng khảo sát 6 tài liệu liên quan theo bài
  toán, phương pháp, dữ liệu, hạn chế và mức độ liên quan với đề tài.
- `classical_ml/features.py`, `deep_learning/tokenizer.py`
- `data/processed/train_test_split/split_and_check.py`: entry point theo nền tảng;
  kiểm tra dataset chuẩn và sinh ba tập theo schema 7 cột. Lần kiểm tra gần nhất đạt
  **PASS**, không có xung đột nhãn, payload trùng giữa tập hoặc rò rỉ `group_id`.
- `scripts/check_env.py`, `lab/docker-compose.yml`
- `report/`: tài liệu khảo sát dữ liệu (Tuần 1), mô tả dataset (Tuần 2), đánh giá
  Semgrep v0/v1 (Tuần 3), cơ chế né tránh (Tuần 6) và khung bảng kết quả trong báo
  cáo 9 chương.

**Dataset Tuần 2 — hoàn thành khoảng 90%**

- File chuẩn duy nhất: `data/processed/dataset_all.csv`.
- Tổng cộng **18.142** payload: 9.393 benign và 8.749 malicious.
- Train: 12.713; validation: 2.710; test: 2.719.
- Các file `data/splits/*.csv` được sinh tự động từ cột `split`, không được sửa
  riêng lẻ.
- Schema dùng cho ML/DL: `payload_id,input_text,label,source,category,group_id,notes`.
- Báo cáo kiểm tra gần nhất: `reports/week2_dataset_validation.txt`.
- Phần còn lại trước khi khóa dataset: rà soát chất lượng độc lập 678 mẫu
  `benign_special_char`, đối chiếu tài liệu gốc CSIC 2010 để xác nhận cách diễn
  giải nhãn `normal`, và bổ sung quy trình tái tạo end-to-end từ dữ liệu nguồn thô.

**Mới có khung (hoàn thiện trong Tuần 2–6)**

- `classical_ml/train.py`
- `deep_learning/train.py`, `deep_learning/explainability/run_shap.py`
- `lab_verification/scripts/*`
- `dashboard/app.py`
- `notebooks/plot_results_template.py`: vẽ 4 biểu đồ so sánh; hiện dùng mock data,
  sẽ đọc CSV thật khi các hướng ML/DL chốt tên file kết quả.

Khi chạy, các file khung chỉ in ra `Skeleton...`. Đây là hành vi đúng vì chưa có code thật.

---

## Cấu trúc thư mục

```text
t05-command-injection-detection/
├── data/
│   ├── raw/                     # Dữ liệu gốc (Commix, PayloadsAllTheThings, CSIC 2010), KHÔNG sửa
│   ├── processed/               # Dữ liệu đã chuẩn hóa: malicious, benign, evasion (*.csv)
│   ├── splits/                  # Train/val/test sinh từ dataset_all.csv
│   └── sqli_xss_testset/        # Test set SQLi/XSS cho Exp.5
├── semgrep/                     # Hướng 1: phân tích tĩnh PHP
│   ├── rules/                   # Rule taint phát hiện CI (CWE-78)
│   ├── truc_rules/              # Rule v1 (thêm $_FILES, backtick)
│   ├── testcases_php/           # 6 testcase vulnerable + 6 testcase safe
│   ├── extra_cases/             # T13–T14: ca bổ sung kiểm tra giới hạn của v0
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
├── scripts/
│   ├── check_env.py             # Kiểm tra môi trường
│   ├── build_malicious.py       # Sinh malicious.csv từ PayloadsAllTheThings
│   └── export_splits.py         # Xuất train/val/test từ dataset_all.csv
├── lab/
│   ├── docker-compose.yml       # Lab DVWA + bWAPP
│   └── README.md                # Cách dựng và kiểm tra lab
├── requirements.txt             # Thư viện Python
└── SETUP_TUAN1.md               # Hướng dẫn setup Tuần 1
```

Mỗi hướng (`semgrep/`, `classical_ml/`, `deep_learning/`, `lab_verification/`) có thư
mục `results/` riêng để lưu kết quả khi chạy.

### Tạo và kiểm tra các tập dữ liệu

Không chia lại ngẫu nhiên từ các file con. Cột `split` và `group_id` trong
`dataset_all.csv` là nguồn chuẩn. Chạy lệnh sau để kiểm tra và xuất lại các tập:

```bash
python data/processed/train_test_split/split_and_check.py
```

Lệnh chỉ xuất file khi dataset thỏa các điều kiện: schema hợp lệ, ID duy nhất, nhãn
thuộc `{0, 1}`, không có payload trùng giữa các tập, không có payload trùng nhưng
khác nhãn và mỗi `group_id` chỉ thuộc một split.

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
