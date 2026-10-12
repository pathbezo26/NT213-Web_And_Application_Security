# Hướng dẫn setup & hoàn thành Tuần 1 — T05 (làm một mình trước)

Mục tiêu: cuối buổi có **môi trường chạy được + bằng chứng** (`reports/env_check.txt`,
`semgrep/results/exp1_semgrep_v0.csv`), dữ liệu thô đã tải, và báo cáo Tuần 1 điền xong các ô [ĐIỀN].
Thời gian ước tính: 2–3 giờ setup + thời gian đọc paper.

Viết cho **Windows + WSL2 (Ubuntu)**. Lý do: Semgrep, Docker và tool bảo mật chạy ổn nhất trên Linux,
và payload để trong WSL ít bị Windows Defender xóa nhầm. Dùng Ubuntu/macOS thật thì bỏ qua Bước 0.

---

## Bước 0 — Cài WSL2 Ubuntu (Windows)

PowerShell **Run as Administrator**:

```powershell
wsl --install -d Ubuntu-24.04
```

Khởi động lại máy, mở "Ubuntu" từ Start, tạo username/password. Từ đây mọi lệnh chạy **trong terminal Ubuntu**.

## Bước 1 — Công cụ nền

```bash
sudo apt update && sudo apt install -y python3-venv python3-pip git unzip curl
python3 --version     # cần >= 3.10
git config --global user.name  "Nguyen Tan Phat"
git config --global user.email "<email-cua-ban>"
```

Nếu dự án đã giải nén sẵn trên ổ Windows (ví dụ ổ D:), copy sang home của Ubuntu (`~`) và làm việc ở đó.
Lý do: `/mnt/c`, `/mnt/d` chậm hơn và bị Windows Defender quét/xóa file payload.

```bash
cp -r "/mnt/d/Documents/NT213_Bao_Mat_Web/Project/t05-command-injection-detection/t05-command-injection-detection" ~/
cd ~/t05-command-injection-detection
pwd      # phải ra /home/<user>/t05-command-injection-detection
code .   # mở VS Code (góc trái dưới hiện "WSL: Ubuntu-24.04")
```

Từ đây chỉ sửa bản trong `~`, bản trên ổ D: để làm bản gốc.

## Bước 2 — Lấy bộ khởi đầu dự án

Đã copy ở Bước 1 thì bỏ qua `cp`/`unzip`, chỉ chạy `git init ...` và phần GitHub.
Nếu chỉ có file `t05-command-injection-detection.zip` trong Downloads của Windows:

```bash
cd ~
cp /mnt/c/Users/<TEN_USER_WINDOWS>/Downloads/t05-command-injection-detection.zip .
unzip t05-command-injection-detection.zip && cd t05-command-injection-detection
git init && git add . && git commit -m "Tuan 1: khung du an, rule Semgrep v0, 12 testcase"
```

Tạo repo **private** trên GitHub (ví dụ `t05-command-injection-detection`), rồi:

```bash
git remote add origin https://github.com/<user>/t05-command-injection-detection.git
git branch -M main && git push -u origin main
```

> Mở bằng VS Code: `code .` (cài extension "WSL").

## Bước 3 — Python venv + thư viện ML/Semgrep

```bash
python3 -m venv .venv
source .venv/bin/activate          # mỗi lần mở terminal mới đều chạy lại dòng này
pip install --upgrade pip
pip install -r requirements.txt
```

## Bước 4 — PyTorch (framework DL đã chọn)

Chỉ dùng **một** framework DL → PyTorch. CNN-1D nhỏ chạy CPU là đủ:

```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip freeze > requirements.lock.txt   # khóa version để nhóm tái lập
```

Có card NVIDIA và muốn GPU: lấy lệnh ở https://pytorch.org/get-started/locally/.

## Bước 5 — Chạy rule Semgrep v0 (Exp.1 sơ bộ)

```bash
python semgrep/run_scan.py --version v0
```

Kết quả mong đợi:

```
TP=6 FP=0 FN=0 TN=6 | Precision=1.00 Recall=1.00
Da ghi: semgrep/results/exp1_semgrep_v0.csv
```

Nhãn chuẩn lấy theo **thư mục**: file trong `semgrep/testcases_php/vulnerable/` phải bị báo,
file trong `safe/` không được báo. Thêm testcase chỉ cần bỏ file `.php` vào đúng thư mục.

