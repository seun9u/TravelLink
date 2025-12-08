## 🛠️ Tech Stack

| Category | Technology |
| --- | --- |
| **Frontend** | React, CSS3, Axios |
| **Backend** | Python, FastAPI, SQLAlchemy, Pydantic |
| **Database** | MySQL (AWS RDS) |
| **Infra & DevOps** | AWS (EC2, S3, RDS), Nginx, Gunicorn, Git/GitHub |
| **AI / API** | Google Gemini API |

---

## 💡 Key Features

* **🤖 AI 맞춤 여행 코스 생성**
    * 여행지, 기간, 예산, 취향(액티비티, 휴식 등)을 분석하여 최적의 경로와 일정을 자동 생성.
* **🔐 보안 강화된 인증 시스템**
    * 세션/쿠키 기반의 로그인 유지 및 관리자(Admin) 권한 분리.
* **🤝 동행 매칭 시스템**
    * 타 사용자의 여행 타임라인을 상세 조회하고, 동행 참여를 신청/수락하는 매칭 프로세스 구현.
* **🛡️ 관리자 대시보드**
    * 전체 회원 관리 및 1:1 문의사항(Q&A)에 대한 관리자 답변 처리 시스템.

---

## 🚀 Trouble Shooting & Experience (Core)

프로젝트를 진행하며 겪은 주요 기술적 이슈와 해결 과정입니다.

### 1. CORS 정책 위반 및 쿠키 공유 문제
* **문제:** 프론트엔드(S3)와 백엔드(EC2)의 도메인이 달라 브라우저 보안 정책(SameSite)에 의해 쿠키가 차단되어 로그인이 풀리는 현상.
* **해결:**
    1.  FastAPI 미들웨어에 S3 도메인을 `allow_origins`로 명시.
    2.  쿠키 설정 시 `samesite='Lax'`, `secure=False` (http 환경 고려) 옵션 적용하여 통신 안정성 확보.

### 2. Gunicorn Worker Timeout 및 메모리 최적화
* **문제:** AI 응답 생성 시간이 길어질 경우 Gunicorn이 Worker를 강제 종료(SIGKILL)하거나, EC2 프리티어(RAM 1GB) 메모리 부족 발생.
* **해결:**
    1.  Gunicorn 실행 옵션에 `--timeout 120`을 추가하여 AI 응답 대기 시간 확보.
    2.  리눅스 `Swap Memory` (1GB)를 설정하여 물리 메모리 한계 극복.

### 3. Nginx 405 Method Not Allowed
* **문제:** 배포 후 로그인(POST) 요청 시 Nginx에서 405 오류 반환.
* **해결:** 정적 파일 경로와 API 프록시 경로(`/api`)를 `nginx.conf`에서 명확히 분리하고, 프론트엔드 환경변수(`REACT_APP_API_URL`)가 Nginx 포트(80)를 경유하도록 수정.

---

## 💾 Database Design (ERD)
데이터 무결성을 위해 정규화된 관계형 데이터베이스를 설계했습니다.
* **User - Plan:** 1:N 관계 (한 명의 유저는 여러 여행 계획 생성 가능)
* **User - Comment:** 1:N 관계
* **Plan - DetailSchedule:** 1:N 관계 (하나의 계획은 시간대별 상세 일정을 포함)

---

## 💻 How to Run (Local)

**1. Backend**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # (Windows: venv\Scripts\activate)
pip install -r requirements.txt
uvicorn main:app --reload

**2. Frontend**
cd frontend
npm install
npm start

## 👤 Author
강승구 (Seunggu Kang)
Github: https://github.com/seun9u
Email: gugusg@naver.com
