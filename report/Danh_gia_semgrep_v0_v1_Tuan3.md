# Tuần 3 — Hoàn thiện rule Semgrep và đánh giá Exp.1

## 1. Mục tiêu và phạm vi

Kiểm tra rule phân tích tĩnh Semgrep nhằm phát hiện trường hợp dữ liệu do người dùng kiểm soát đi tới các vị trí thực thi lệnh hệ điều hành trong mã nguồn PHP. Việc đánh giá tiến hành trên các file PHP được gán nhãn sẵn; **không chạy mã PHP chứa lỗ hổng** và không đo khả năng chặn HTTP request tại thời điểm chạy ứng dụng.

Nhóm đã có rule v0 và bộ 12 testcase (T01–T12), gồm 6 file `vulnerable/` và 6 file `safe/`. Để xem xét giới hạn bao phủ của v0, bổ sung hai testcase chủ động thiết kế: T13 (tên file upload lấy từ `$_FILES` đi đến `system()`) và T14 (giá trị `$_GET` đi đến toán tử backtick PHP). Hai trường hợp bổ sung được thiết kế nhằm kiểm tra đúng những dạng nguồn/sink v0 chưa khai báo, do đó kết quả không đại diện cho một benchmark độc lập hoặc khách quan trên mã nguồn thực tế.

## 2. Môi trường và các phiên bản rule

- Máy kiểm thử: Windows 10, môi trường Python `.venv`.
- Semgrep CLI: `1.182.1`.
- **v0 — rule gốc của nhóm:** `semgrep/rules/php-cmdi-taint.yml`.
- **v1 — rule thử nghiệm bổ sung:** `semgrep/truc_rules/php-cmdi-taint-v1.yml`.
- Bộ gốc: `semgrep/testcases_php/` (12 file PHP).
- Bộ bổ sung: `semgrep/extra_cases/` (T13, T14).
- Script đánh giá có sẵn của nhóm: `semgrep/run_scan.py`.

So với v0, v1 giữ nguyên cơ chế `mode: taint`, bổ sung nguồn `$_FILES` và sink là toán tử thực thi lệnh backtick của PHP. Không thay thế rule gốc để tiện tái lập và đối chiếu.

## 3. Cách chạy lại

Chạy các lệnh dưới đây **từ thư mục gốc repository**:

```bat
semgrep --version
semgrep --validate --config semgrep/rules/php-cmdi-taint.yml
semgrep --validate --config semgrep/truc_rules/php-cmdi-taint-v1.yml
python semgrep/run_scan.py --version v0
semgrep scan --config semgrep/rules/php-cmdi-taint.yml --metrics off semgrep/extra_cases
semgrep scan --config semgrep/truc_rules/php-cmdi-taint-v1.yml --metrics off semgrep/extra_cases
semgrep scan --config semgrep/truc_rules/php-cmdi-taint-v1.yml --metrics off semgrep/testcases_php
```

Lệnh `run_scan.py --version v0` sinh file `semgrep/results/exp1_semgrep_v0.csv` cho **12 testcase gốc**. Đối với các lần quét v1 và hai testcase bổ sung, kết quả dưới đây được tổng hợp từ **đầu ra CLI đã chạy**, không phải từ một file CSV v1 tự động sinh. Tham số `--version` của script nhóm chỉ dùng để đặt tên file kết quả; script này vẫn quét rule trong `semgrep/rules/`, nên không dùng nó để tự nhận đã đánh giá v1.

## 4. Kết quả thực nghiệm

Cả rule v0 và v1 đều được Semgrep kiểm tra cấu hình hợp lệ: **0 configuration error, 1 rule**.

### 4.1. Bộ kiểm thử gốc T01–T12

| Testcase | Nhãn chuẩn | v0 | v1 |
|---|---|---|---|
| T01 — Nối chuỗi trực tiếp | Vulnerable | TP | TP |
| T02 — `$_GET` qua biến trung gian | Vulnerable | TP | TP |
| T03 — Dữ liệu `$_POST` | Vulnerable | TP | TP |
| T04 — Hàm xử lý yếu | Vulnerable | TP | TP |
| T05 — Gán biến nhiều bước | Vulnerable | TP | TP |
| T06 — Tạo chuỗi bằng `sprintf` | Vulnerable | TP | TP |
| T07 — API thư viện an toàn | Safe | TN | TN |
| T08 — Mảng đối số | Safe | TN | TN |
| T09 — Allowlist | Safe | TN | TN |
| T10 — Lệnh hằng | Safe | TN | TN |
| T11 — Ký tự đặc biệt ở dạng dữ liệu | Safe | TN | TN |
| T12 — `escapeshellarg()` | Safe | TN | TN |

