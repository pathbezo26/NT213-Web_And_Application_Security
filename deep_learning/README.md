# Hướng dẫn chạy Depp-learning

Mọi lệnh chạy bằng PowerShell, mở tại thư mục gốc repo.

## 1. Chuẩn bị

**Môi trường**:

```powershell
python -m venv .venv-dl
.\.venv-dl\Scripts\Activate.ps1
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install numpy pandas scikit-learn
```

Mỗi lần mở terminal mới chỉ cần chạy lại dòng `Activate.ps1`. Đầu dòng lệnh hiện `(.venv-dl)` là đã vào đúng venv.

**Dữ liệu:** `dataset\processed\dataset_all.csv` trên repo đã qua toàn bộ các bước xử lý và đã chia train/val/test, dùng luôn được. File phải có các cột `payload_id`, `payload`, `label`, `category`, `source`, `split`.

## 2. Các file và việc của từng file

| File | Dùng để |
|---|---|
| `tokenizer.py` | Tách payload theo ký tự. Chạy riêng để xem ví dụ mã hoá. |
| `model_cnn1d.py` | Kiến trúc CNN-1D. Chạy riêng để kiểm tra model dựng được. |
| `train.py` | Train, tune, kiểm tra chéo nguồn, ghi kết quả |
| `diagnose_val.py` | So model với baseline regex, đếm category trong từng tập |

## 3. Kiểm tra tokenizer và model

```powershell
python deep_learning\tokenizer.py
python deep_learning\model_cnn1d.py
```

Kết quả đúng: `tokenizer.py` in ra kích thước vocab và một dãy số. `model_cnn1d.py` in `torch.Size([4, 2])`.

## 4. Train và tune

**Train một cấu hình** (cấu hình đã chọn: max_len 100, emb_dim 16):

```powershell
python deep_learning\train.py --input data\processed\dataset_all.csv `
    --max-len-grid 100 --emb-dim-grid 16 --epochs 20 --exp exp3_dl_final
```

**Tune nhiều cấu hình:** truyền danh sách giá trị cách nhau bằng dấu phẩy, script chạy lần lượt mọi tổ hợp (9 cấu hình mất khoảng 30–60 phút trên CPU):

```powershell
python deep_learning\train.py --input data\processed\dataset_all.csv `
    --max-len-grid 50,100,200 --emb-dim-grid 16,32,64 --epochs 20 --exp exp3_dl_tune
```

Script tự chọn cấu hình có F1 val cao nhất và lưu checkpoint của cấu hình đó. Nhóm không chọn theo cách này mà theo độ ổn định (xem báo cáo). Muốn lưu đúng cấu hình nhóm chọn thì chạy lại lệnh train một cấu hình ở trên.

**Kiểm tra chéo nguồn:** loại hẳn một nguồn khỏi train và val, rồi đo riêng trên nguồn đó:

```powershell
python deep_learning\train.py --input data\processed\dataset_all.csv `
    --max-len-grid 100 --emb-dim-grid 16 `
    --holdout-source "command_exec|command-execution-unix" `
    --exp exp3_dl_holdout_patt --checkpoint deep_learning\best_cnn1d_holdout.pt
```

Đổi `--holdout-source` thành `"commix"` để chạy chiều ngược lại (bỏ Commix). **Luôn đặt `--checkpoint` sang file khác** khi chạy holdout, nếu không sẽ ghi đè checkpoint chính.

**Chẩn đoán khi F1 cao bất thường:**

```powershell
python deep_learning\diagnose_val.py --input data\processed\dataset_all.csv
```

## 5. Tham số của `train.py`

| Tham số | Mặc định | Ý nghĩa |
|---|---|---|
| `--input` | (bắt buộc) | File dataset đã chia |
| `--max-len-grid` | `100` | Danh sách độ dài chuỗi, ví dụ `50,100,200` |
| `--emb-dim-grid` | `32` | Danh sách kích thước embedding, ví dụ `16,32,64` |
| `--epochs` | `20` | Số epoch mỗi cấu hình |
| `--batch-size` | `64` | |
| `--lr` | `0.001` | Learning rate của Adam |
| `--n-filters` | `64` | Số filter mỗi kernel |
| `--seed` | `42` | Giữ nguyên để kết quả tái lập được |
| `--exp` | `exp3_dl` | Tên thí nghiệm, dùng đặt tên file kết quả và ghi vào cột `exp` |
| `--output-dir` | `deep_learning\results` | Thư mục ghi kết quả |
| `--checkpoint` | `deep_learning\best_cnn1d.pt` | Nơi lưu model |
| `--holdout-source` | không có | Regex khớp cột `source`. Các dòng khớp bị loại khỏi train/val và chỉ dùng để đo. |

## 6. Kết quả ra đâu

| File | Nội dung |
|---|---|
| `deep_learning\best_cnn1d.pt` | Trọng số model, kèm vocab, max_len, emb_dim (cần khi nạp lại model) |
| `deep_learning\results\<exp>_cnn1d.csv` | Dự đoán trên val, schema chung `payload_id, model, prediction, confidence, true_label, exp` |
| `deep_learning\results\<exp>_cnn1d_holdout.csv` | Dự đoán trên nguồn bị loại (chỉ khi dùng `--holdout-source`) |

Màn hình in thêm: F1 val theo từng epoch, accuracy/precision/recall/F1 của model được lưu, tỷ lệ đúng theo từng category, và tối đa 30 dòng đoán sai. `train.py` không bao giờ đụng tới tập test.