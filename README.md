# ✈️ Travel Link (AI Based Travel Planner)

![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-00000F?style=for-the-badge&logo=mysql&logoColor=white)
![AWS](https://img.shields.io/badge/AWS-%23FF9900.svg?style=for-the-badge&logo=amazon-aws&logoColor=white)

> **"복잡한 여행 계획은 AI에게, 당신은 여행에만 집중하세요."** > Google Gemini AI를 활용하여 개인 취향에 맞는 맞춤형 여행 코스를 생성하고, 동행을 구할 수 있는 여행 플랫폼입니다.

---

## 🔗 배포 링크
👉 **Service URL:** ([[https://seun9u.github.io/TravelLink](http://sgu-tl-2-travellink-s3.s3-website.ap-northeast-3.amazonaws.com/)](http://sgu-tl-2-travellink-s3.s3-website.ap-northeast-3.amazonaws.com/))  
*(AWS 비용 문제로 서버가 닫혀있을 수 있습니다.)*

---

## 🏗️ System Architecture & Service Flow

### 1. Cloud Infrastructure
안정적인 서비스 운영을 위해 **AWS 클라우드 환경**을 구축했습니다.
* **Frontend:** AWS S3 (Static Hosting)
* **Backend:** AWS EC2 (Ubuntu) + Nginx (Reverse Proxy) + Gunicorn
* **Database:** AWS RDS (MySQL)

### 2. AI Service Pipeline
사용자의 요청을 단순 저장하는 것이 아니라, AI를 통해 가공하여 DB에 적재하는 프로세스를 구현했습니다.

```mermaid
graph LR
    A[Client (설문 제출)] --> B(FastAPI Server)
    B -->|프롬프트 최적화| C{Google Gemini API}
    C -->|JSON 데이터 반환| B
    B -->|데이터 파싱 및 검증| D[(MySQL DB)]
    D --> B
    B --> A[Client (결과 반환)]
