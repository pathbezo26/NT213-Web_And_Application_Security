# classical_ml/ — ML cổ điển

Mọi lệnh chạy bằng PowerShell tại **thư mục gốc repo**.

## Cài đặt

```powershell
.\.venv\Scripts\Activate.ps1
pip install scikit-learn pandas numpy joblib
```

## Chạy

**Train + tune cả SVM và RF** (chọn tham số theo F1 trên val):

```powershell
python classical_ml\train.py --input data\processed\dataset_all.csv --exp exp3_ml
```

**Kiểm tra chéo nguồn, hai chiều** (giống DL):

```powershell
python classical_ml\train.py --input data\processed\dataset_all.csv `
    --holdout-source "command_exec|command-execution-unix" --exp exp3_ml_holdout_patt

python classical_ml\train.py --input data\processed\dataset_all.csv `
    --holdout-source "commix" --exp exp3_ml_holdout_commix
```

**Phân tích kết quả holdout** (dùng chung script của DL):

```powershell
python deep_learning\analyze_holdout.py `
    --holdout classical_ml\results\exp3_ml_holdout_patt_svm_holdout.csv `
    --dataset data\processed\dataset_all.csv
```

Kiểm tra nhanh đặc trưng: `python classical_ml\features.py`

## Tham số chính của `train.py`

| Tham số | Mặc định | Ý nghĩa |
|---|---|---|
| `--input` | `data/processed/dataset_all.csv` | Dataset đã chia (có cột `split`) |
| `--models` | `svm,rf` | Model cần chạy |
| `--ngram-grid` | `1-3,2-4` | Khoảng char n-gram cần thử |
| `--svm-c-grid` | `0.1,1,10` | Giá trị `C` của SVM |
| `--rf-n-grid` | `200` | Số cây của RF |
| `--rf-depth-grid` | `None,30` | Độ sâu tối đa của RF (`None` = không giới hạn) |
| `--exp` | `exp3_ml` | Tên thí nghiệm: đặt tên file và ghi vào cột `exp` |
| `--holdout-source` | không có | Regex khớp cột `source`: loại nguồn đó khỏi train/val, đo riêng |
| `--seed` | `42` | Giữ nguyên để tái lập |

## Kết quả ra đâu

| File | Nội dung |
|---|---|
| `models\<exp>_svm.pkl`, `models\<exp>_rf.pkl` | Pipeline đã train (đặc trưng + model) và cấu hình tốt nhất. Nạp lại bằng `joblib.load`, cần `classical_ml\features.py` nằm trong `sys.path`. |
| `results\<exp>_svm.csv`, `results\<exp>_rf.csv` | Dự đoán trên val, schema chung, `confidence` = P(độc hại) |
| `results\<exp>_<model>_holdout.csv` | Dự đoán trên nguồn bị loại (khi dùng `--holdout-source`) |
| `results\<exp>_tune_log.csv` | F1/precision/recall trên val của mọi cấu hình đã thử |

## Nguyên tắc

- **Không chia lại dữ liệu** (không dùng `train_test_split`): đọc cột `split` do `scripts/split.py` tạo, để ML và DL đo trên cùng một tập.
- TF-IDF, scaler và model đều nằm trong `Pipeline`, nên chỉ học từ train. Chọn tham số theo val. **Không đụng tập test.**
- SVM tuyến tính không có xác suất, nên được bọc bằng `CalibratedClassifierCV` (sigmoid, 3 fold trên train) để có `confidence`.
- Khi các cấu hình hoà F1, giữ cấu hình xếp trước (đơn giản hơn).
- Lưu ý khi diễn giải: đặc trưng `has_separator` và `has_substitution` gần như trùng với quy tắc gán nhãn của dataset (malicious phải có dấu nối hoặc thay thế lệnh). Kết quả tốt, nhất là khi kiểm tra chéo nguồn, một phần đến từ chính quy tắc nhãn này.
