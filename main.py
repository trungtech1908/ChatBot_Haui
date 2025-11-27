from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from database.database import engine, Base, SessionLocal
from database.seeder import seed_database

from routers import auth, dashboard, chat

# --- KHỞI TẠO APP ---
app = FastAPI(
    title="Student Management System",
    description="Hệ thống Quản lý Sinh viên - Modular Structure",
    version="2.1.0"
)

# --- CẤU HÌNH STATIC FILES ---
app.mount("/static", StaticFiles(directory="templates"), name="static")


# --- KHỞI TẠO DB & SEED DATA ---
@app.on_event("startup")
def startup_event():
    print("\n[STARTUP] 🚀 Khởi động hệ thống...")
    Base.metadata.create_all(bind=engine)

    # Nạp dữ liệu mẫu
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    print("[STARTUP] ✅ Hệ thống sẵn sàng!\n")


# --- GẮN CÁC ROUTER VÀO APP ---
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(chat.router)