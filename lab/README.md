# Lab thử nghiệm: DVWA + bWAPP (Docker)

Lab cục bộ gồm hai ứng dụng web cố tình có lỗ hổng, dùng để thu thập và kiểm chứng payload **command injection** cho dự án T05. Toàn bộ lab dựng bằng một file `docker-compose.yml`, ai chạy cũng ra môi trường giống nhau.

> **Cảnh báo an toàn.** Đây là các ứng dụng có lỗ hổng thật. Mạng `labnet` đặt
> `internal: true` và không publish cổng ra host. Chỉ các container trong lab được
> giao tiếp với DVWA/bWAPP. Không bỏ cấu hình cách ly khi chạy thử payload.

## 1. Yêu cầu

- Docker Engine và Docker Compose v2 (`docker compose version` chạy được)
- Kết nối internet ở lần chạy đầu để tải image

## 2. Thành phần

| Dịch vụ | Image | Địa chỉ nội bộ | Ghi chú |
|---|---|---|---|
| DVWA | `ghcr.io/digininja/dvwa` | `http://dvwa` | Cần database riêng |
| MariaDB (cho DVWA) | `mariadb:10` | không mở ra ngoài | Chỉ DVWA truy cập được qua mạng `labnet` |
| bWAPP | `raesene/bwapp` | `http://bwapp` | Đã gói sẵn web server + database |

## 3. Cấu trúc thư mục

```
lab/
├── docker-compose.yml
└── README.md
```

## 4. Khởi chạy

```bash
cd lab
docker compose up -d
docker compose ps        # cả 3 dịch vụ phải ở trạng thái running
```

## 5. Truy cập từ script kiểm thử

Script sinh traffic phải chạy trong một container cùng mạng `labnet` và gọi dịch
vụ bằng tên `http://dvwa` hoặc `http://bwapp`. Thiết kế này cố ý không cho trình
duyệt trên host truy cập trực tiếp ứng dụng có lỗ hổng.

## 6. Kiểm tra lab hoạt động

Kiểm tra trạng thái container bằng `docker compose ps`. Việc khởi tạo database và
gửi traffic thật sẽ được tự động hóa trong `lab_verification/` trước Tuần 5; chưa
đánh dấu lab end-to-end hoàn tất chỉ dựa trên trạng thái `running`.

## 7. Dừng và tái lập

```bash
docker compose stop                          # tạm dừng, giữ dữ liệu
docker compose down                          # xóa container, giữ dữ liệu database
docker compose down -v && docker compose up -d   # reset sạch hoàn toàn
```

Sau lệnh reset sạch, dữ liệu database phải được khởi tạo lại trước khi sinh traffic.
