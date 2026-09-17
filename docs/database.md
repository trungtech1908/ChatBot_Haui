# Khởi tạo database

Script `backend/scripts/init_db.py` tạo database, chạy migration (Alembic) và nạp dữ liệu mẫu từ `backend/assets/seed/`.

Script chạy trên máy, **không nằm trong Docker**: container backend chỉ chạy API, không tự tạo bảng hay nạp dữ liệu. Phải khởi tạo database trước khi mở app lần đầu.

## Yêu cầu

- MySQL 8 đang chạy: dùng MySQL trong `docker compose` hoặc MySQL cài sẵn trên máy
- [uv](https://docs.astral.sh/uv/)
- `.env` ở thư mục gốc repo đã điền phần MySQL:

| Biến          | Mô tả                                                                 |
|---------------|-----------------------------------------------------------------------|
| `DB_HOST`     | Để `localhost` khi chạy script trên máy                               |
| `DB_PORT`     | Cổng MySQL trên máy; với Docker, compose mở MySQL ra đúng cổng này    |
| `DB_USER`     | `root` nếu dùng MySQL của Docker                                      |
| `DB_PASSWORD` | Mật khẩu; với Docker đây cũng là mật khẩu root lúc tạo container      |
| `DB_NAME`     | Tên database, script tự tạo nếu chưa có                               |

## Chạy

### Dùng MySQL trong Docker

```bash
# 1. Chỉ bật MySQL
docker compose up -d --wait mysql

# 2. Khởi tạo database từ máy
cd backend
uv sync --extra cpu
uv run python scripts/init_db.py

# 3. Bật toàn bộ app
cd ..
docker compose up -d --build
```

Nếu máy đã có MySQL chiếm cổng 3306, đổi `DB_PORT` trong `.env` (ví dụ `3307`) trước bước 1.

### Dùng MySQL cài sẵn trên máy

```bash
cd backend
uv sync --extra cpu
uv run python scripts/init_db.py
```

## Tùy chọn

| Lệnh                                            | Tác dụng                                              |
|-------------------------------------------------|-------------------------------------------------------|
| `uv run python scripts/init_db.py`              | Tạo database nếu chưa có, migrate, nạp dữ liệu mẫu    |
| `uv run python scripts/init_db.py --no-seed`    | Chỉ tạo database và migrate, không nạp dữ liệu mẫu    |
| `uv run python scripts/init_db.py --reset`      | **Xóa sạch** database rồi tạo lại (hỏi xác nhận)      |
| `uv run python scripts/init_db.py --reset -y`   | Như trên, không hỏi xác nhận                          |

Chạy lại nhiều lần vẫn an toàn: migration đã chạy thì bỏ qua, bảng đã có dữ liệu thì không nạp lại.

Output mẫu:

```
Database CSDLDoAnCN đã sẵn sàng
Chạy migration...
Running upgrade  -> a1ee8f6ee390, initial schema
Nạp dữ liệu mẫu từ assets/seed...
Đã nạp 7 bản ghi vào khoa
...
Xong: CSDLDoAnCN @ localhost:3306
```

Tài khoản mẫu sau khi seed: `SV001_tk` / `pass001` … `SV010_tk` / `pass010`.

## Khi đổi cấu trúc bảng

Sửa model trong `backend/src/chatbot_haui/db/models/`, rồi từ `backend/`:

```bash
uv run alembic revision --autogenerate -m "mô tả thay đổi"   # sinh file migration, nên đọc lại trước khi commit
uv run python scripts/init_db.py --no-seed                     # áp dụng migration
```

## Lỗi thường gặp

| Lỗi                                                  | Cách xử lý                                                                 |
|------------------------------------------------------|----------------------------------------------------------------------------|
| `Không kết nối được MySQL localhost:3306`            | MySQL chưa chạy, sai `DB_PORT`, hoặc chưa `docker compose up -d mysql`     |
| `Access denied for user 'root'`                      | Sai `DB_PASSWORD`. Với Docker, mật khẩu chỉ áp dụng lúc tạo volume lần đầu: đổi mật khẩu thì phải `docker compose down -v` |
| `Table '...' already exists`                         | Database cũ tạo từ phiên bản trước (không có Alembic): chạy `--reset`      |
| Backend báo lỗi `Table ... doesn't exist`            | Chưa chạy `init_db.py`                                                     |