**Thử nghiệm nhỏ để hiểu rule** (ghi vào báo cáo): mở `semgrep/rules/php-cmdi-taint.yml`,
xóa khối `pattern-sanitizers` và dòng `pattern-not: proc_open([...], ...)`, chạy lại →
T08 và T12 biến thành FP. Hoàn tác: `git checkout semgrep/rules/`.

## Bước 6 — Docker + lab DVWA/bWAPP (cần cho Tuần 2, cài luôn)

1. Cài **Docker Desktop** cho Windows → Settings → Resources → WSL Integration → bật cho Ubuntu-24.04.
2. Trong Ubuntu:

```bash
docker run --rm hello-world      # thấy "Hello from Docker!" là xong
docker compose up -d             # bật DVWA + bWAPP (mạng internal, không lộ cổng)
docker compose ps                # kiểm tra 2 container đang chạy
docker compose down              # tắt khi không dùng
```

(Ubuntu thật: `sudo apt install docker.io docker-compose-v2`, `sudo usermod -aG docker $USER`, đăng nhập lại.)

## Bước 7 — Kiểm tra toàn bộ môi trường + lưu bằng chứng

```bash
python scripts/check_env.py      # tất cả dòng phải [OK] -> reports/env_check.txt
git add . && git commit -m "Tuan 1: env check + Exp.1 v0" && git push
```

## Bước 8 — Khảo sát nguồn dữ liệu (chỉ tải và ghi chép, CHƯA gán nhãn)

```bash
cd data/raw
git clone --depth 1 https://github.com/swisskyrepo/PayloadsAllTheThings.git payloadsallthethings/repo
git clone --depth 1 https://github.com/commixproject/commix.git commix_payloads/repo
cd ../..
python data/processed/train_test_split/split_and_check.py   # chạy thử trên dữ liệu ví dụ
```

Với mỗi nguồn, ghi vào `report/` hoặc một file `docs` ngắn: URL gốc, license, số mẫu ước lượng,
nhãn có sẵn, dùng vào đâu. Riêng:
- **CSIC 2010**: đọc tài liệu nhãn trước khi tải vào `data/raw/csic2010/`; chỉ lấy request *normal* làm benign.
- **ECML/PKDD 2007**: có nhãn "OS commanding" → nguồn CI thật.
- `data/raw/` đã nằm trong `.gitignore` → không đẩy payload lên GitHub.

## Bước 9 — Đọc 6 paper (phần tốn thời gian nhất)

Danh sách ở báo cáo mục 3. Mỗi paper ghi 5 dòng: bài toán & input; feature/kiến trúc; dataset
(nguồn, cỡ, cách lấy benign); kết quả + **có đo FPR không, trên tập nào**; lấy gì cho T05 / điểm yếu cần tránh.
Ưu tiên: Wang 2024, Durmuşkaya 2025, Saxe 2017.

## Bước 10 — Hoàn thiện báo cáo Tuần 1

Mở `T05_Bao_cao_ket_qua_Tuan_1_v5.docx` (file nhận ở chat), tìm các ô **[ĐIỀN]**:
- Mục 8: dán nội dung `reports/env_check.txt`.
- Mục 7: xác nhận Exp.1 trên máy bạn khớp TP=6/FP=0/FN=0/TN=6 (khác → ghi lại, đó là phát hiện).
- Mục 3: bổ sung nhận xét sau khi đọc full-text.

## Checklist hoàn thành Tuần 1

- [ ] `check_env.py` toàn `[OK]` → `reports/env_check.txt`
- [ ] `semgrep/run_scan.py --version v0` → TP=6 FP=0 FN=0 TN=6
- [ ] `docker compose up -d` chạy được DVWA + bWAPP
- [ ] Repo private trên GitHub, đã push
- [ ] `data/raw/` có PayloadsAllTheThings + Commix; đã ghi chép 4 nguồn
- [ ] Đã đọc ≥ 4 paper, ghi tóm tắt
- [ ] Báo cáo Tuần 1 v5 điền xong các ô [ĐIỀN]

## Lỗi thường gặp

| Triệu chứng | Cách xử lý |
| --- | --- |
| `semgrep: command not found` | Chưa `source .venv/bin/activate` |
| `docker: Cannot connect to the Docker daemon` | Mở Docker Desktop; bật WSL Integration |
| Windows Defender xóa file payload | Để dự án trong `~` của WSL, không ở `/mnt/c/...` |
| `pip install` báo `externally-managed-environment` | Đang ngoài venv → kích hoạt `.venv` |
| `docker compose` báo không có bWAPP image | Lần đầu cần mạng; tạm bỏ `internal: true`, pull xong bật lại |
