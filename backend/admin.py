from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from pydantic import BaseModel
from typing import List
from db import UserModel
from database import get_db 

# =========================================================
# ✨ Pydantic 스키마 정의 (핵심 수정 사항)
# =========================================================

# 사용자 목록 반환을 위한 Pydantic 스키마
class UserSchema(BaseModel):
    id: int
    username: str
    email: str
    is_admin: int
    
    class Config:
        # ORM 모드 활성화: SQLAlchemy 모델 객체를 Pydantic 스키마로 변환 가능하게 함
        # Pydantic v2에서 사용되는 설정입니다.
        from_attributes = True 
        
# 기존 Pydantic 모델
class UserRoleUpdate(BaseModel):
    is_admin: bool

class UserStatusUpdate(BaseModel):
    is_active: bool
    
class BulkUsernames(BaseModel):
    usernames: List[str]

# 통합 Pydantic 모델
class BulkRoleUpdate(BaseModel):
    is_admin: bool
    usernames: List[str]

router = APIRouter()

# =========================================================
# ✨ API 엔드포인트 (수정된 get_all_users 포함)
# =========================================================

# 사용자 목록 조회 API
# ✨ response_model=List[UserSchema]를 지정하여 직렬화 문제를 해결합니다.
@router.get("/api/users", response_model=List[UserSchema]) 
def get_all_users(db: Session = Depends(get_db), search: str = None):
    query = db.query(UserModel)
    if search:
        query = query.filter(or_(
            UserModel.username.ilike(f"%{search}%"),
            UserModel.email.ilike(f"%{search}%")
        ))
    users = query.all()
    # SQLAlchemy ORM 객체가 Pydantic UserSchema 목록으로 직렬화되어 반환됩니다.
    return users

# 사용자 상태(is_active) 변경 API (UserModel에 is_active가 있어야 작동)
@router.put("/api/users/{username}/status")
def toggle_user_status(username: str, status_update: UserStatusUpdate, db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # db.py의 UserModel에 'is_active' 필드가 추가되었거나 이미 존재해야 합니다.
    user.is_active = status_update.is_active
    db.commit()
    
    return {"message": f"User {username} status updated to {'active' if user.is_active else 'inactive'}", "is_active": user.is_active}


# 단일 사용자 관리자 역할 변경 API
@router.put("/api/users/{username}/role")
def toggle_user_role(username: str, role_update: UserRoleUpdate, db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # UserModel.is_admin이 Integer(0 또는 1)이므로 변환하여 저장
    new_role = 1 if role_update.is_admin else 0
    user.is_admin = new_role
    db.commit()
    
    action = 'admin' if new_role else 'user'
    return {"message": f"User {username} admin status updated to {action}", "is_admin": user.is_admin}


# 일괄 사용자 역할 변경 API (Admin.jsx에서 호출하는 경로)
@router.put("/api/admin/bulk/role-update")
def bulk_toggle_user_role(update_data: BulkRoleUpdate, db: Session = Depends(get_db)):
    users_to_update = db.query(UserModel).filter(UserModel.username.in_(update_data.usernames)).all()
    
    if not users_to_update:
        raise HTTPException(status_code=404, detail="No valid users found for update")

    # update_data.is_admin은 bool이므로 0 또는 1로 변환
    new_role = 1 if update_data.is_admin else 0
    
    for user in users_to_update:
        user.is_admin = new_role
        
    db.commit()
    
    action = 'admin' if new_role else 'user'
    return {"message": f"Successfully updated role to {action} for {len(users_to_update)} users", "count": len(users_to_update)}


# 일괄 사용자 계정 삭제 API
@router.delete("/api/users/bulk/delete")
def bulk_delete_user(user_list: BulkUsernames, db: Session = Depends(get_db)):
    users_to_delete = db.query(UserModel).filter(UserModel.username.in_(user_list.usernames)).all()

    if not users_to_delete:
        raise HTTPException(status_code=404, detail="No valid users found for deletion")

    deleted_count = 0
    for user in users_to_delete:
        db.delete(user)
        deleted_count += 1
        
    db.commit()
    
    return {"message": f"Successfully deleted {deleted_count} users", "count": deleted_count}


# 단일 사용자 계정 삭제 API
@router.delete("/api/users/{username}")
def delete_user(username: str, db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(user)
    db.commit()
    
    return {"message": f"User {username} deleted successfully"}