# Dataset: Phát hiện Command Injection bằng ML/DL (T05)

**Trạng thái Tuần 2: khoảng 90%.** Dataset đã được hợp nhất, gán nhóm, chia
train/validation/test và kiểm tra tính toàn vẹn. Dataset chưa được khóa chính thức
do còn các bước kiểm soát chất lượng và tái lập từ nguồn thô được ghi tại mục 6.

Dataset payload lành tính/độc hại, dùng chung cho mảng ML cổ điển và DL (payload-level detection). Tài liệu này là nội dung cho phần "Mô tả Dataset" của báo cáo Tuần 2, theo kế hoạch v5 (`T05_Plan_NT213.xlsx`).

Phạm vi: đồ án chỉ phân loại **chuỗi payload** có dấu hiệu command injection hay không, không tuyên bố model hiểu ngữ cảnh thực thi lệnh thật trên hệ thống.

---

## 1. Schema

`data/processed/dataset_all.csv` lưu dữ liệu hợp nhất cùng các trường nội bộ phục vụ
tiền xử lý. Ba file dùng trực tiếp cho ML/DL trong `data/splits/` tuân theo schema
của nền tảng:

| Cột | Ý nghĩa |
|---|---|
| `payload_id` | Mã ổn định, không đổi sau khi gán |
| `input_text` | Chuỗi gốc đưa vào ML/DL |
| `label` | `1` = command injection, `0` = lành tính |
| `source` | Một trong `commix`, `payloadsallthethings`, `handwritten`, `csic` |
| `category` | Nhóm dữ liệu hoặc kỹ thuật |
| `group_id` | Nhóm trùng/gần trùng — đơn vị dùng để chia tập, không rò rỉ |
| `notes` | Nguồn chi tiết, context, technique và family được bảo toàn từ dữ liệu hợp nhất |

Đơn vị payload: **giá trị của một tham số** (ví dụ giá trị ô ip trong DVWA), không phải cả HTTP request — áp dụng nhất quán cho mọi nguồn, kể cả CSIC.

---

## 2. Nguồn dữ liệu

### 2.1 Malicious (`label = 1`) — 8.749 dòng

Chỉ 2 nguồn theo đúng mục 4.3 kế hoạch v5 (payload tự sinh theo template và phần malicious trích từ CSIC đã bị loại khỏi tập chính, xem mục 6):

