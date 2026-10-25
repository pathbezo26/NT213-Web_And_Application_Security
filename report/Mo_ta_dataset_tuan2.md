# Tuần 2 — Mô tả bộ dữ liệu (phần chèn vào báo cáo)

## Bộ dữ liệu và đơn vị mẫu

Thực nghiệm phân loại payload ở mức **giá trị của một tham số**. Mỗi dòng được gán nhãn `1` nếu thuộc nhóm payload OS Command Injection và `0` nếu là đầu vào được xem là lành tính. Mô hình ML cổ điển và CNN-1D sử dụng cùng bộ dữ liệu để tránh sai khác do nguồn đầu vào. Việc gán nhãn chuỗi không đồng nghĩa xác nhận chuỗi sẽ thực thi thành công trên ứng dụng thực tế.

Tập dữ liệu hiện lưu tại `data/processed/dataset_all.csv`. Theo kiểm tra trực tiếp, bộ dữ liệu có **18.142** dòng (8.749 nhãn 1 và 9.393 nhãn 0). Phân bố theo nhóm `category`:

| Nhóm | Số lượng | Vai trò |
|---|---:|---|
| `cmdi` | 8.749 | Payload có dấu hiệu command injection |
| `benign_csic` | 6.000 | Các mẫu normal được trích/lọc từ CSIC 2010 theo mô tả của nhóm |
| `benign_normal` | 2.715 | Chuỗi lành tính thông thường |
| `benign_special_char` | 678 | Chuỗi lành tính chứa ký tự đặc biệt, phục vụ kiểm tra FPR |
| **Tổng** | **18.142** | |

Dữ liệu hợp nhất có trường `payload_id`, `payload`, `label`, `category`, `source`, `context`, `technique`, `family`, `group_id`, `split`. Khi xuất sang `data/splits/{train,val,test}.csv`, nhóm dùng schema thống nhất gồm `payload_id,input_text,label,source,category,group_id,notes`; trong đó `input_text` là giá trị mang đi huấn luyện và `notes` lưu thông tin bổ sung về xuất xứ. Không nên nhầm schema của file hợp nhất với schema file huấn luyện.

## Chia dữ liệu và chống rò rỉ

Nhóm áp dụng bước loại trùng chính xác, gom payload gần giống thành `group_id`, rồi phân phối các group vào ba tập nhằm giảm nguy cơ train/test chứa biến thể quá giống nhau. Phân chia hiện tại như sau:

| Tập | Benign | Malicious | Tổng |
|---|---:|---:|---:|
| Train | 6.876 | 5.837 | 12.713 |
| Validation | 1.159 | 1.551 | 2.710 |
| Test | 1.358 | 1.361 | 2.719 |

Lệnh để kiểm tra và xuất lại các tập (chạy tại root repo):

```bash
python data/processed/train_test_split/split_and_check.py
```

Báo cáo đã lưu tại `reports/week2_dataset_validation.txt` ghi 0 trường hợp trùng payload giữa các tập, 0 trường hợp rò rỉ group và không có xung đột nhãn. Kết quả này là kiểm tra **tính nhất quán kỹ thuật của dữ liệu hiện có**, không phải bằng chứng xác minh tính đúng đắn của từng nhãn.

## Lý do cần tập benign khó

Chỉ số FPR cho biết tỷ lệ đầu vào lành tính bị dự đoán thành tấn công. Mô hình học theo ký tự dễ nhầm chuỗi chứa `;`, `|`, dấu nháy, biểu thức đường dẫn hoặc dấu `$` với command injection dù các ký tự này xuất hiện hợp lệ trong tên file, log hoặc văn bản. Theo `data/README.md`, nhóm mô tả 678 mẫu `benign_special_char` là các chuỗi được viết tay độc lập, không dựa trên việc xóa ký tự từ payload độc hại. Tuy nhiên, việc này chưa được một người thứ hai rà soát độc lập đầy đủ nên vẫn cần kiểm tra ở bước khóa dataset. Khi báo cáo FPR cần ghi rõ mẫu số là những mẫu thật sự nhãn 0 trong tập đánh giá đang dùng; nếu dùng riêng 678 mẫu thì cũng phải mô tả chúng thuộc train/val/test nào để không đánh giá lại trên dữ liệu đã train.

## Hạn chế và việc cần hoàn thành trước khi khóa dataset

Theo `data/README.md`: (1) nhóm còn cần kiểm tra chéo chất lượng 678 mẫu benign khó; (2) diễn giải nhãn `normal` của CSIC cần đối chiếu tài liệu nguồn; (3) quy trình tái tạo đầy đủ từ dữ liệu thô còn thiếu; (4) tỷ lệ nhãn giữa các split chưa cân bằng hoàn toàn do phải giữ nguyên các nhóm gần trùng lớn; (5) phạm vi payload Linux/bash không đại diện cho Windows PowerShell hoặc mọi ngữ cảnh ứng dụng.

Vì thế chưa coi dataset đã được nghiệm thu cuối cùng. Sau khi thành viên Dữ liệu & Lab hoàn thành rà soát và chốt phiên bản, nhóm cần lưu seed, phiên bản file và bản ghi kiểm định để việc đánh giá ML/DL có thể tái lập.


