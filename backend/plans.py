from fastapi import APIRouter, Depends, HTTPException, Request, Body
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import google.generativeai as genai
import json
import re

from database import get_db
from models import Plan, PlanApplication, PlanParticipant

# APIRouter 인스턴스 생성
router = APIRouter()

# --- Pydantic 모델 정의 ---

class PlanCreate(BaseModel):
    title: str
    username: Optional[str] = "익명"
    destination: Optional[str] = ""
    date: Optional[str] = None
    summary: Optional[str] = ""
    participants: Optional[int] = 1
    capacity: Optional[int] = 4
    tags: Optional[str] = ""
    itinerary: dict

class PlanOut(BaseModel):
    # Pydantic V2에서는 orm_mode 대신 from_attributes=True를 사용합니다.
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    title: str
    username: str
    destination: Optional[str]
    summary: Optional[str]
    participants: int
    capacity: int
    views: int
    tags: Optional[str]
    
    # ✅ [수정됨] date 타입을 DB와 일치하는 str(문자열)로 변경
    date: Optional[str]
    itinerary: dict 
    
    created_at: datetime
    

class RecommendRequest(BaseModel):
    selectedLocation: Optional[str] = None
    travelArea: str
    travelDuration: Optional[str] = None # "3박 4일" 같은 문자열을 받을 필드
    startDate: Optional[str] = None      # 이제 필수가 아닌 선택사항
    endDate: Optional[str] = None        # 이제 필수가 아닌 선택사항
    interests: List[str]
    budget: Optional[str] = None
    transport: Optional[List[str]] = []
    avoid: Optional[List[str]] = []
    restaurantStyle: Optional[List[str]] = []
    visa: Optional[str] = None
    flightTime: Optional[str] = None
    travelStyle: Optional[List[str]] = []

class SuggestResponse(BaseModel):
    locations: List[str]

# --- API 엔드포인트들 ---

@router.post("/plans", tags=["Plans"])
def create_plan(plan: PlanCreate, db: Session = Depends(get_db)):
    try:
        # Pydantic V2에서는 .dict() 대신 .model_dump()를 사용합니다.
        db_plan = Plan(**plan.model_dump())
        db.add(db_plan)
        db.commit()
        db.refresh(db_plan)
        return {"message": "🎉 계획이 저장되었습니다!", "id": db_plan.id}
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"데이터베이스 저장 중 오류: {str(e)}")

@router.get("/plans", response_model=List[PlanOut], tags=["Plans"])
def get_plans(db: Session = Depends(get_db)):
    return db.query(Plan).order_by(Plan.created_at.desc()).all()

@router.get("/plan/{plan_id}", response_model=PlanOut, tags=["Plans"])
def get_plan_detail(plan_id: int, db: Session = Depends(get_db)):
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    plan.views += 1
    db.commit()
    return plan # ✅ [수정됨] PlanOut 모델이 자동으로 변환해주므로 코드가 깔끔해집니다.

@router.put("/plan/{plan_id}", tags=["Plans"])
def update_plan(plan_id: int, updated: PlanCreate, db: Session = Depends(get_db)):
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    update_data = updated.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(plan, key, value)
        
    db.commit()
    db.refresh(plan)
    return {"message": "계획이 수정되었습니다."}

@router.delete("/plan/{plan_id}", tags=["Plans"])
def delete_plan(plan_id: int, db: Session = Depends(get_db)):
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    try:
        db.delete(plan)
        db.commit()
        return {"message": "Plan deleted successfully"}
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"삭제 중 오류: {str(e)}")

# ... 이하 신청, 참가, Gemini 관련 코드는 기존과 동일하게 유지 ...

