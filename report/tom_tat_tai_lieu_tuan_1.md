# Tóm tắt tài liệu liên quan — Tuần 1

## 1. Mục tiêu khảo sát

Khảo sát tập trung vào các phương pháp phát hiện tấn công injection và OS Command
Injection theo ba hướng của đề tài: phân tích tĩnh dựa trên luồng dữ liệu, học máy
cổ điển trên chuỗi payload và học sâu ở mức ký tự. Các tài liệu được đối chiếu theo
năm tiêu chí: bài toán, đầu vào, đặc trưng hoặc kiến trúc, dữ liệu đánh giá và hạn
chế có ảnh hưởng trực tiếp đến thiết kế thực nghiệm.

## 2. Bảng tổng hợp

| STT | Tài liệu | Bài toán và đầu vào | Phương pháp/đặc trưng chính | Dữ liệu và đánh giá | Hạn chế và giá trị đối với đề tài |
|---:|---|---|---|---|---|
| 1 | Spoto và cộng sự (2019), *Static Identification of Injection Attacks in Java* | Phát hiện các luồng dữ liệu không tin cậy đi vào sink nguy hiểm trong chương trình Java; bao gồm command injection, SQL injection, XSS và các loại injection khác | Phân tích taint liên thủ tục dựa trên abstract interpretation; flow-sensitive, context-sensitive, object-sensitive và field-sensitive | Juliet Test Suite, OWASP Benchmark và các ứng dụng Java thực tế | Mạnh về truy vết source–sink nhưng phụ thuộc ngôn ngữ và mô hình chương trình. Tài liệu cung cấp cơ sở cho baseline Semgrep taint-mode: xác định source, sink, sanitizer và luồng truyền dữ liệu thay vì chỉ tìm từ khóa |
| 2 | Rong, Zhang và Lv (2018), *Malicious Web Request Detection Using Character-level CNN* | Phân loại tham số HTTP thành bình thường hoặc độc hại | Character embedding kết hợp CNN một chiều; bộ lọc học mẫu cục bộ trực tiếp từ chuỗi ký tự | So sánh với SVM và Random Forest; tác giả báo cáo CNN mức ký tự làm giảm false-positive rate | Phạm vi là injection web nói chung, không riêng OS Command Injection. Tài liệu hỗ trợ lựa chọn CNN-1D mức ký tự và yêu cầu đo FPR trên tập benign khó |
| 3 | Odumuyiwa và Chibueze (2021), *Automatic Detection of HTTP Injection Attacks using Convolutional Neural Network and Deep Neural Network* | Phát hiện nội dung injection trong tham số HTTP | Character embedding, CNN và DNN nhằm học biểu diễn của chuỗi đầu vào mà không phụ thuộc hoàn toàn vào signature thủ công | Thử nghiệm trên dữ liệu HTTP injection; đánh giá khả năng phân loại của các mô hình học sâu | Kết quả phụ thuộc mạnh vào chất lượng và độ đại diện của dataset. Tài liệu củng cố việc chuẩn hóa đơn vị mẫu ở mức giá trị tham số và xây pipeline ký tự nhất quán |
| 4 | Yu, Wang, Li và He (2021), *Towards Automated Detection of Higher-Order Command Injection Vulnerabilities in IoT Devices* | Phát hiện command injection bậc cao: dữ liệu độc được lưu ở một bước và đi tới command interpreter ở bước sau | ReLink kết hợp fuzzing với theo dõi luồng dữ liệu động để liên kết request ghi dữ liệu với request kích hoạt sink | Đánh giá trên thiết bị/phần mềm IoT có luồng khai thác nhiều bước | Khác với bài toán phân loại payload đơn lẻ, nhưng cho thấy phát hiện chuỗi độc không đồng nghĩa chứng minh lệnh được thực thi. Vì vậy đề tài cần tách kết quả phân loại khỏi bước xác minh end-to-end trong DVWA/bWAPP |
| 5 | Wang, Zhai và Yang (2024), *Detecting Command Injection Attacks in Web Applications Based on Novel Deep Learning Methods* | Phát hiện trực tiếp web command injection từ trường dữ liệu trong lưu lượng web | Mô hình CCBA gồm hai kênh CNN, BiLSTM và attention để kết hợp đặc trưng cục bộ với quan hệ tuần tự hai chiều | Tác giả báo cáo Accuracy 99,3% và Recall 98,2% trên dữ liệu thực tế, đồng thời thử nghiệm trên hai bộ dữ liệu công khai | Kiến trúc có độ phức tạp cao và kết quả khó so sánh nếu quy trình chia dữ liệu khác nhau. Tài liệu là mốc tham khảo cho CNN/BiLSTM nhưng đề tài ưu tiên CNN-1D nhỏ, khả năng tái lập và kiểm tra rò rỉ dữ liệu |
| 6 | Widodo và Imaniawan (2026), *Detection of SQL Injection, XSS, and Command Injection Attacks in Web Payloads Using SVM, Random Forest, and XGBoost* | Phân loại đa lớp các payload SQLi, XSS và Command Injection | So sánh LinearSVC, Random Forest, XGBoost, character CNN, BiLSTM và rule-based comparator; sử dụng mutation testing và SHAP | 49.998 mẫu phân tầng; có đánh giá lại sau khi loại 878 mẫu trùng chính xác | Tập trung vào nhiều loại injection và chưa kiểm chứng trên log HTTP thực tế. Quy trình loại trùng, kiểm thử mutation, SHAP và đo thời gian suy luận có thể áp dụng trực tiếp cho thiết kế đánh giá của đề tài |

