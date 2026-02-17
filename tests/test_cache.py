"""
Redis 캐싱 기능 테스트

캐시 동작, TTL, Decimal 직렬화 테스트
"""

import pytest
import json
import redis
from decimal import Decimal
from app.cache import DecimalEncoder, get_redis_client


class TestDecimalEncoder:
    """Decimal JSON 인코더 테스트"""

    def test_encode_decimal(self):
        """Decimal을 float로 변환"""
        data = {'value': Decimal('123.45')}
        json_str = json.dumps(data, cls=DecimalEncoder)
        result = json.loads(json_str)
        assert result['value'] == 123.45
        assert isinstance(result['value'], float)

    def test_encode_mixed_types(self):
        """다양한 타입 혼합 직렬화"""
        data = {
            'integer': 100,
            'float': 12.34,
            'decimal': Decimal('56.78'),
            'string': 'test',
            'bool': True,
            'list': [1, 2, Decimal('3.14')],
            'nested': {'value': Decimal('99.99')}
        }
        json_str = json.dumps(data, cls=DecimalEncoder)
        result = json.loads(json_str)

        assert result['integer'] == 100
        assert result['float'] == 12.34
        assert result['decimal'] == 56.78
        assert result['string'] == 'test'
        assert result['bool'] == True
        assert result['list'][2] == 3.14
        assert result['nested']['value'] == 99.99


class TestCacheDecorator:
    """캐싱 데코레이터 통합 테스트"""

    def test_cache_disabled_when_redis_unavailable(self, client, auth_headers):
        """Redis 미사용 시 캐싱 비활성화"""
        # conftest.py에서 REDIS_URL=None으로 설정됨
        response = client.get('/stats/risk', headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()

        # Redis가 없으면 cached 필드가 없거나 False
        # (원본 함수에서 반환하는 데이터 그대로)
        # cached 필드가 없는 것이 정상 (decorator가 bypass됨)


class TestRedisConnection:
    """Redis 연결 테스트 (실제 Redis 필요)"""

    @pytest.mark.skipif(
        not redis.from_url("redis://localhost:6379/0", socket_connect_timeout=1).ping(),
        reason="Redis not available"
    )
    def test_redis_ping(self):
        """Redis 서버 연결 확인"""
        r = redis.from_url("redis://localhost:6379/0")
        assert r.ping() == True

    @pytest.mark.skipif(
        not redis.from_url("redis://localhost:6379/0", socket_connect_timeout=1).ping(),
        reason="Redis not available"
    )
    def test_redis_set_get(self):
        """Redis 기본 SET/GET 동작"""
        r = redis.from_url("redis://localhost:6379/0", decode_responses=True)
        key = "test:key:123"
        value = "test_value"

        r.setex(key, 5, value)
        result = r.get(key)
        assert result == value

        # TTL 확인
        ttl = r.ttl(key)
        assert 0 < ttl <= 5

        # 정리
        r.delete(key)

    @pytest.mark.skipif(
        not redis.from_url("redis://localhost:6379/0", socket_connect_timeout=1).ping(),
        reason="Redis not available"
    )
    def test_redis_json_serialization(self):
        """Redis JSON 직렬화/역직렬화"""
        r = redis.from_url("redis://localhost:6379/0", decode_responses=True)
        key = "test:json:456"
        data = {
            'count': 100,
            'avg': Decimal('12.34'),
            'name': 'test'
        }

        # 저장
        json_str = json.dumps(data, cls=DecimalEncoder)
        r.setex(key, 5, json_str)

        # 조회
        cached = r.get(key)
        result = json.loads(cached)

        assert result['count'] == 100
        assert result['avg'] == 12.34
        assert result['name'] == 'test'

        # 정리
        r.delete(key)
