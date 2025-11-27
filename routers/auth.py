from fastapi import APIRouter, Depends, status, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import database.models as models
from database.database import get_db

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse, name="login_page")
def get_login_page(request: Request):
    return templates.TemplateResponse("html/login.html", {"request": request})

@router.post("/login", response_class=HTMLResponse)
def login(
    request: Request, 
    username: str = Form(...), 
    password: str = Form(...), 
    db: Session = Depends(get_db)
):
    user = db.query(models.TaiKhoan).filter(
        models.TaiKhoan.tenTaiKhoan == username, 
        models.TaiKhoan.matKhau == password
    ).first()
    
    if user:
        return RedirectResponse(url=f"/welcome?username={user.tenTaiKhoan}", status_code=status.HTTP_303_SEE_OTHER)
    else:
        return templates.TemplateResponse(
            "html/login.html", 
            {"request": request, "error": "Sai tài khoản hoặc mật khẩu."}, 
            status_code=status.HTTP_401_UNAUTHORIZED
        )

@router.get("/logout")
def logout():
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)