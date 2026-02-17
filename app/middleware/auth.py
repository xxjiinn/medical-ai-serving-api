"""
API Key 인증 미들웨어

X-API-KEY 헤더 검증
"""

from functools import wraps
from flask import request, jsonify, current_app


def require_api_key(f):
    """
    API Key 검증 데코레이터

    Usage:
        @app.route('/protected')
        @require_api_key
        def protected_route():
            return {'data': 'secret'}
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # API Key 추출
        api_key = request.headers.get('X-API-KEY')

        # 검증
        expected_key = current_app.config.get('API_KEY')

        if not api_key:
            return jsonify({
                'error': 'Unauthorized',
                'message': 'API key is missing. Include X-API-KEY header.'
            }), 401

        if api_key != expected_key:
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Invalid API key'
            }), 401

        # 검증 통과
        return f(*args, **kwargs)

    return decorated_function
