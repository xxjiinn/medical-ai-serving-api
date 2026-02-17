"""
Redis 캐싱 유틸리티

Stats API 응답 캐싱 (TTL 60초)
"""

import json
import redis
from decimal import Decimal
from functools import wraps
from flask import current_app, jsonify


class DecimalEncoder(json.JSONEncoder):
    """Decimal 타입을 JSON으로 변환하는 인코더"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


# Redis 클라이언트 (전역)
_redis_client = None


def get_redis_client():
    """
    Redis 클라이언트 싱글톤 반환

    Returns:
        redis.Redis: Redis 클라이언트 또는 None
    """
    global _redis_client

    if _redis_client is None:
        redis_url = current_app.config.get('REDIS_URL')
        if not redis_url:
            return None

        try:
            _redis_client = redis.from_url(
                redis_url,
                decode_responses=True,  # 자동 UTF-8 디코딩
                socket_connect_timeout=2,
                socket_timeout=2
            )
            # 연결 테스트
            _redis_client.ping()
        except Exception as e:
            current_app.logger.warning(f"Redis connection failed: {e}")
            _redis_client = None

    return _redis_client


def cached(ttl=60):
    """
    응답 캐싱 데코레이터

    Args:
        ttl (int): Time-to-live (초)

    Usage:
        @cached(ttl=60)
        def my_endpoint():
            return jsonify({...})
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            client = get_redis_client()

            # Redis 미사용 시 원본 함수 실행
            if client is None:
                return f(*args, **kwargs)

            # 캐시 키 생성 (함수명 + 파라미터)
            cache_key = f"cache:{f.__name__}:{str(args)}:{str(kwargs)}"

            try:
                # 캐시 조회
                cached_data = client.get(cache_key)
                if cached_data:
                    # 캐시 히트
                    data = json.loads(cached_data)
                    data['cached'] = True
                    return jsonify(data)

                # 캐시 미스 - 원본 함수 실행
                response = f(*args, **kwargs)

                # dict 반환 시 직접 처리
                if isinstance(response, dict):
                    data = response
                    data['cached'] = False

                    # Redis에 저장
                    client.setex(
                        cache_key,
                        ttl,
                        json.dumps(data, cls=DecimalEncoder)
                    )

                    return jsonify(data)

                # Flask Response 객체인 경우
                if hasattr(response, 'is_json') and response.is_json:
                    data = response.get_json()
                    data['cached'] = False

                    # Redis에 저장
                    client.setex(
                        cache_key,
                        ttl,
                        json.dumps(data, cls=DecimalEncoder)
                    )

                    return jsonify(data)

                return response

            except Exception as e:
                current_app.logger.warning(f"Cache error: {e}")
                # 에러 시 원본 함수 실행
                return f(*args, **kwargs)

        return decorated_function
    return decorator


def clear_cache_pattern(pattern):
    """
    패턴에 매칭되는 캐시 삭제

    Args:
        pattern (str): Redis key 패턴 (예: 'cache:get_risk_stats:*')

    Returns:
        int: 삭제된 키 개수
    """
    client = get_redis_client()
    if client is None:
        return 0

    try:
        keys = client.keys(pattern)
        if keys:
            return client.delete(*keys)
        return 0
    except Exception as e:
        current_app.logger.warning(f"Cache clear error: {e}")
        return 0
