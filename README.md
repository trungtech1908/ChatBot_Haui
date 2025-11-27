CÁC FILE SỬ DỤNG:
1. File Chính (Root)
- main.py: "Cửa chính" của ứng dụng. File này khởi tạo FastAPI, kết nối Database, cấu hình file tĩnh (CSS/JS) và gom các Router (Auth, Dashboard, Chat) lại để chạy Server.

2. Thư mục routers/ (Xử lý Logic - Controller)
- auth.py: Xử lý Đăng nhập & Đăng xuất. Kiểm tra tài khoản/mật khẩu và điều hướng người dùng.
- dashboard.py: Xử lý logic cho Màn hình chính. Chứa các câu truy vấn phức tạp để lấy thông tin sinh viên, điểm số, lịch học, công nợ... và đẩy sang giao diện.
- chat.py: Xử lý API cho Chatbot. Nhận tin nhắn, lưu vào file JSON và xử lý lệnh xóa lịch sử chat.

3. Thư mục database/ (Cơ sở dữ liệu - Model)
- database.py: Cấu hình kết nối tới MySQL. Tạo ra Session để code có thể nói chuyện với Database.
- models.py: Định nghĩa cấu trúc bảng (SQLAlchemy). Biến các bảng SQL thành các Class Python (ví dụ: bảng sinhVien thành class SinhVien).
- schemas.py: Kiểm tra dữ liệu đầu vào/ra (Pydantic). Đảm bảo dữ liệu gửi đi hoặc nhận về đúng định dạng (ví dụ: email phải là chuỗi, diem phải là số).
- seeder.py: Nạp dữ liệu mẫu. Đọc các file trong thư mục json/ và tự động điền vào Database khi khởi động nếu bảng còn trống.

4. Thư mục templates/ (Giao diện - View)
- html/layout.html: Khung sườn chung. Chứa Header (Logo, nút Đăng xuất) và cấu trúc chia cột (Menu trái - Nội dung phải).
- html/login.html: Trang Đăng nhập.
- html/sidebar_menu.html: Thanh Menu bên trái. Chứa thông tin tóm tắt sinh viên và các nút chuyển đổi chức năng.
- html/content.html: Nội dung chính. Chứa toàn bộ code hiển thị Bảng điểm, Lịch học, Tài chính, CTĐT... (được ẩn/hiện bằng JS).
- html/chat.html: Giao diện Chatbot. Bao gồm cả HTML hiển thị tin nhắn và Javascript xử lý gửi/nhận tin.
- html/dashboard.html: Trang chủ tổng hợp. Kế thừa từ layout.html và nhúng sidebar, content, chat vào một chỗ.

5. Thư mục json/ (Dữ liệu nguồn)
- Các file số (01_..., 02_...): Chứa dữ liệu thô để nạp vào Database lúc đầu.
- chat_data.json: Nơi lưu trữ lịch sử tin nhắn của Chatbot.

HƯỚNG DẪN CHẠY:
1. Cài đặt các thư viện cần thiết:
`python -m pip install fastapi`
`python -m pip install sqlalchemy`
`python -m pip install uvicorn`

2. Tạo mySQL Connection trong mySQL:
username:`root`
password:`test1234!`

3. chạy `python -m uvicorn main:app --reload` được nhập trong terminal

4. hủy chạy Ctrl+C