"""
API 엔드포인트 테스트

GET /health, /records, /stats, POST /simulate
"""

import pytest


class TestHealthEndpoint:
    """Health check 엔드포인트 테스트"""

    def test_health_check(self, client):
        """GET /health - 서버 상태 확인"""
        response = client.get('/health')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'ok'


class TestAuthMiddleware:
    """API 인증 미들웨어 테스트"""

    def test_missing_api_key(self, client):
        """API Key 없이 요청 시 401 에러"""
        response = client.get('/records')
        assert response.status_code == 401
        data = response.get_json()
        assert 'error' in data
        assert data['error'] == 'Unauthorized'

    def test_invalid_api_key(self, client):
        """잘못된 API Key 사용 시 401 에러"""
        headers = {'X-API-KEY': 'wrong-key'}
        response = client.get('/records', headers=headers)
        assert response.status_code == 401

    def test_valid_api_key(self, client, auth_headers):
        """올바른 API Key 사용 시 정상 응답"""
        response = client.get('/records', headers=auth_headers)
        assert response.status_code == 200


class TestRecordsEndpoint:
    """Records 엔드포인트 테스트"""

    def test_get_records_pagination(self, client, auth_headers):
        """GET /records - 페이징 응답 구조 확인"""
        response = client.get('/records?page=1&limit=5', headers=auth_headers)
        assert response.status_code == 200

        data = response.get_json()
        assert 'data' in data
        assert 'pagination' in data
        assert isinstance(data['data'], list)

        pagination = data['pagination']
        assert 'page' in pagination
        assert 'limit' in pagination
        assert 'total_items' in pagination
        assert 'total_pages' in pagination
        assert pagination['page'] == 1
        assert pagination['limit'] == 5

    def test_get_records_invalid_page(self, client, auth_headers):
        """GET /records - 잘못된 page 파라미터"""
        response = client.get('/records?page=0', headers=auth_headers)
        assert response.status_code == 400

    def test_get_records_invalid_limit(self, client, auth_headers):
        """GET /records - 잘못된 limit 파라미터"""
        response = client.get('/records?limit=200', headers=auth_headers)
        assert response.status_code == 400


class TestStatsEndpoint:
    """Stats 엔드포인트 테스트"""

    def test_get_risk_stats(self, client, auth_headers):
        """GET /stats/risk - 위험군 통계"""
        response = client.get('/stats/risk', headers=auth_headers)
        assert response.status_code == 200

        data = response.get_json()
        assert 'risk_distribution' in data
        assert 'total_records' in data
        assert 'valid_records' in data
        assert 'invalid_records' in data

        # 위험군 키 확인
        risk_dist = data['risk_distribution']
        assert isinstance(risk_dist, dict)

    def test_get_age_stats(self, client, auth_headers):
        """GET /stats/age - 연령대 통계"""
        response = client.get('/stats/age', headers=auth_headers)
        assert response.status_code == 200

        data = response.get_json()
        assert 'age_distribution' in data
        assert 'total_records' in data
        assert isinstance(data['age_distribution'], list)

        # 연령대 항목 구조 확인
        if data['age_distribution']:
            item = data['age_distribution'][0]
            assert 'age_group' in item
            assert 'count' in item
            assert 'percentage' in item
            assert 'avg_risk_factor_count' in item
            assert 'high_risk_count' in item


class TestSimulateEndpoint:
    """Simulate 엔드포인트 테스트"""

    def test_simulate_high_risk_patient(self, client, auth_headers, sample_patient_data):
        """POST /simulate - 고위험 환자"""
        response = client.post(
            '/simulate',
            json=sample_patient_data,
            headers=auth_headers
        )
        assert response.status_code == 200

        data = response.get_json()
        assert 'input' in data
        assert 'result' in data
        assert 'disclaimer' in data

        result = data['result']
        assert 'risk_factor_count' in result
        assert 'risk_group' in result
        assert 'flags' in result
        assert 'explanations' in result

        # 고위험 환자는 7개 위험요인 예상
        assert result['risk_factor_count'] == 7
        assert result['risk_group'] == 'CHD_RISK_EQUIVALENT'

        # 모든 플래그 True 확인
        flags = result['flags']
        assert flags['hypertension'] == True
        assert flags['diabetes'] == True
        assert flags['smoking'] == True

    def test_simulate_healthy_patient(self, client, auth_headers, healthy_patient_data):
        """POST /simulate - 정상 환자"""
        response = client.post(
            '/simulate',
            json=healthy_patient_data,
            headers=auth_headers
        )
        assert response.status_code == 200

        data = response.get_json()
        result = data['result']

        # 정상 환자는 위험요인 0~1개 예상
        assert result['risk_factor_count'] <= 1
        assert result['risk_group'] == 'ZERO_TO_ONE_RISK_FACTOR'

    def test_simulate_missing_fields(self, client, auth_headers):
        """POST /simulate - 필수 필드 누락"""
        incomplete_data = {'age_group': 12, 'gender': 1}
        response = client.post(
            '/simulate',
            json=incomplete_data,
            headers=auth_headers
        )
        assert response.status_code == 400

        data = response.get_json()
        assert 'error' in data
        assert data['error'] == 'Validation Error'

    def test_simulate_invalid_range(self, client, auth_headers):
        """POST /simulate - 범위 초과 값"""
        invalid_data = {
            'age_group': 25,  # 9~18만 허용
            'gender': 1,
            'height': 170,
            'weight': 80,
            'systolic_bp': 120,
            'diastolic_bp': 80,
            'fasting_glucose': 100,
            'total_cholesterol': 200,
            'triglycerides': 150,
            'hdl_cholesterol': 50,
            'smoking_status': 'never'
        }
        response = client.post(
            '/simulate',
            json=invalid_data,
            headers=auth_headers
        )
        assert response.status_code == 400

    def test_simulate_invalid_smoking_status(self, client, auth_headers, sample_patient_data):
        """POST /simulate - 잘못된 smoking_status"""
        sample_patient_data['smoking_status'] = 'sometimes'
        response = client.post(
            '/simulate',
            json=sample_patient_data,
            headers=auth_headers
        )
        assert response.status_code == 400
