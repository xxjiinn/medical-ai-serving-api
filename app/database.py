"""
데이터베이스 연결 관리

SQLAlchemy Engine, Session 생성
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from app.config import get_config

# 설정 로드
config = get_config()

# Engine 생성 (DB 연결 풀)
engine = create_engine(
    config.SQLALCHEMY_DATABASE_URI,
    echo=config.SQLALCHEMY_ECHO,  # SQL 로그 (개발 환경에서만)
    pool_pre_ping=True,  # 연결 유효성 체크
    pool_recycle=3600,  # 1시간마다 연결 재생성
)

# Session Factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Thread-safe Session
session = scoped_session(SessionLocal)


def get_db():
    """
    DB 세션 생성 (Flask 요청마다 사용)

    Usage:
        db = get_db()
        try:
            # DB 작업
        finally:
            db.close()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    테이블 생성

    models의 Base.metadata를 사용하여 모든 테이블 생성
    """
    from app.models.health_check import Base
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")


def drop_db():
    """
    모든 테이블 삭제 (주의!)

    개발 중에만 사용
    """
    from app.models.health_check import Base
    Base.metadata.drop_all(bind=engine)
    print("⚠️  All database tables dropped")
