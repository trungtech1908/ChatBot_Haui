# Khởi tạo database

Script `backend/scripts/init_db.py` tạo database PostgreSQL, chạy migration (Alembic) và nạp dữ liệu từ `backend/assets/seed/`.

Script chạy trên máy, **không nằm trong Docker**: container backend chỉ chạy API, không tự tạo bảng hay nạp dữ liệu. Phải khởi tạo database trước khi mở app lần đầu.

## Cấu trúc

Thiết kế đầy đủ ở [haui_db/ARCHITECTURE.md](../haui_db/ARCHITECTURE.md) mục 4 và 6. Tóm tắt:

| Schema | Nội dung | Ai truy cập |
|---|---|---|
| `core` | 40 bảng nghiệp vụ: 34 bảng theo thiết kế gốc + 6 bảng giảng dạy (`giang_vien`, `lich_hoc`, `lich_thi`, `lich_thi_sv`, `doanh_nghiep`, `thuc_tap`) | owner (`DB_USER`) |
| `private` | `tai_khoan` | owner, dịch vụ đăng nhập |
| `chatbot` | 27 view: 24 theo thiết kế gốc + `v_lich_hoc`, `v_lich_thi`, `v_thuc_tap` | role `chatbot_reader` |
| `public` | `chat_message`, bảng checkpointer của LangGraph (tự tạo khi backend khởi động) | owner |

Migration tạo sẵn login role `DB_CHATBOT_USER` thuộc `chatbot_reader`: chỉ `SELECT` được schema `chatbot`, `statement_timeout = 5s`. View `v_*` tự lọc theo `app.ma_sv`; backend đặt giá trị này bằng `set_config` trong transaction `READ ONLY` trước khi chạy SQL của Text2SQL. Chưa đặt thì view trả 0 dòng.

Nguồn sự thật khi chạy:

| Thành phần | File |
|---|---|
| Bảng | model SQLAlchemy `backend/src/chatbot_haui/db/models/` + Alembic |
| View, function `chatbot.ma_sv()`, phân quyền | `backend/src/chatbot_haui/db/sql/views.sql` (Alembic thực thi) |
| Tham số lấy từ văn bản | `backend/assets/seed/02_seed_tham_so.sql` |
| Dữ liệu giả lập | `backend/assets/seed/04_sample_data.sql`, sinh bởi `backend/scripts/gen_sample_data.py` |

`haui_db/01_schema.sql`, `03_views_chatbot.sql` là bản tài liệu (nạp độc lập được theo thứ tự 01 → 02 → 03 → 04), phải giữ khớp với nguồn ở trên.

## Yêu cầu

