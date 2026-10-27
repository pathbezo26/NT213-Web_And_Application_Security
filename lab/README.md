# Lab thử nghiệm: DVWA + bWAPP (Docker)

Lab cục bộ gồm hai ứng dụng web cố tình có lỗ hổng, dùng để thu thập và kiểm chứng payload **command injection** cho dự án T05. Toàn bộ lab dựng bằng một file `docker-compose.yml`, ai chạy cũng ra môi trường giống nhau.

> **Cảnh báo an toàn.** Đây là các ứng dụng có lỗ hổng thật. Chỉ chạy trên máy cá nhân, không đưa lên server công cộng, không mở cổng ra mạng ký túc xá/trường. File compose đã bind cổng vào `127.0.0.1`, đừng sửa thành `0.0.0.0` hoặc bỏ phần IP.

## 1. Yêu cầu

- Docker Engine và Docker Compose v2 (`docker compose version` chạy được)
- Cổng `4280` và `4281` trên máy còn trống
- Kết nối internet ở lần chạy đầu để tải image

## 2. Thành phần

| Dịch vụ | Image | URL | Ghi chú |
|---|---|---|---|
| DVWA | `ghcr.io/digininja/dvwa` | http://127.0.0.1:4280 | Cần database riêng |
| MariaDB (cho DVWA) | `mariadb:10` | không mở ra ngoài | Chỉ DVWA truy cập được qua mạng `labnet` |
| bWAPP | `raesene/bwapp` | http://127.0.0.1:4281 | Đã gói sẵn web server + database |

## 3. Cấu trúc thư mục

```
lab/
├── docker-compose.yml
└── README.md
└── env.example
```

## 4. Khởi chạy

```bash
cd lab
docker compose up -d
docker compose ps        # cả 3 dịch vụ phải ở trạng thái running
```

## 5. Khởi tạo lần đầu

### DVWA
1. Mở http://127.0.0.1:4280/setup.php
2. Bấm **Create / Reset Database**
3. Đăng nhập: `admin` / `password`
4. Vào **DVWA Security**, đặt mức **Low**, bấm Submit

### bWAPP
1. Mở http://127.0.0.1:4281/install.php
2. Bấm liên kết **here** để cài database
3. Đăng nhập: `bee` / `bug`
4. Chọn bug **OS Command Injection** trong danh sách, bấm **Hack**

## 6. Kiểm tra lab hoạt động

- **DVWA** → *Command Injection*: nhập `127.0.0.1`, phải thấy kết quả `ping`.
- **bWAPP** → *OS Command Injection*: nhập `127.0.0.1`, phải thấy kết quả tương tự.

Nếu ping chạy bình thường, lab đã sẵn sàng.

## 7. Dừng và tái lập

```bash
docker compose stop                          # tạm dừng, giữ dữ liệu
docker compose down                          # xóa container, giữ dữ liệu database
docker compose down -v && docker compose up -d   # reset sạch hoàn toàn
```

Sau lệnh reset sạch, phải lặp lại **mục 5** (bấm *Create / Reset Database* cho DVWA, cài lại bWAPP).
