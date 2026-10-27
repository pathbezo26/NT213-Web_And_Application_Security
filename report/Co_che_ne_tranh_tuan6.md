# Tuần 6 — Giải thích cơ chế các kỹ thuật né tránh Command Injection

## 1. Vì sao cần kiểm tra né tránh

Mô hình dự đoán từ chuỗi payload học trên bộ dữ liệu hữu hạn. Cùng một ý định thực thi lệnh có thể được biểu diễn thành nhiều chuỗi ký tự khác nhau, trong khi model có thể chú ý tới từ khóa và dấu phân tách từng gặp trong train. Do vậy, việc đạt F1 cao trên test set chuẩn chưa đủ chứng minh độ bền vững. Bài toán của nhóm là đo xem tỷ lệ nhận diện có giảm khi payload đổi **cách viết** nhưng mục đích không đổi.

## 2. Cơ chế từng nhóm

### 2.1. Biến đổi biểu diễn / encoding

Một số tầng xử lý request có thể giải mã URL encoding trước khi chuyển dữ liệu cho ứng dụng, trong khi mô hình lấy input ở thời điểm khác. Nếu mô hình đọc chuỗi chưa giải mã nhưng chương trình phía sau nhận chuỗi đã giải mã, hai thành phần thực tế nhìn thấy dữ liệu khác nhau. Vì vậy phải lưu cả biểu diễn request ban đầu và chuỗi đầu vào chính xác đưa cho model; không được xem mọi dạng encoding là tương đương nếu backend không giải mã chúng.

### 2.2. Thay thế khoảng trắng, dấu phân tách bằng cách diễn đạt khác

Trong shell Linux/bash, khoảng trắng thường phân tách đối số, còn shell cũng có cơ chế mở rộng biến và các ký tự đặc biệt. Việc biểu diễn khoảng trắng hoặc chuỗi lệnh theo cách khác có thể làm đổi n-gram và chuỗi ký tự mà classifier nhìn thấy. Với `${IFS}`, kết quả còn tùy shell, cách trích dẫn và thời điểm mở rộng; phải xác minh trong môi trường lab, không mặc định thay thế nào cũng chạy.

### 2.3. Ghép biến, nối chuỗi, thay hình thức từ khóa

Một chương trình hoặc shell có thể ghép các phần từ biến hoặc biểu thức để tạo thành chuỗi cuối cùng. Một từ khóa không xuất hiện liền mạch trong payload thô nhưng có thể xuất hiện sau một bước diễn giải. Nhận diện từ khóa thô thường dễ bỏ sót kiểu biến thể này. Ngược lại, việc nhìn thấy một chuỗi có ký hiệu biến cũng không chứng minh nó nguy hiểm nếu ứng dụng chỉ lưu nó thành dữ liệu.

### 2.4. Comment / dấu nháy / thay đổi cấu trúc cú pháp

Dấu nháy, comment và cách tách token có thể ảnh hưởng cách shell nhận lệnh. Hiệu quả phụ thuộc vị trí chúng xuất hiện, câu lệnh chứa chúng và loại shell. Các cách biến đổi này nên được kiểm tra riêng từng nhóm, tránh gộp nhiều kỹ thuật trong một payload rồi không xác định được nguyên nhân vượt qua bộ lọc.

### 2.5. Unicode lookalike và chuẩn hóa

Ký tự nhìn giống nhau trên màn hình không nhất thiết là cùng mã Unicode hay cùng ngữ nghĩa đối với shell. Kỹ thuật này chủ yếu kiểm tra tính nhất quán khâu chuẩn hóa văn bản; nếu chương trình phía sau không chuyển chúng về cú pháp hợp lệ thì payload có thể **không thực thi**. Vì vậy cần báo rõ bước chuẩn hóa và xác minh thực thi, không mặc định homoglyph là một bypass có hiệu lực.

## 3. Thiết kế đánh giá

Mỗi mẫu cần lưu `payload_id`, `technique`, nhãn dự kiến, dự đoán của từng mô hình, trạng thái **thực thi lệnh đã xác minh**, cùng đường dẫn evidence/log. Để đánh giá bypass rate, chỉ tính mẫu đã được chứng minh có tác động thực thi trong lab làm mẫu số; với mẫu không chạy được, có thể báo tỷ lệ thất bại khi tạo payload nhưng không cộng vào bypass rate.

Phải tách đầu vào: **Semgrep** quét mã nguồn theo source–sink, không nhận trực tiếp payload. Chỉ nên nói ba hướng đánh giá trên cùng **kịch bản an ninh** khi thiết kế tương ứng, chứ không khẳng định Semgrep đã nhận một payload đầu vào như SVM/CNN.

## 4. Phạm vi an toàn và hạn chế

Mọi thử nghiệm chỉ chạy trong container/VM do nhóm dựng, mạng cách ly, không gửi request tới hệ thống bên ngoài. Phần mô tả này dựa vào cơ chế thường gặp và kế hoạch v5 của nhóm; để kết luận hiệu quả với từng kỹ thuật cần kết quả DVWA/bWAPP, log và phiên bản môi trường thực tế. Phạm vi bước đầu là Linux/bash; Windows cmd/PowerShell và context-aware code analysis chưa được thực hiện.
