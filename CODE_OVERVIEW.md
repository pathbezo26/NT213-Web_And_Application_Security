# Giải thích các file trong dự án

Tài liệu này giải thích ngắn gọn từng file trong dự án T05: file đó làm gì và đang ở
trạng thái nào. Cách cài đặt và chạy xem trong [README.md](README.md).

Ý nghĩa cột **Trạng thái**:

- **Chạy được**: đã có code hoặc nội dung thật.
- **Khung**: mới có sườn; khi chạy, file code chỉ in `Skeleton...`.
- **Dữ liệu mẫu**: chỉ có vài dòng ví dụ, sẽ thay bằng dữ liệu thật ở Tuần 2.
- **Trống**: thư mục hoặc file mới giữ chỗ.

---

## Thư mục gốc

| File | Làm gì | Trạng thái |
| --- | --- | --- |
| `README.md` | Trang giới thiệu repo: cách cài, bảng lệnh chính, phạm vi, nguyên tắc dữ liệu. Giúp người ngoài nhóm chạy lại được dự án (yêu cầu của Tuần 8). | Chạy được |
| `SETUP_TUAN1.md` | Hướng dẫn từng bước cho Tuần 1: WSL, venv, Semgrep, Docker, tải dữ liệu, đọc paper. | Chạy được |
| `requirements.txt` | Danh sách thư viện Python. `pip install -r requirements.txt` giúp cả nhóm dùng chung một môi trường. PyTorch cài riêng vì phụ thuộc CPU/GPU. | Chạy được |
| `docker-compose.yml` | Dựng 2 web có lỗ hổng sẵn (DVWA, bWAPP) bằng một lệnh. Mạng `internal: true` nên lab không ra được Internet và không mở cổng ra máy host. Tên image chưa được kiểm chứng khi chạy thật, có thể phải đổi. | Chạy được |
| `.gitignore` | Không đẩy lên GitHub: `.venv`, dữ liệu gốc `data/raw/`, model đã train, file kết quả `*/results/*.csv`. Lý do: payload tấn công không nên nằm trên repo công khai; model và kết quả có thể sinh lại. | Chạy được |

> **Lưu ý:** vì `results/*.csv` bị bỏ qua, file `exp1_semgrep_v0.csv` sẽ không lên
> GitHub. Muốn nộp làm bằng chứng thì chụp màn hình hoặc dán số liệu vào báo cáo.

---

## `semgrep/`: Hướng 1, rule-based

Đây là phần hoàn chỉnh nhất sau Tuần 1.

| File | Làm gì |
| --- | --- |
| `rules/php-cmdi-taint.yml` | Rule phát hiện lỗi trong mã PHP, gồm 3 phần. **Source** là nơi dữ liệu người dùng đi vào (`$_GET`, `$_POST`, `$_REQUEST`, `$_COOKIE`, `$_SERVER`). **Sink** là hàm chạy lệnh (`system`, `exec`, `shell_exec`, `passthru`, `popen`, `proc_open`). **Sanitizer** là hàm làm sạch (`escapeshellarg`). Dữ liệu đi từ source tới sink mà không qua sanitizer thì rule báo lỗi. Riêng `proc_open` với mảng đối số bị loại trừ vì không gọi shell. |
| `testcases_php/vulnerable/` (T01–T06) | 6 đoạn PHP có lỗi, rule **bắt buộc phải báo**. T01 nối chuỗi trực tiếp (giống DVWA), T02 qua biến trung gian, T03 dùng `$_POST`, T04 qua hàm lọc tự viết, T05 gán qua nhiều bước, T06 dùng `sprintf`. |
| `testcases_php/safe/` (T07–T12) | 6 đoạn PHP an toàn, rule **không được báo**. T07 dùng API PHP thay vì shell, T08 dùng `proc_open` dạng mảng, T09 dùng allowlist, T10 dùng hằng số, T11 có ký tự đặc biệt nhưng chỉ là dữ liệu, T12 đã qua `escapeshellarg`. T11 và T12 là ca biên để thử độ chính xác của rule. |
| `run_scan.py` | Chạy Semgrep trên 12 file, so với nhãn đúng, in TP/FP/FN/TN và ghi CSV. Nhãn đúng lấy theo tên thư mục (`vulnerable` hoặc `safe`). |
| `results/` | Nơi `run_scan.py` ghi file CSV kết quả. |

Hiện rule đạt **TP=6, FP=0, FN=0, TN=6**. Tuy nhiên bộ test chỉ có 12 mẫu do nhóm tự
viết, nên điểm 100% chưa chứng minh được rule tốt. Chỉ khi thêm ca mới mà rule vẫn đúng
thì mới kết luận được điều đó.

---

## `data/`: Dữ liệu