- **v0:** `TP=6, FP=0, FN=0, TN=6`. Script nhóm xuất 12 dòng chi tiết vào `semgrep/results/exp1_semgrep_v0.csv`.
- **v1:** Quét 12 file, Semgrep báo **6 findings** nằm đúng trong T01–T06; không báo trong T07–T12. Suy ra `TP=6, FP=0, FN=0, TN=6` trên bộ gốc.

### 4.2. Hai testcase bổ sung T13–T14

| Testcase | Nhãn chuẩn | v0 | v1 | Vị trí v1 phát hiện |
|---|---|---|---|---|
| `T13_vuln_file_upload_name.php` | Vulnerable | FN | TP | Dòng 5: `system('echo ' . $filename);` |
| `T14_vuln_backtick_execution.php` | Vulnerable | FN | TP | Dòng 5: ``$out = `echo $user`;`` |

- **v0:** quét 2 file, **0 findings**.
- **v1:** quét 2 file, **2 findings** ở đúng hai file đã gán nhãn vulnerable.

### 4.3. Tổng hợp trên cả 14 testcase

| Chỉ số | Rule v0 | Rule v1 |
|---|---:|---:|
| True Positive (TP) | 6 | 8 |
| False Positive (FP) | 0 | 0 |
| False Negative (FN) | 2 | 0 |
| True Negative (TN) | 6 | 6 |
| Accuracy | 85,71% | 100,00% |
| Precision | 100,00% | 100,00% |
| Recall | 75,00% | 100,00% |
| F1-score | 85,71% | 100,00% |
| False Positive Rate (FPR) | 0,00% | 0,00% |

Cách tính:

- `Precision = TP / (TP + FP)`;
- `Recall = TP / (TP + FN)`;
- `F1 = 2 × Precision × Recall / (Precision + Recall)`;
- `FPR = FP / (FP + TN)`;
- `Accuracy = (TP + TN) / (TP + FP + FN + TN)`.

Các giá trị trong bảng là phép tổng hợp từ các **lần quét riêng** (12 file gốc và 2 file bổ sung). Chúng không phải kết quả của một lệnh duy nhất quét cùng lúc 14 file.

## 5. Nhận xét và giới hạn

Rule v0 nhận đúng 12 testcase ban đầu nhưng bỏ sót hai đường đi từ đầu vào tới vị trí thực thi lệnh chưa được khai báo. Việc bổ sung `$_FILES` và backtick trong v1 giúp phát hiện T13–T14 mà không làm phát sinh cảnh báo sai trên sáu file an toàn đã kiểm tra. Điều này cho thấy **cải thiện về độ bao phủ trên bộ testcase đang dùng**, không khẳng định v1 phát hiện tốt mọi lỗ hổng Command Injection trong PHP.

Các giới hạn cần ghi nhận:

1. **Quy mô nhỏ và có chủ đích:** 14 testcase là bộ kiểm thử đơn vị nội bộ; T13–T14 được chọn để thử đúng hai điểm thiếu của v0. Vì vậy, không suy rộng Accuracy/F1 = 100% thành hiệu năng thực tế.
2. **Chưa bao phủ hết nguồn, sink, sanitizer và các biến thể luồng dữ liệu:** v1 chỉ thay đổi hai trường hợp nói trên; các trường hợp khác có thể vẫn bị bỏ sót hoặc báo nhầm.
3. **Semgrep phân tích mã nguồn**, trong khi ML/DL của nhóm phân loại chuỗi payload/request. Không so sánh trực tiếp tỷ lệ phần trăm trên 14 file PHP với tỷ lệ trên tập payload ML/DL như thể đây là cùng một phép đo.
4. **Không kiểm chứng khai thác thực tế:** Các file T13–T14 chỉ được quét tĩnh, không chạy PHP và không thực hiện kiểm thử trên ứng dụng thật.

## 6. File bàn giao

- `semgrep/truc_rules/php-cmdi-taint-v1.yml`: rule v1 để nhóm trưởng review; **chưa ghi đè** rule v0 của nhóm.
- `semgrep/extra_cases/T13_vuln_file_upload_name.php`: testcase bổ sung cho `$_FILES`.
- `semgrep/extra_cases/T14_vuln_backtick_execution.php`: testcase bổ sung cho backtick.
- `report/Danh_gia_semgrep_v0_v1_Tuan3.md`: báo cáo thực nghiệm và đối chiếu v0/v1.


