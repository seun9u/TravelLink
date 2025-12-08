from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db      # 👈 수정된 부분 1
from models import UserModel     # 👈 수정된 부분 2
from utils import hash_password
from typing import Optional


router = APIRouter()

class Contact(BaseModel):
    type: str
    value: str

class User(BaseModel):
    username: str
    email: str
    password: str
    contact: Contact
    is_admin: Optional[bool] = False

@router.post("/register")
def register(user: User, db: Session = Depends(get_db)):
    
    # 1. 이메일 중복 확인
    existing_email = db.query(UserModel).filter(UserModel.email == user.email).first()
    if existing_email:
        # FastAPI의 HTTPException을 사용하여 명확한 오류를 반환
        raise HTTPException(status_code=400, detail="이미 가입된 이메일입니다.")

    # 2. 사용자 아이디 중복 확인 (👈 이 로직 추가)
    existing_username = db.query(UserModel).filter(UserModel.username == user.username).first()
    if existing_username:
        raise HTTPException(status_code=400, detail="이미 사용 중인 아이디입니다.")

    new_user = UserModel(
        username=user.username,
        email=user.email,
        password=hash_password(user.password),
        contact_type=user.contact.type,
        contact_value=user.contact.value,
        is_admin=user.is_admin
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": f"{user.username} 회원가입이 완료되었습니다."}