"""
pytest 설정 및 공통 fixture

테스트용 Flask app, client, mock data 제공
"""

import pytest
from app import create_app


@pytest.fixture
def app():
    """테스트용 Flask 애플리케이션"""
    app = create_app()
    app.config.update({
        'TESTING': True,
        'API_KEY': 'test-api-key-12345',
        'REDIS_URL': None  # Redis 캐싱 비활성화 (단위 테스트용)
    })
    yield app


@pytest.fixture
def client(app):
    """테스트용 Flask 클라이언트"""
    return app.test_client()


@pytest.fixture
def auth_headers():
    """인증 헤더"""
    return {'X-API-KEY': 'test-api-key-12345'}


@pytest.fixture
def sample_patient_data():
    """시뮬레이션 테스트용 환자 데이터"""
    return {
        'age_group': 12,
        'gender': 1,
        'height': 170,
        'weight': 85,
        'systolic_bp': 152,
        'diastolic_bp': 96,
        'fasting_glucose': 131,
        'total_cholesterol': 255,
        'triglycerides': 210,
        'hdl_cholesterol': 38,
        'smoking_status': 'current'
    }


@pytest.fixture
def healthy_patient_data():
    """정상 환자 데이터"""
    return {
        'age_group': 10,
        'gender': 2,
        'height': 165,
        'weight': 60,
        'systolic_bp': 110,
        'diastolic_bp': 70,
        'fasting_glucose': 90,
        'total_cholesterol': 180,
        'triglycerides': 120,
        'hdl_cholesterol': 55,
        'smoking_status': 'never'
    }
