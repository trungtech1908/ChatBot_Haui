# Khởi tạo database

Script `backend/scripts/init_db.py` tạo database PostgreSQL, chạy migration (Alembic) và nạp dữ liệu từ `backend/assets/seed/`.

Script chạy trên máy, **không nằm trong Docker**: container backend chỉ chạy API, không tự tạo bảng hay nạp dữ liệu. Phải khởi tạo database trước khi mở app lần đầu.

## Cấu trúc

Tóm tắt:

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

**Đăng nhập: tên đăng nhập = mật khẩu = mã sinh viên** (hash argon2). Sinh viên theo từng tình huống kiểm thử:

| Tình huống | Mã SV |
|---|---|
| HB HaUI toàn khóa / năm nhất / 5 triệu | 2025619166 / 2025637924 / 2025628155 |
| Khuyết tật: miễn học phí, nhận HB NTB | 2024619567 |
| DTTS hộ nghèo: miễn học phí, hỗ trợ chi phí học tập | 2025646999 |
| Hộ cận nghèo, học lực xuất sắc, đủ điều kiện tham gia xét KKHT | 2023655593 |
| Học lực giỏi nhưng trượt điều kiện HB kỳ gần nhất vì rèn luyện 68 điểm | 2024628144 |
| Mồ côi cha: nhận HB NTB | 2024633657 |
| Cha bị TNLĐ: giảm 50% học phí | 2023629820 |
| Kỷ luật cảnh cáo / khiển trách | 2023619595 / 2024642770 |
| Bảo lưu rồi quay lại | 2023634292 |
| Buộc thôi học | 2024643553 |
| Có điểm I | 2024658893 |
| Olympic quốc gia, HB tài trợ | 2023617043 |
| Còn nợ học phí | 2023654041, 2022632465, 2023625316, 2024619980, 2024639830, 2025651790, 2023655593 |
| K17 chưa tốt nghiệp vì thiếu ngoại ngữ | 2022632465, 2022659727 |
| Có kỳ thực tập doanh nghiệp (K17) | 2022612814, 2022623840 |
| Có ca thi không đủ điều kiện dự thi | 2025629882, 2023654041 |

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

View: tạo migration mới `op.execute(...)` với `CREATE OR REPLACE VIEW` (hoặc `DROP VIEW` + `CREATE VIEW` khi đổi cột), cập nhật `db/sql/views.sql` cho khớp, rồi thêm mô tả view vào `VIEW_DOCS` trong `ai/prompts/text2sql.py` (test `test_all_views_described_in_prompt` báo nếu thiếu). Sau khi tạo view mới phải `GRANT SELECT ... TO chatbot_reader`.

## Lỗi thường gặp

| Lỗi | Cách xử lý |
|---|---|
| `Không kết nối được PostgreSQL localhost:5432` | PostgreSQL chưa chạy, sai `DB_PORT`, hoặc chưa `docker compose up -d postgres` |
| `password authentication failed for user "postgres"` | Sai `DB_PASSWORD`. Với Docker, mật khẩu chỉ áp dụng lúc tạo volume lần đầu: đổi mật khẩu thì phải `docker compose down -v` |
| Chatbot báo lỗi, log có `password authentication failed for user "chatbot_app"` | Đổi `DB_CHATBOT_PASSWORD` sau khi migrate: chạy `init_db.py --reset -y` để migration đặt lại mật khẩu role |
| `permission denied for schema core` trong log Text2SQL | Đúng thiết kế: SQL do LLM sinh đã cố đọc ngoài schema `chatbot` |
