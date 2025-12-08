# main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import os
import dotenv
import google.generativeai as genai

# --- 데이터베이스 및 모델 초기화 ---
# 🚨 이 파일에 MySQL 연결 설정과 Base 객체가 정의되어 있어야 합니다.
from database import engine, Base

# --- 라우터 임포트 ---
from signup import router as signup_router
from log import router as log_router
from contact import router as contact_router
from menu import router as menu_router
from forgot_password import router as forgot_password_router
from plans import router as plans_router 
from admin import router as admin_router
from find_username_router import router as find_username_router # 💡 아이디 찾기 라우터 임포트

# --- 앱 설정 ---
dotenv.load_dotenv()
app = FastAPI()

# --- 미들웨어 설정 ---
origins = [
    "http://localhost:3000",
    "http://sgu-tl-2-travellink-s3.s3-website.ap-northeast-3.amazonaws.com"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET_KEY")
)

# --- 외부 서비스 설정 ---
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# --- DB 테이블 생성 ---
# 애플리케이션 시작 시 models.py에 정의된 모든 테이블을 생성합니다.
Base.metadata.create_all(bind=engine)

# --- 라우터 포함 ---
app.include_router(signup_router, tags=["Authentication"])
app.include_router(log_router, tags=["Authentication"])
app.include_router(forgot_password_router, tags=["Authentication"])
app.include_router(contact_router, tags=["Contact"])
app.include_router(menu_router, tags=["Menu"])
app.include_router(plans_router) 
app.include_router(admin_router, tags=["Admin"])
app.include_router(find_username_router) # 💡 아이디 찾기 라우터 포함

# --- 루트 엔드포인트 ---
@app.get("/")
def root():
    return {"message": "Travel Link API Server is running"}