| File | Làm gì | Trạng thái |
| --- | --- | --- |
| `raw/{csic2010, commix_payloads, payloadsallthethings}/` | Nơi để dữ liệu gốc tải về, giữ nguyên, không sửa (Bước 8 của setup). Hiện chỉ có file `.gitkeep` để Git giữ thư mục rỗng. | Trống |
| `processed/malicious.csv` | Payload độc hại, `label=1`. | Dữ liệu mẫu (3 dòng) |
| `processed/benign_handwritten.csv` | Input lành tính viết tay độc lập, `label=0`. Ví dụ `ping -c 4 8.8.8.8` hay `report_2024;final.pdf` có ký tự đặc biệt nhưng vẫn hợp lệ. Mục đích là dạy model rằng có ký tự đặc biệt chưa chắc là tấn công. Không được tạo bằng cách xóa ký tự khỏi payload độc. | Dữ liệu mẫu (3 dòng) |
| `processed/benign_csic_selected.csv` | Phần lành tính chọn lọc từ CSIC 2010. Chỉ lấy request `normal` sau khi đã đọc tài liệu nhãn. | Trống (chỉ có tiêu đề) |
| `processed/evasion_payloads.csv` | Payload né tránh, dùng ở Tuần 3–5 để đo bypass rate. | Dữ liệu mẫu (2 dòng) |
| `processed/train_test_split/split_and_check.py` | Chia train/val/test theo tỉ lệ 70/15/15, mỗi `group_id` nằm trọn trong một tập. Sau đó kiểm tra không có nhóm hoặc chuỗi nào bị trùng giữa các tập. | Chạy được, cần dữ liệu thật mới ra kết quả |
| `sqli_xss_testset/README.md` | Mô tả bộ test SQLi/XSS cho Exp.5, dùng để kiểm tra model có nhầm SQLi/XSS thành CI không. | Chỉ có mô tả |

Các cột chung của file CSV:

| Cột | Ý nghĩa |
| --- | --- |
| `payload_id` | Mã của mẫu |
| `input_text` | Chuỗi payload |
| `label` | `1` là CI, `0` là lành tính |
| `source` | Nguồn gốc của mẫu |
| `group_id` | Nhóm biến thể, dùng khi chia tập |

---

## `classical_ml/`: Hướng 2, ML cổ điển

| File | Làm gì | Trạng thái |
| --- | --- | --- |
| `features.py` | Tính đặc trưng thủ công cho một chuỗi: độ dài, tỉ lệ ký tự đặc biệt, số ký tự meta của shell (`` ; \| & ` $ ( ) < > ``), có `$(...)` hay backtick không, có dấu phân tách lệnh không. Chạy thử sẽ in ra 3 ví dụ. Phần TF-IDF n-gram mới là TODO. | Chạy được một nửa |
| `train.py` | Sườn huấn luyện SVM và RandomForest. | Khung |
| `models/`, `results/` | Nơi lưu model và kết quả. `results/README.md` ghi schema cột, dùng chung với DL. | Trống |

---

## `deep_learning/`: Hướng 3, CNN-1D

| File | Làm gì | Trạng thái |
| --- | --- | --- |
| `tokenizer.py` | Biến chuỗi thành dãy số theo từng ký tự, cắt hoặc đệm về độ dài 200. Số `0` là đệm, `1` là ký tự lạ. Đây là bước chuẩn bị đầu vào cho CNN. | Chạy được |
| `model_cnn1d.py` | Định nghĩa mạng CNN-1D (class `CharCNN1D`, kernel 3/4/5). | Khung (có kiến trúc mạng, chưa train) |
| `train.py` | Sườn huấn luyện. | Khung |
| `explainability/run_shap.py` | Sườn giải thích model bằng SHAP (Tuần 5). | Khung |
| `checkpoints/`, `results/` | Nơi lưu model và kết quả. | Trống |

---

## Các thư mục còn lại

| File | Làm gì | Trạng thái |
| --- | --- | --- |
| `lab_verification/scripts/gen_traffic.py` | Sinh traffic thật (bình thường và có payload) tới DVWA trong lab cách ly để chạy Exp.6 (Tuần 5). | Khung |
| `lab_verification/scripts/run_evasion.py` | Gửi payload né tránh vào DVWA để xem lệnh có thực sự được thực thi không (Tuần 5). | Khung |
| `lab_verification/results/` | Kết quả đo trong lab, tách riêng khỏi benchmark tĩnh. | Trống |
| `dashboard/app.py` | Giao diện demo: nhập payload, hiện 3 kết quả song song (Tuần 6). | Khung |
| `scripts/check_env.py` | Kiểm tra Python, Semgrep, Docker, thư viện ML, PyTorch; ghi `[OK]`/`[THIEU]` vào file bằng chứng. | Chạy được |
| `notebooks/` | Dành cho Jupyter notebook: EDA, biểu đồ, phân tích False Positive. | Trống |
| `report/de_cuong_2_3_trang.md` | Khung đề cương 2–3 trang theo plan. | Khung |
| `report/bao_cao_9_chuong_(...).md` | File giữ chỗ cho báo cáo chính. | Trống |
| `report/slide/` | Nơi để slide. | Trống |
| `reports/` | Nơi `check_env.py` ghi `env_check.txt`. | Trống cho tới khi chạy |

> **Dễ nhầm:** `report/` (số ít) chứa tài liệu viết, còn `reports/` (số nhiều) chỉ chứa
> bằng chứng kiểm tra môi trường. Có thể gộp làm một nếu muốn.

---

## Những gì cần hiểu trong Tuần 1

1. **`php-cmdi-taint.yml`, 12 testcase và `run_scan.py`.** Làm thử nghiệm ở Bước 5 của
   [SETUP_TUAN1.md](SETUP_TUAN1.md): xóa khối `pattern-sanitizers` và dòng
   `pattern-not: proc_open([...], ...)`, chạy lại sẽ thấy T08 và T12 bị báo nhầm (FP).
2. **Ý nghĩa của 4 file CSV** trong `data/processed/` và vai trò của `group_id`.
3. **`check_env.py` và `docker-compose.yml`**, để hiểu vì sao lab phải cách ly.