- PostgreSQL 14+ đang chạy: dùng service `postgres` trong `docker compose` hoặc PostgreSQL cài sẵn
- [uv](https://docs.astral.sh/uv/)
- `.env` ở thư mục gốc repo:

| Biến | Mô tả |
|---|---|
| `DB_HOST` | Để `localhost` khi chạy script trên máy |
| `DB_PORT` | Cổng PostgreSQL trên máy; với Docker, compose mở PostgreSQL ra đúng cổng này |
| `DB_USER`, `DB_PASSWORD` | Owner. Với Docker, đây cũng là tài khoản tạo lúc khởi tạo volume |
| `DB_NAME` | Tên database, script tự tạo nếu chưa có |
| `DB_CHATBOT_USER`, `DB_CHATBOT_PASSWORD` | Login role cho Text2SQL, migration tự tạo/đặt lại mật khẩu |

## Chạy

```bash
# 1. Bật PostgreSQL (bỏ qua nếu dùng PostgreSQL cài sẵn)
docker compose up -d --wait postgres

# 2. Khởi tạo database từ máy
cd backend
uv sync --extra cpu
uv run --no-sync python scripts/init_db.py
```

| Lệnh | Tác dụng |
|---|---|
| `scripts/init_db.py` | Tạo database nếu chưa có, migrate, nạp dữ liệu mẫu |
| `scripts/init_db.py --no-seed` | Chỉ tạo database và migrate |
| `scripts/init_db.py --reset` | **Xóa sạch** database rồi tạo lại (hỏi xác nhận) |
| `scripts/init_db.py --reset -y` | Như trên, không hỏi xác nhận |

Chạy lại nhiều lần vẫn an toàn: migration đã chạy thì bỏ qua, đã có sinh viên thì không nạp lại.

Output mẫu:

```
Database CSDLDoAnCN đã sẵn sàng
Chạy migration...
Running upgrade  -> c996469711a7, schema core/private/chatbot cho PostgreSQL
Nạp 02_seed_tham_so.sql...
Nạp 04_sample_data.sql...
Đã nạp: 62 sinh viên, 62 tài khoản, 2163 điểm học phần, 1399 buổi lịch học
Xong: CSDLDoAnCN @ localhost:5432
```

## Dữ liệu giả lập

62 sinh viên (5 ngành × khóa K17–K20), chốt ngày 31/08/2026. Điểm, kết quả học kỳ, rèn luyện, học bổng, học phí được **tính theo quy chế** chứ không random độc lập (xem docstring `gen_sample_data.py`). Mức học bổng KKHT, NTB, tài trợ là số minh họa.

**Đăng nhập: tên đăng nhập = mật khẩu = mã sinh viên** (hash argon2). Sinh viên theo từng tình huống kiểm thử (học bổng, miễn giảm, kỷ luật, nợ học phí, thực tập...): [ARCHITECTURE.md mục 7](../haui_db/ARCHITECTURE.md#7-đánh-giá).

Sinh lại dữ liệu (tất định: cùng code → cùng file, không phụ thuộc máy):

```bash
cd backend
uv run --no-sync python scripts/gen_sample_data.py      # ghi assets/seed/04_sample_data.sql
uv run --no-sync python scripts/init_db.py --reset -y   # nạp lại
```

Các bảng bổ sung (giảng viên, lịch học, lịch thi, thực tập) dùng bộ sinh số ngẫu nhiên riêng, chạy sau cùng, nên sửa phần này không làm thay đổi dữ liệu các bảng gốc.

## Khi đổi cấu trúc

Bảng: sửa model trong `backend/src/chatbot_haui/db/models/`, rồi từ `backend/`:

```bash
uv run --no-sync alembic revision --autogenerate -m "mô tả thay đổi"   # đọc lại file sinh ra trước khi commit
uv run --no-sync python scripts/init_db.py --no-seed                     # áp dụng
```

View: tạo migration mới `op.execute(...)` với `CREATE OR REPLACE VIEW` (hoặc `DROP VIEW` + `CREATE VIEW` khi đổi cột), cập nhật `db/sql/views.sql` và `haui_db/03_views_chatbot.sql` cho khớp, rồi thêm mô tả view vào `VIEW_DOCS` trong `ai/prompts/text2sql.py` (test `test_all_views_described_in_prompt` báo nếu thiếu). Sau khi tạo view mới phải `GRANT SELECT ... TO chatbot_reader`.

## Lỗi thường gặp

| Lỗi | Cách xử lý |
|---|---|
| `Không kết nối được PostgreSQL localhost:5432` | PostgreSQL chưa chạy, sai `DB_PORT`, hoặc chưa `docker compose up -d postgres` |
| `password authentication failed for user "postgres"` | Sai `DB_PASSWORD`. Với Docker, mật khẩu chỉ áp dụng lúc tạo volume lần đầu: đổi mật khẩu thì phải `docker compose down -v` |
| Chatbot báo lỗi, log có `password authentication failed for user "chatbot_app"` | Đổi `DB_CHATBOT_PASSWORD` sau khi migrate: chạy `init_db.py --reset -y` để migration đặt lại mật khẩu role |
| `permission denied for schema core` trong log Text2SQL | Đúng thiết kế: SQL do LLM sinh đã cố đọc ngoài schema `chatbot` |
