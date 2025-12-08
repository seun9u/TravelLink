from sqlalchemy import Column, Integer, String, Date, Text, JSON, TIMESTAMP, ForeignKey, func
from database import Base

class UserModel(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    contact_type = Column(String(20), nullable=True)
    contact_value = Column(String(100), nullable=True)
    is_admin = Column(Integer, default=0)

# Plan, PlanApplication 등 다른 모든 모델들도 여기에 함께 정의합니다.
class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    username = Column(String(100))
    destination = Column(String(100))
    date = Column(String(100))
    summary = Column(Text)
    participants = Column(Integer, default=1)
    capacity = Column(Integer, default=4)
    views = Column(Integer, default=0)
    tags = Column(Text)
    itinerary = Column(JSON)
    created_at = Column(TIMESTAMP, server_default=func.now())

# PlanApplication, PlanParticipant 모델도 이 아래에 추가하면 됩니다.

# models.py 파일 하단에 추가
from sqlalchemy import Text

class Contact(Base):
    __tablename__ = "contact"

    id = Column(String(255), primary_key=True, index=True)
    name = Column(String(255))
    title = Column(String(255))
    message = Column(Text)
    answer = Column(Text, nullable=True) # 답변은 없을 수도 있으므로 nullable=True


# 계획 참여 신청 테이블 모델
class PlanApplication(Base):
    __tablename__ = "plan_applications"
    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("plans.id"))
    username = Column(String(255), index=True)
    reason = Column(Text)
    travel_style = Column(String(255))
    contact_type = Column(String(255))
    contact_value = Column(String(255))

# 계획 확정 참가자 테이블 모델
class PlanParticipant(Base):
    __tablename__ = "plan_participants"
    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("plans.id"))
    username = Column(String(255), index=True)
    contact_type = Column(String(255))
    contact_value = Column(String(255))
    travel_style = Column(String(255))