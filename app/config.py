"""
애플리케이션 설정

환경변수를 읽어서 DB, Redis 연결 정보 제공
"""

import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()


class Config:
    """기본 설정"""

    # Database
    DATABASE_URL = os.getenv('DATABASE_URL')
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable is required")

    # Redis
    REDIS_URL = os.getenv('REDIS_URL')

    # API Key
    API_KEY = os.getenv('API_KEY', 'default-secret-key-change-me')

    # Flask
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = FLASK_ENV == 'development'

    # SQLAlchemy
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # 성능 개선 (보통 꺼두는 설정)
    SQLALCHEMY_ECHO = DEBUG  # 개발 환경에서만 SQL 로그 출력

    # ETL
    ETL_CHUNK_SIZE = int(os.getenv('ETL_CHUNK_SIZE', 10000))  # pandas chunk 크기


class DevelopmentConfig(Config):
    """개발 환경 설정"""
    DEBUG = True


class ProductionConfig(Config):
    """배포 환경 설정"""
    DEBUG = False
    SQLALCHEMY_ECHO = False


# 환경에 따라 설정 선택
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}


def get_config():
    """현재 환경의 설정 반환"""
    env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, config['default'])
