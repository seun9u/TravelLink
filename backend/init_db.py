from sqlalchemy import text
from db import engine, Base, UserModel  # Base 꼭 임포트해야 함

# 1. 외래키 제약 해제
with engine.connect() as conn:
    conn.execute(text("SET FOREIGN_KEY_CHECKS=0;"))

# 2. 모든 테이블 삭제
Base.metadata.drop_all(bind=engine)

# 3. 외래키 제약 다시 활성화
with engine.connect() as conn:
    conn.execute(text("SET FOREIGN_KEY_CHECKS=1;"))

# 4. 테이블 재생성
Base.metadata.create_all(bind=engine)

print("✅ users 테이블 재생성 완료")
