# Tuần 1 — Khảo sát nguồn dữ liệu cho bài toán Command Injection

## 1. Mục đích

Ta cần dữ liệu để đánh giá bộ phân loại payload có dấu hiệu OS Command Injection. Dữ liệu phải bao gồm cả chuỗi tấn công lẫn chuỗi lành tính; nếu toàn bộ benign chỉ gồm chữ và số đơn giản, mô hình dễ học mẹo dựa vào dấu `;`, `|`, `$` thay vì nhận diện chuỗi có ý nghĩa tấn công. Do đó cần thêm dữ liệu lành tính có ký tự đặc biệt hợp lệ.

Đơn vị phân loại của ML/DL là **giá trị một tham số đầu vào**, không phải phân tích luồng thực thi trong chương trình. Semgrep nhận **mã nguồn PHP** chứ không nhận các payload CSV; kết quả hai hướng không thể so sánh trực tiếp bằng một tập test có cùng định dạng.

## 2. Các nguồn được xem xét

| Nguồn | Loại thông tin dự kiến khai thác | Cách dùng phù hợp | Điểm cần lưu ý |
|---|---|---|---|
| Commix | Các dạng chuỗi/payload phục vụ kiểm thử OS command injection | Lọc và chuẩn hóa thành nhóm malicious, bảo lưu kỹ thuật và họ payload | Wordlist được viết phục vụ khai thác/thăm dò; nhiều biến thể gần giống. Một payload nhìn có vẻ độc **chưa đồng nghĩa** thực thi thành công trên mọi hệ thống |
| PayloadsAllTheThings | Mẫu cú pháp liên quan command injection trên các môi trường/kiểu tách lệnh khác nhau | Chọn các mẫu liên quan shell Linux/bash; lưu nguồn, kỹ thuật và nhãn | Không lấy nhầm SQLi/XSS hoặc các biến thể cho môi trường ngoài phạm vi. Cần tránh trùng với Commix |
| CSIC 2010 | Request HTTP bình thường và bất thường trong bài toán phát hiện bất thường web | Xem xét trích **giá trị tham số của request `normal`**, sau khi đối chiếu hướng dẫn gốc và lọc thủ công | **Không gán nhãn toàn bộ dataset CSIC là benign**; request `anomalous` không mặc nhiên là command injection. Nhãn CSIC không thiết kế riêng cho CWE-78 |
| Benign viết tay độc lập | Tên file, URL, đường dẫn, đoạn JSON/văn bản, câu lệnh quản trị hợp lệ chứa dấu đặc biệt | Làm tập benign khó, đo FPR | Phải tạo độc lập, không sinh bằng cách xóa ký tự từ payload tấn công |

## 3. Tiêu chí xử lý dữ liệu

1. Lưu lại nguồn gốc, nhãn, `category` và ghi chú về ngữ cảnh; trường hợp chưa xác định nhãn thì loại khỏi train/test và kiểm tra lại.
2. Chuẩn hóa cùng đơn vị `input_text` ở mức giá trị tham số cho ML/DL. Không trộn một request HTTP nguyên vẹn với một mảnh tham số mà không mô tả.
3. Loại trùng chính xác, sau đó gom chuỗi gần trùng theo `group_id` trước khi chia dữ liệu 70/15/15; một nhóm chỉ được nằm trong một split.
4. Tách train/validation/test. Dùng validation để chọn cấu hình; không tuning sau khi xem test.
5. Đo Precision, Recall, F1, FPR và sau này thêm bypass rate trên payload **được xác minh chạy thành công** trong lab.
6. Chỉ chạy kiểm chứng trên DVWA/bWAPP được nhóm dựng riêng trong Docker; không thử vào địa chỉ ngoài lab.

## 4. Đối chiếu với dữ liệu hiện có trong repo 

Trong `data/processed/dataset_all.csv` hiện có **18.142** mẫu: **9.393 benign / 8.749 malicious**. Nhóm đã chia train **12.713**, val **2.710**, test **2.719**. Có **678** mẫu thuộc `benign_special_char`, trong đó train 545, val 58, test 75. Số liệu này được đọc từ CSV, **không phải kết quả tự thu thập mới trong tuần 1**.

File `reports/week2_dataset_validation.txt` báo không rò rỉ payload đúng và không rò rỉ `group_id`. Tuy nhiên, theo `data/README.md`, 678 mẫu benign khó chưa được rà soát độc lập đầy đủ, cách hiểu nhãn CSIC còn cần kiểm chứng, và quy trình dựng lại dataset từ dữ liệu thô chưa có đủ bằng chứng. Vì vậy chỉ đánh giá rằng bộ dữ liệu **đã có cấu trúc và đã kiểm tra split**, chưa nên tuyên bố chất lượng nhãn được xác nhận toàn bộ.

## 5. Kết luận

Nguồn Commix và PayloadsAllTheThings phù hợp để chọn các chuỗi command injection; CSIC 2010 hỗ trợ khai thác benign nhưng phải hiểu đúng nhãn nguồn; bộ benign đặc biệt cần được bổ sung độc lập. Các bước tiếp theo phụ thuộc người xây dataset: rà nhãn, bảo lưu xuất xứ, hoàn thiện dữ liệu gốc và kiểm thử lại rò rỉ trước khi huấn luyện. Mục tiêu của khảo sát là xác định cách dùng nguồn cho đúng, không coi số lượng payload lớn là đủ để chứng minh hiệu năng thực tế.

