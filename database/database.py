from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import pymysql

# --- CẤU HÌNH DATABASE ---
DB_NAME = 'CSDLDoAnCN'
DB_USER = 'root'
DB_PASS = '123456'
DB_HOST = 'localhost'
DB_PORT = '3306'

# 1. URL KẾT NỐI ĐẾN SERVER CHUNG (Dùng để tạo DB nếu chưa có)
# Loại bỏ tên database khỏi URL
SERVER_URL = f'mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}'

# 2. URL KẾT NỐI ĐẦY ĐỦ (Dùng cho SQLAlchemy Engine)
URL_DATABASE = f'{SERVER_URL}/{DB_NAME}'

# --- HÀM TẠO DATABASE NẾU CHƯA CÓ ---
def create_database_if_not_exists():
    """Tạo database MySQL nếu nó chưa tồn tại."""
    # Tạo một Engine tạm thời kết nối đến Server, KHÔNG phải database cụ thể
    server_engine = create_engine(SERVER_URL)
    
    try:
        # Mở kết nối
        with server_engine.connect() as connection:
            # Kiểm tra và tạo database
            print(f"Kiểm tra database '{DB_NAME}'...")
            
            # Sử dụng cú pháp SQL để tạo database nếu chưa tồn tại
            # Dùng 'text()' để truyền câu lệnh SQL thô
            connection.execute(text(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"))
            connection.commit()
            print(f"✅ Database '{DB_NAME}' đã sẵn sàng.")
            
    except Exception as e:
        # Đây là lỗi nếu không thể kết nối đến máy chủ MySQL/MariaDB
        print(f"❌ LỖI KẾT NỐI SERVER: Không thể tạo database. Chi tiết: {e}")
        raise

# --- THỰC HIỆN TẠO DATABASE TRƯỚC KHI TẠO ENGINE CHÍNH ---
create_database_if_not_exists()

# --- CẤU HÌNH SQLALCHEMY ORM ---
# Engine chính kết nối đến database đã được đảm bảo tồn tại
engine = create_engine(URL_DATABASE)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()