## 3. Kết luận khảo sát

Các nghiên cứu cho thấy không có một phương pháp duy nhất bao phủ đầy đủ ba khía
cạnh: phát hiện luồng source–sink trong mã nguồn, phân loại payload chưa biết và xác
minh khả năng thực thi trong môi trường thật. Do đó, thiết kế thực nghiệm sử dụng ba
lớp bổ sung cho nhau:

1. Semgrep taint-mode làm baseline phân tích tĩnh trên mã nguồn PHP.
2. SVM/Random Forest với TF-IDF ký tự và đặc trưng thủ công làm baseline học máy có
   thể giải thích.
3. CNN-1D mức ký tự học đặc trưng trực tiếp từ payload.

Accuracy và F1 không đủ để kết luận mô hình an toàn. Việc đánh giá cần bổ sung FPR
trên dữ liệu lành tính khó, bypass rate trên các biến thể né tránh và kiểm chứng rằng
payload thực sự chạy được lệnh trong lab cách ly. Các payload gần trùng phải được gom
theo `group_id` trước khi chia train/validation/test để tránh làm kết quả cao giả do
rò rỉ dữ liệu.

## 4. Tài liệu tham khảo

[1] F. Spoto, E. Burato, M. D. Ernst, P. Ferrara, A. Lovato, D. Macedonio và
C. Spiridon, “Static Identification of Injection Attacks in Java,” *ACM Transactions
on Programming Languages and Systems*, vol. 41, no. 3, article 18, 2019.
https://doi.org/10.1145/3332371

[2] W. Rong, B. Zhang và X. Lv, “Malicious Web Request Detection Using
Character-level CNN,” *Machine Learning for Cyber Security*, LNCS 11806, 2019.
https://arxiv.org/abs/1811.08641

[3] V. Odumuyiwa và A. Chibueze, “Automatic Detection of HTTP Injection Attacks
using Convolutional Neural Network and Deep Neural Network,” *Journal of Cyber
Security and Mobility*, vol. 9, no. 4, pp. 489–514, 2021.
https://doi.org/10.13052/jcsm2245-1439.941

[4] L. Yu, H. Wang, L. Li và H. He, “Towards Automated Detection of Higher-Order Command
Injection Vulnerabilities in IoT Devices,” *International Journal of Digital Crime
and Forensics*, vol. 13, no. 6, 2021.
https://doi.org/10.4018/IJDCF.286755

[5] X. Wang, J. Zhai và H. Yang, “Detecting Command Injection Attacks in Web
Applications Based on Novel Deep Learning Methods,” *Scientific Reports*, vol. 14,
article 25487, 2024. https://doi.org/10.1038/s41598-024-74350-3

[6] A. E. Widodo và F. F. D. Imaniawan, “Detection of SQL Injection, XSS, and
Command Injection Attacks in Web Payloads Using SVM, Random Forest, and XGBoost,”
*Journal of Information Systems and Informatics*, vol. 8, no. 3, pp. 3516–3538,
2026. https://doi.org/10.63158/journalisi.v8i3.1655
