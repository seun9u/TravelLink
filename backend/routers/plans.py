from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from database import get_db
from models import Plan

router = APIRouter()

# ======================
# Pydantic 요청 모델
# ======================
class PlanCreate(BaseModel):
    title: str
    username: Optional[str] = "익명"
    destination: Optional[str] = ""
    date: Optional[str] = None
    summary: Optional[str] = ""
    participants: Optional[int] = 1
    capacity: Optional[int] = 4
    tags: Optional[str] = ""
    itinerary: dict  # JSON 형식 일정

class PlanOut(BaseModel):
    id: int
    title: str
    username: str
    destination: Optional[str]
    summary: Optional[str]
    participants: int
    capacity: int
    views: int
    tags: Optional[str]
    date: Optional[str]
    created_at: str

    class Config:
        orm_mode = True

# ======================
# POST /plans - 저장
# ======================
@router.post("/plans")
def create_plan(plan: PlanCreate, db: Session = Depends(get_db)):
    db_plan = Plan(**plan.dict())
    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)
    return {"message": "계획이 저장되었습니다.", "id": db_plan.id}

# ======================
# GET /plans - 목록 조회
# ======================
@router.get("/plans", response_model=List[PlanOut])
def get_plans(db: Session = Depends(get_db)):
    plans = db.query(Plan).order_by(Plan.created_at.desc()).all()
    return plans