@router.post("/plans/{plan_id}/apply", tags=["Plans Actions"])
async def apply_plan(plan_id: int, request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    application = PlanApplication(plan_id=plan_id, **data)
    db.add(application)
    db.commit()
    return {"message": "신청 완료"}

@router.get("/plan/{plan_id}/applications", tags=["Plans Actions"])
def get_plan_applications(plan_id: int, db: Session = Depends(get_db)):
    return db.query(PlanApplication).filter(PlanApplication.plan_id == plan_id).all()

@router.post("/plan/{plan_id}/accept", tags=["Plans Actions"])
async def accept_applicant(plan_id: int, request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    username = data.get("username")
    if not username:
        raise HTTPException(status_code=400, detail="username은 필수입니다.")
    
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="해당 계획이 존재하지 않습니다.")
    if plan.participants >= plan.capacity:
        raise HTTPException(status_code=400, detail="모집 정원이 이미 찼습니다.")
    
    application = db.query(PlanApplication).filter_by(plan_id=plan_id, username=username).first()
    if not application:
        raise HTTPException(status_code=404, detail="신청 내역을 찾을 수 없습니다.")
    
    participant = PlanParticipant(
        plan_id=plan_id,
        username=username,
        contact_type=application.contact_type,
        contact_value=application.contact_value,
        travel_style=application.travel_style,
    )
    db.add(participant)
    plan.participants += 1
    db.delete(application)
    db.commit()
    return {"message": "합류 완료"}

@router.get("/plan/{plan_id}/participants", tags=["Plans Actions"])
def get_participants(plan_id: int, db: Session = Depends(get_db)):
    return db.query(PlanParticipant).filter(PlanParticipant.plan_id == plan_id).all()

@router.post("/plan/{plan_id}/participants/remove", tags=["Plans Actions"])
def remove_participant(plan_id: int, data: dict, db: Session = Depends(get_db)):
    username = data.get("username")
    if not username:
        raise HTTPException(status_code=400, detail="username is required")
    
    participant = db.query(PlanParticipant).filter_by(plan_id=plan_id, username=username).first()
    if not participant:
        raise HTTPException(status_code=404, detail="해당 참가자를 찾을 수 없습니다")
    
    db.delete(participant)
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if plan and plan.participants > 0:
        plan.participants -= 1
    db.commit()
    return {"message": "삭제 성공"}

@router.get("/plans/{plan_id}/applied", tags=["Plans Actions"])
def check_applied_status(plan_id: int, request: Request, db: Session = Depends(get_db)):
    username = request.cookies.get("user")
    if not username:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    
    applied = db.query(PlanApplication).filter_by(plan_id=plan_id, username=username).first()
    return {"applied": bool(applied)}

@router.post("/suggest-locations", response_model=SuggestResponse, tags=["Gemini"])
async def suggest_locations(data: RecommendRequest):
    try:
        body = data.model_dump()
        travel_area = body.get("travelArea")
        if not travel_area:
            raise HTTPException(status_code=400, detail="여행 지역 정보가 누락되었습니다.")
        
        preferences = body.get("interests", []) + body.get("travelStyle", [])
        preferences_str = ", ".join(filter(None, set(preferences))) or "특별한 선호 없음"

        prompt = f"""
            **당신은 지정된 지역 내에서만 여행지를 추천하는 AI 여행 전문가입니다.**
            **가장 중요한 절대 규칙: 반드시 '{travel_area}' 지역 또는 대륙 내의 여행지만 추천해야 합니다.**
            사용자의 주요 여행 선호도는 다음과 같습니다:
            - 주요 관심사: {preferences_str}
            - 예산: {body.get("budget", "지정 안함")}
            위의 선호도를 바탕으로, **'{travel_area}' 내에서** 가장 매력적인 실제 도시나 국가 이름 3곳을 추천해주세요.
            다른 설명 없이 오직 JSON 형식으로만 응답하세요.
            반환 형식 예시: {{ "locations": ["추천 여행지 1", "추천 여행지 2", "추천 여행지 3"] }}
        """
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        text = response.text.strip()
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if not match:
            raise HTTPException(status_code=500, detail="JSON 형식의 지역 추천을 받는 데 실패했습니다.")
        return json.loads(match.group())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# plans.py의 recommend 함수를 아래 코드로 통째로 교체하세요.

@router.post("/recommend", tags=["Gemini"])
async def recommend(data: RecommendRequest):
    try:
        body = data.model_dump()
        
        # --- 1. 사용자 요청에서 핵심 정보 추출 ---

        # ✅ [수정됨] 'travelDuration' 문자열을 분석해 실제 여행 일수 계산
        trip_duration_days = 3 # 기본값
        duration_str = data.travelDuration
        
        if duration_str:
            # "n주일" 형태 처리 (예: "1주일", "2주일")
            week_match = re.search(r'(\d+)\s*주일', duration_str)
            if week_match:
                trip_duration_days = int(week_match.group(1)) * 7
            else:
                # "n일" 또는 "n박 m일" 형태 처리 (예: "4일", "3박 4일")
                # '일' 앞의 숫자를 우선적으로 사용합니다.
                day_match = re.search(r'(\d+)\s*일', duration_str)
                if day_match:
                    trip_duration_days = int(day_match.group(1))
        
        # (이하 로직은 거의 동일)
        activity_levels = {
            "여유롭게": "하루 3~4개",
            "적당히": "하루 5~6개",
            "부지런히": "하루 7개 이상"
        }
        seasons = ["봄", "여름", "가을", "겨울"]
        
        user_activity_level = "적당히"
        num_activities = activity_levels[user_activity_level]
        user_season = None
        other_interests = []
        
        for interest in body.get("interests", []):
            if interest in activity_levels:
                user_activity_level = interest
                num_activities = activity_levels[interest]
            elif interest in seasons:
                user_season = interest
            else:
                other_interests.append(interest)
        
        other_preferences_str = ", ".join(other_interests) if other_interests else "특별한 선호 없음"

        # --- 2. AI에게 보낼 프롬프트 (이전과 동일, trip_duration_days 변수만 사용) ---
        
        prompt = f"""
            **당신은 실제 지도 앱(구글맵, 네이버맵)으로 검증이 가능한, 매우 꼼꼼한 AI 여행 전문가입니다.**
            **당신의 최우선 임무는 '거짓 없는' 현실적인 여행 계획을 생성하는 것입니다.**

            **[절대 규칙]**
            1.  **실존하는 장소만 추천**: 모든 식당, 카페, 관광지 이름은 반드시 실제 운영 중이고 검색 가능한 곳이어야 합니다. 절대 장소 이름을 지어내지 마세요.
            2.  **교차 검증**: 생성하는 모든 정보는 여러 소스를 통해 교차 검증되었다고 가정하고 가장 확실한 정보만 제공하세요.
            3.  **언어**: 모든 장소의 이름은 반드시 **'한국어'**로 표기하세요. (예: 'Starbucks' -> '스타벅스', 'Eiffel Tower' -> '에펠탑')
            
            **[사용자 맞춤 조건]**
            1.  **여행지**: '{data.selectedLocation}'
            2.  **여행 기간**: 총 **'{trip_duration_days}일'** 동안의 계획을 생성하세요. 날짜 수를 반드시 맞춰야 합니다.
            3.  **계절**: **'{user_season}'**
                - 이 계절에만 즐길 수 있거나, 이 계절에 가장 매력적인 활동과 장소를 반드시 포함하세요. (예: 여름엔 해수욕장, 가을엔 단풍 명소)
            4.  **활동량**: 사용자는 **'{user_activity_level}'** 스타일을 원합니다.
                - 하루 활동 갯수를 반드시 **'{num_activities}'** 범위에 맞춰서 계획을 짜주세요. 이것은 매우 중요한 요구사항입니다.
            5.  **기타 관심사**: {other_preferences_str}

            **[출력 형식]**
            - 위의 모든 규칙과 조건을 완벽하게 반영하여, 아래와 동일한 JSON 구조로만 응답하세요.
            - 다른 설명이나 대답 없이 오직 JSON 데이터만 반환해야 합니다.
            - 예시: {{ "recommendations": ["{data.selectedLocation}"], "itinerary": {{ "YYYY-MM-DD": [{{ "time": "HH:MM ~ HH:MM", "activity": "..." }}] }} }}
        """

        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if not match:
            print("Gemini 응답 (JSON 아님):", text)
            raise HTTPException(status_code=500, detail=f"Gemini 응답에서 JSON 추출 실패. 응답 내용: {text}")
            
        return json.loads(match.group())
        
    except Exception as e:
        print(f"Error in /recommend: {e}")
        raise HTTPException(status_code=500, detail=f"Gemini 호출 실패: {str(e)}")

@router.post("/ask-plan", tags=["Gemini"])
async def ask_about_plan(payload: dict = Body(...)):
    question = payload.get("question")
    plan = payload.get("plan")
    if not question or not plan:
        raise HTTPException(status_code=400, detail="질문 또는 계획 정보가 없습니다.")

    prompt = f"""
    사용자가 아래 여행 계획을 참고하여 질문을 했습니다.
    여행 계획: {json.dumps(plan, ensure_ascii=False, indent=2)}
    사용자 질문: {question}
    위 정보를 바탕으로 친절하고 간결하게 답변해주세요.
    """
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        return {"answer": response.text.strip()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini 호출 실패: {str(e)}")