# Tuần 5 — Phân tích khả năng giải thích của CNN-1D bằng SHAP và LIME

## Mục tiêu

Thí nghiệm trả lời RQ4: mô hình CNN-1D nhận biết cấu trúc liên quan đến OS Command
Injection hay chủ yếu ghi nhớ ký tự, từ khóa và đặc trưng riêng của nguồn dữ liệu.
Kết quả giải thích không được xem là bằng chứng quan hệ nhân quả; các nhận định phải
được đối chiếu bằng thí nghiệm che đặc trưng (ablation).

## Phương pháp

Payload được tách thành toán tử shell, từ/lệnh, khoảng trắng và dấu câu. SHAP và
LIME sử dụng cùng biểu diễn mặt nạ: segment bị che được thay bằng khoảng trắng cùng
độ dài để không làm dính hai token. Điểm dương làm tăng xác suất Command Injection;
điểm âm làm giảm xác suất này. Với mỗi segment, mô hình còn được chạy lại sau khi
che riêng segment đó để đo thay đổi xác suất trực tiếp.

Bốn nhóm cần phân tích gồm true positive, true negative khó, false negative và mẫu
thuộc nguồn holdout. Mỗi nhóm dùng cùng số mẫu và seed cố định. SHAP dùng Kernel
Explainer; LIME dùng perturbation có trọng số và hồi quy Ridge cục bộ.

## Cách tái lập

```bash
python deep_learning/explainability/run_shap.py \
  --checkpoint deep_learning/best_cnn1d.pt \
  --input data/processed/dataset_all.csv \
  --split val --method both --per-group 10 --seed 42
```

Kết quả được ghi tại `deep_learning/results/explainability/`, gồm
`attributions.csv`, `summary.json` và heatmap của từng payload.

## Tiêu chí phân tích

1. Kiểm tra các toán tử `;`, `&&`, `|`, `$()` và backtick có attribution cao hay không.
2. So sánh điểm SHAP, LIME và độ giảm xác suất khi che cùng một segment.
3. Kiểm tra mô hình có phụ thuộc quá mức vào tên lệnh hoặc đường dẫn cụ thể không.
4. So sánh mẫu test thông thường với false negative và nguồn holdout.
5. Chỉ kết luận sau khi số liệu thật được sinh từ checkpoint chính thức.

## Kết quả

Mô hình được train lại trên 10.831 mẫu train và đánh giá trên 2.239 mẫu validation.
Tại epoch tốt nhất, mô hình đạt accuracy 0,9964, precision 1,0000, recall 0,9902 và
F1 0,9951. Ma trận nhầm lẫn trên validation gồm 1.426 true negative, 805 true
positive, 8 false negative và không có false positive.

SHAP/LIME được chạy trên 28 mẫu: 10 true positive, 10 true negative có xác suất độc
hại cao nhất và toàn bộ 8 false negative. Hệ số tương quan thứ hạng Spearman trung
bình giữa SHAP và LIME theo từng payload đạt 0,7816, cho thấy hai phương pháp nhìn
chung đồng thuận nhưng không hoàn toàn tương đương.

Các toán tử shell thường có đóng góp dương. Trong nhóm false negative, dấu `;`, `|`
và `&` có SHAP dương từ khoảng 0,267 đến 0,387. Tuy nhiên, một số phần còn lại tạo
đóng góp âm lớn: `whoami` có SHAP từ -0,616 đến -0,709; các số cổng `4444`–`4448`
có SHAP từ -0,325 đến -0,471. Hiện tượng này giải thích vì sao các payload ngắn như
`; whoami` và các lệnh reverse shell `nc -lvvp ... -e /bin/sh` bị bỏ sót dù chứa
toán tử shell rõ ràng.

Ở nhóm benign khó, toán tử `&&` có SHAP dương từ 0,404 đến 0,529 trong các chuỗi
`apt-get update && apt-get install ...`. Phần từ khóa và ngữ cảnh lành tính tạo đóng
góp âm đủ lớn để dự đoán cuối cùng vẫn đúng, với xác suất độc hại từ 0,082 đến
0,353. Kết quả cho thấy CNN không chỉ dựa vào sự xuất hiện của toán tử shell mà còn
phụ thuộc mạnh vào các cụm từ xung quanh.

Một hạn chế đáng chú ý là nhiều true positive từ Commix bão hòa ở xác suất 1,0.
Khi đó, che riêng một segment thường làm xác suất thay đổi rất ít, khiến attribution
cục bộ khó phân biệt mức quan trọng giữa các thành phần. Ngoài ra, checkpoint này
được train trên toàn bộ nguồn của tập train; kết quả trên nguồn holdout phải được
thực hiện bằng một checkpoint riêng đã loại nguồn đó trước khi train.
