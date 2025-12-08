from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
import random
import string

from database import get_db
from models import UserModel
from utils import hash_password

router = APIRouter()

class ForgotPasswordRequest(BaseModel):
    username: str

@router.post("/forgot-password")
def forgot_password(data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.username == data.username.strip()).first()
    if not user:
        raise HTTPException(status_code=404, detail="가입된 아이디가 없습니다.")
    
    temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    user.password = hash_password(temp_password)
    db.commit()
    
    return {"message": "임시 비밀번호가 발급되었습니다.", "temp_password": temp_password}