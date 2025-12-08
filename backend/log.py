from fastapi import APIRouter, Depends, Response, Request, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db      # get_db 함수는 database.py에서 가져옵니다.
from models import UserModel     # UserModel 클래스는 models.py에서 가져옵니다.
from utils import verify_password


router = APIRouter()

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/login")
def login(data: LoginRequest, response: Response, db: Session = Depends(get_db)):
    print(f"✅ 로그인 시도 username: '{data.username}', password: '{data.password}'")
    user = db.query(UserModel).filter(UserModel.username == data.username).first()
    if not user or not verify_password(data.password, user.password):
        raise HTTPException(status_code=401, detail="아이디 또는 비밀번호가 틀렸습니다.")
    response.set_cookie(key="user", value=user.username, httponly=True)
    return {"message": "로그인 성공", "username": user.username,
        "is_admin": user.is_admin }

@router.get("/api/user")
def get_user(request: Request, db: Session = Depends(get_db)):
    username = request.cookies.get("user")
    if not username:
        return {"loggedIn": False}
    user = db.query(UserModel).filter(UserModel.username == username).first()
    if not user:
        return {"loggedIn": False}
    return {
        "loggedIn": True,
        "username": user.username,
        "email": user.email,
        "contact_type": user.contact_type,
        "contact_value": user.contact_value,
        "is_admin": user.is_admin
    }

@router.post("/api/logout")
def logout(response: Response):
    response.delete_cookie("user")
    return {"message": "로그아웃 성공"}
