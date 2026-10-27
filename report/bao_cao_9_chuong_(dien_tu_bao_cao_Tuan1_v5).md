# Báo Cáo Đồ Án T05: Phát hiện OS Command Injection

## Chương X: Kết quả Thực Nghiệm (Template Tuần 3)

Dưới đây là các bảng tổng hợp kết quả chạy thực nghiệm cho 3 hướng tiếp cận, chuẩn bị cho việc điền số liệu ở Tuần 4-5.

### 1. Bảng So Sánh Hiệu Năng Tổng Thể (Exp.1 & Exp.2)
Đánh giá trên tập test chuẩn (`data/splits/test.csv`).

| Hướng Tiếp Cận | Kỹ thuật / Model | Accuracy | Precision | Recall | F1-Score | Ghi chú |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Rule-based** | Semgrep (Taint-mode) | *[Chờ T4]* | *[Chờ T4]* | *[Chờ T4]* | *[Chờ T4]* | Quét tĩnh trên mã nguồn PHP |
| **ML Cổ điển** | SVM (TF-IDF char) | *[Chờ T4]* | *[Chờ T4]* | *[Chờ T4]* | *[Chờ T4]* | Đánh giá ở mức payload |
| **ML Cổ điển** | Random Forest | *[Chờ T4]* | *[Chờ T4]* | *[Chờ T4]* | *[Chờ T4]* | Đánh giá ở mức payload |
| **Học Sâu (DL)**| CNN-1D (Char-level) | *[Chờ T4]* | *[Chờ T4]* | *[Chờ T4]* | *[Chờ T4]* | Đánh giá ở mức payload |

### 2. Bảng Tỷ lệ Cảnh Báo Nhầm (FPR) trên Tập Lành Tính Khó (Exp.3)
Đánh giá khả năng phân biệt dữ liệu bình thường chứa ký tự đặc biệt (`;`, `|`, `$`).

| Kỹ thuật / Model | Số mẫu False Positive | Tỷ lệ FPR (%) | Ví dụ False Positive điển hình |
| :--- | :--- | :--- | :--- |
| Semgrep | *[Chờ T4]* | *[Chờ T4]* | *[Chờ phân tích T4]* |
| SVM | *[Chờ T4]* | *[Chờ T4]* | *[Chờ phân tích T4]* |
| CNN-1D | *[Chờ T4]* | *[Chờ T4]* | *[Chờ phân tích T4]* |

### 3. Bảng Kháng Cự Kỹ Thuật Né Tránh / Bypass Rate (Exp.4)
Tỷ lệ vượt mặt model của các nhóm kỹ thuật tấn công nâng cao.

| Kỹ thuật Né Tránh | Semgrep (Bypass %) | SVM (Bypass %) | CNN-1D (Bypass %) |
| :--- | :--- | :--- | :--- |
| URL/Hex Encoding | *[Chờ T5]* | *[Chờ T5]* | *[Chờ T5]* |
| Command Substitution (`$()`, `` ` ``) | *[Chờ T5]* | *[Chờ T5]* | *[Chờ T5]* |
| Ký tự phân cách thay thế (`${IFS}`) | *[Chờ T5]* | *[Chờ T5]* | *[Chờ T5]* |
| Chèn biến môi trường rỗng | *[Chờ T5]* | *[Chờ T5]* | *[Chờ T5]* |

### 4. Bảng Đánh Giá Khả Năng Phân Biệt Ngữ Pháp (Exp.5)
Kiểm tra xem mô hình có nhận diện nhầm các cuộc tấn công Web khác (SQLi, XSS) thành OS Command Injection hay không (Giải quyết RQ1). Đánh giá trên tập `data/sqli_xss_testset/sqli_xss.csv`.

| Mô hình | Số mẫu SQLi test | Số mẫu XSS test | Nhận diện nhầm thành CI (FPR) | Ghi chú |
| :--- | :--- | :--- | :--- | :--- |
| Semgrep | *[Chờ T4]* | *[Chờ T4]* | *[Chờ T4]* | Bắt theo source/sink PHP |
| SVM | *[Chờ T4]* | *[Chờ T4]* | *[Chờ T4]* | Dễ nhầm do dùng chung ký tự đặc biệt |
| CNN-1D | *[Chờ T4]* | *[Chờ T4]* | *[Chờ T4]* | Đánh giá khả năng học ngữ cảnh ngữ pháp |

### 5. Bảng Kiểm Chứng Trên Traffic Lab Thực Tế (Exp.6)
So sánh hiệu năng của mô hình khi chạy với traffic HTTP thật sinh ra từ `lab_verification/scripts/gen_traffic.py` bắn vào DVWA (Giải quyết RQ0).

| Mô hình | Accuracy (Lab) | Precision (Lab) | Recall (Lab) | F1-Score (Lab) | Nhận xét độ suy giảm so với Benchmark |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Semgrep | *[Chờ T5]* | *[Chờ T5]* | *[Chờ T5]* | *[Chờ T5]* | *[Chờ T5]* |
| SVM | *[Chờ T5]* | *[Chờ T5]* | *[Chờ T5]* | *[Chờ T5]* | *[Chờ T5]* |
| CNN-1D | *[Chờ T5]* | *[Chờ T5]* | *[Chờ T5]* | *[Chờ T5]* | *[Chờ T5]* |