| Nguồn | Link | Kỹ thuật đại diện |
|---|---|---|
| SecLists — `command-injection-commix.txt` | [GitHub](https://github.com/danielmiessler/SecLists/blob/master/Fuzzing/command-injection-commix.txt) | Mô phỏng kỹ thuật "classic injection" của Commix (marker + biểu thức toán học để xác minh), license MIT (SecLists) |
| PayloadsAllTheThings — `Command Injection/Intruder/command-execution-unix.txt` | [GitHub](https://github.com/swisskyrepo/PayloadsAllTheThings/tree/master/Command%20Injection/Intruder) | Payload command injection Unix cổ điển, license MIT |
| PayloadsAllTheThings — `Command Injection/Intruder/command_exec.txt` | cùng repo | Payload command injection đa dạng separator | 

**Lưu ý đã xác minh:** repo chính thức `commixproject/commix` không có file wordlist tĩnh (payload được sinh runtime trong code Python của tool) — SecLists là nguồn tĩnh gần nhất mô phỏng kỹ thuật Commix, không phải lấy trực tiếp từ repo đó. Đã kiểm tra thư mục `data/txt/` của `commixproject/commix`: chỉ chứa wordlist phụ trợ (tên tham số, đường dẫn, user-agent...), không phải payload command injection, nên không dùng.

**SQLi/XSS lẫn trong wordlist:** tập hiện tại được tách và rà soát thủ công; chưa có
script lọc tự động được commit trong repo. Cần thận trọng với payload command
injection có chứa chuỗi hiển thị giống XSS, ví dụ `;echo '<script>alert(1)</script>'`,
vì không thể chỉ dựa vào từ khóa `<script>` để kết luận đây là XSS thuần. Đây là hạn
chế về khả năng tái lập của bước tiền xử lý nguồn.

### 2.2 Benign (`label = 0`) — 9.393 dòng, 3 nhóm theo mục 4.4

| Nhóm | Số dòng | Nội dung | Cách tạo |
|---|---|---|---|
| `benign_normal` | 2.715 | Giá trị tham số thông thường: IP, domain, từ khoá tìm kiếm, tên người dùng... | Sinh từ mẫu hợp lệ (Faker) + mẫu truy vấn tìm kiếm thật |
| `benign_special_char` | 678 | Chuỗi hợp lệ có ký tự đặc biệt (`;`, `|`, `$`, `` ` ``, dấu nháy...) trong ngữ cảnh KHÔNG nguy hiểm | Viết tay bởi nhóm, có cột `context` cho từng dòng |
| `benign_csic` | 6.000 | Giá trị tham số trích từ request `normal` của CSIC 2010 | Chọn lọc theo tiêu chí ở mục 2.3, downsample ngẫu nhiên seed=42 |

**Lưu ý benign_special_char:** không tạo bằng cách xoá/thay ký tự nguy hiểm khỏi payload độc hại — viết độc lập theo nhiều dạng: lệnh hợp lệ có đối số (`ping -c 4 8.8.8.8`), tên file/đường dẫn có dấu chấm phẩy, câu văn có dấu câu, URL có query string, văn bản chứa `$` hoặc dấu nháy ngược trong ngữ cảnh thường.

### 2.3 CSIC 2010 — quy trình chọn lọc cho `benign_csic`

Thực hiện qua `scripts/prep-csic-v5.py`, 4 tiêu chí loại tường minh (log đầy đủ ở `dataset/csic_criteria.md`):

1. Độ dài tham số > 200 ký tự hoặc rỗng → loại
2. Tham số khớp pattern SQLi/XSS rõ ràng (`union select`, `or 1=1`, `<script`...) dù nhãn `normal` → loại, nghi ngờ gán nhãn sai ở dataset gốc
3. Trùng lặp → giữ 1 bản
4. Downsample ngẫu nhiên (không hoàn lại, seed=42) xuống 6.000 dòng để không áp đảo số lượng so với malicious — **tách biệt với việc lọc chất lượng ở trên**, chỉ nhằm cân bằng số lượng

CSIC là bộ nghiên cứu bất thường traffic web, không phải bộ command injection — request bất thường không đồng nghĩa với command injection. Nhãn `normal` chỉ dùng cho `benign_csic`, không trích phần `anomalous` làm malicious (không có trong mục 4.3).

---

## 3. Quy trình loại trùng, gom nhóm và chia tập (mục 4.6)

Thứ tự bắt buộc: loại trùng đúng → gán `group_id` → chia tập. (Chia trước rồi loại trùng sẽ làm tập test lẫn mẫu giống tập train.)

1. **Loại trùng đúng**: gộp theo `payload.strip()`; chuỗi bị gán nhãn khác nhau giữa 2 nguồn được cảnh báo và ghi ra file riêng để giải quyết tay. Lần chạy gần nhất: **0 chuỗi xung đột nhãn**.
2. **Gom near-duplicate → `group_id`**: TF-IDF ký tự 3-gram + cosine similarity, ngưỡng > 0.9, tính theo khối (`block_size=2000`) để tránh ma trận O(n²) khi dataset > ~10k dòng; nhóm bằng connected components (`scipy.sparse.csgraph.connected_components`).
3. **Chia 70/15/15 theo `group_id`**: dùng thuật toán tự viết `stratified_group_split` (script `scripts/split.py`), KHÔNG dùng `GroupShuffleSplit` thuần — xem lý do ở mục 4.
4. **Kiểm tra rò rỉ**: assert mỗi `group_id` chỉ thuộc đúng 1 tập — đã pass.

Lệnh đã dùng để gán nhóm và chia dữ liệu (seed=42, ngưỡng cosine 0.9):

```bash
python scripts/split.py --input data/processed/dataset_all.csv \
    --output data/processed/dataset_all.csv --seed 42
```

Sau khi cột `split` đã được chốt, sinh và kiểm tra ba file sử dụng cho huấn luyện
bằng lệnh:

```bash
python data/processed/train_test_split/split_and_check.py
```

`dataset_all.csv` là nguồn chuẩn duy nhất. Không chỉnh sửa riêng
`data/splits/train.csv`, `val.csv` hoặc `test.csv`, và không dùng test để lựa chọn
mô hình hay siêu tham số.

---

## 4. Vì sao không dùng `GroupShuffleSplit` thuần

Kế hoạch v5 gợi ý `GroupShuffleSplit` 2 lần liên tiếp (70/15/15), nhưng cách này **chỉ cân bằng số dòng mỗi tập, bỏ qua tỷ lệ nhãn**. Kiểm thử thực tế với seed khác nhau cho thấy: dù % tổng số dòng luôn đúng 70/15/15, % malicious giữa 3 tập lệch rất mạnh (ví dụ train 47,2% / val 40,7% / test 57,5% malicious — lệch 16,8 điểm %), và lệch này **lặp lại có hệ thống dù đổi seed** → chứng minh đây là lỗi cấu trúc thuật toán, không phải may rủi seed.

**Nguyên nhân:** benign có vài cụm near-duplicate rất lớn (cụm lớn nhất 1.134 dòng, 6,3% toàn dataset — từ các câu tìm kiếm/tham số gần giống nhau), còn malicious có rất nhiều cụm nhỏ/đơn lẻ (marker ngẫu nhiên của Commix). `GroupShuffleSplit` xử lý các cụm này như đơn vị kích thước thuần, dễ dồn một cụm benign khổng lồ nguyên khối vào 1 tập, làm lệch tỷ lệ nhãn tập đó.

**Cách sửa:** viết `stratified_group_split` — xử lý cụm lớn nhất trước, mỗi cụm được gán vào tập đang "thiếu" nhiều nhất (tỷ lệ đã lấp đầy *trước khi thêm*, so với mục tiêu riêng của tập đó — tính trên cả tổng số dòng, số dòng nhãn 0 và nhãn 1). Một phiên bản đầu dùng độ lệch *sau khi thêm* bị phát hiện thiên vị ngược (ưu tiên nhầm val/test vì target nhỏ hơn "cải thiện" nhanh hơn một cách giả tạo) — đã sửa lại dùng tỷ lệ trước khi thêm, kiểm chứng trên dữ liệu giả mô phỏng đúng cấu trúc thật trước khi áp dụng.

### Kết quả cuối cùng (seed=42)

Tổng 18.142 dòng sau loại trùng đúng, 13.493 group (lớn nhất 1.134 dòng, 6,3%).

| Tập | Benign | Malicious | Tổng | % tổng | % malicious |
|---|---|---|---|---|---|
| train | 6.876 | 5.837 | 12.713 | 70,1% | 45,9% |
| val | 1.159 | 1.551 | 2.710 | 14,9% | 57,2% |
| test | 1.358 | 1.361 | 2.719 | 15,0% | 50,1% |
| **Tổng** | 9.393 | 8.749 | 18.142 | 100% | 48,2% |

So với `GroupShuffleSplit` thuần: độ lệch nhãn lớn nhất-nhỏ nhất giảm từ **16,8 điểm % xuống 11,3 điểm %**. Phần còn lệch (val lệch +9 điểm % so với trung bình) là **hạn chế cấu trúc của dữ liệu** — vài cụm benign gần-trùng chiếm tỷ trọng lớn (tới 6,3% dataset trong 1 cụm duy nhất) không thể cắt nhỏ để chia đều mà không rò rỉ (mục 4.6 yêu cầu mỗi cụm chỉ thuộc 1 tập). Xem mục 6.

---

## 5. Danh sách script (`scripts/`)

| Script | Việc |
|---|---|
| `split.py` | Loại trùng, gán `group_id`, chia 70/15/15 cân bằng nhãn (`stratified_group_split`) |
| `data/processed/train_test_split/split_and_check.py` | Entry point theo nền tảng để xuất và kiểm tra train/val/test |
| `export_splits.py` | Kiểm tra xung đột, payload trùng giữa tập, rò rỉ nhóm và xuất schema 7 cột |
| `validate_schema.py` | Kiểm tra schema 7 cột của các file train/val/test |

---

## 6. Hạn chế đã biết

1. **Lệch nhãn giữa 3 tập còn tồn dư** (~11 điểm %, xem mục 4) do vài cụm benign gần-trùng chiếm tỷ trọng lớn so với kích thước tập val/test.
2. **`benign_special_char` chưa qua rà soát chất lượng toàn diện** — 678 dòng viết tay, chưa có bước rà trùng/rà chất lượng độc lập bởi người thứ hai như mục 4.4 khuyến nghị.
3. **Tách SQLi/XSS khỏi malicious thực hiện bằng tay**, chưa có script tự động trong
   repo (xem mục 2.1); vì vậy bước này chưa có bằng chứng tái lập được bằng công cụ.
4. **CSIC 2010 dùng cho benign** dựa trên giả định nhãn `normal` ≈ lành tính; chưa đối chiếu lại với tài liệu gốc của bộ dữ liệu để xác nhận ý nghĩa nhãn.
5. Phạm vi chỉ payload-level, giới hạn shell Linux/bash — không đại diện cho mọi hệ điều hành hoặc ngữ cảnh thực thi.
6. **Quy trình tạo lại dataset từ nguồn thô chưa đầy đủ trong repo.** Dataset hiện
   tại và bước chia có thể kiểm tra được, nhưng chưa thể chạy một lệnh từ toàn bộ
   nguồn thô để tái tạo chính xác `dataset_all.csv`.
