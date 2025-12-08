# find_username_router.py (최종 수정본)

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
# 🚨 models.py에 정의된 UserModel과 get_db를 정확히 임포트합니다.
from database import get_db                      
from models import UserModel            # users 테이블에 매핑된 SQLAlchemy 모델

# ----------------------------------------------------
# Pydantic 모델 정의
# ----------------------------------------------------

router = APIRouter()

# 요청 바디를 정의하는 Pydantic 모델
class FindUsernameRequest(BaseModel):
    email: str

# ----------------------------------------------------
# FastAPI 라우터 구현 (MySQL/SQLAlchemy 사용)
# ----------------------------------------------------

@router.post("/find-username")
def find_username_api(
    request_data: FindUsernameRequest,
    db: Session = Depends(get_db) # DB 세션 의존성 주입
):
    """이메일을 통해 사용자 아이디를 MySQL DB에서 찾습니다."""
    email = request_data.email

    try:
        # 🔽 수정: models.py의 UserModel을 사용하여 쿼리합니다.
        user = db.query(UserModel).filter(UserModel.email == email).first()

        if user:
            # 사용자가 존재하는 경우, username 반환
            return {"username": user.username}
        else:
            # 사용자가 존재하지 않는 경우
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="해당 이메일로 등록된 아이디가 없습니다."
            )
    except Exception as e:
        # 일반적인 DB 오류 또는 서버 오류를 처리합니다.
        print(f"❌ 데이터베이스 쿼리 오류 발생: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="아이디를 찾는 중 서버 오류가 발생했습니다."
        )


