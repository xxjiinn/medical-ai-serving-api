"""
Flask 애플리케이션 팩토리

Blueprint 등록, 확장 초기화
"""

from flask import Flask
from flask_cors import CORS
from app.config import get_config


def create_app():
    """Flask 애플리케이션 생성"""
    app = Flask(__name__)

    # 설정 로드
    config = get_config()
    app.config.from_object(config)

    # CORS 설정 (개발 환경)
    CORS(app)

    # Blueprint 등록
    from app.blueprints.records import records_bp
    from app.blueprints.stats import stats_bp
    from app.blueprints.simulate import simulate_bp

    app.register_blueprint(records_bp, url_prefix='/records')
    app.register_blueprint(stats_bp, url_prefix='/stats')
    app.register_blueprint(simulate_bp)

    # Health check
    @app.route('/')
    def index():
        return {
            'service': 'Medical AI Risk Factor Profiling API',
            'version': 'guideline-v1',
            'status': 'healthy'
        }

    @app.route('/health')
    def health():
        return {'status': 'ok'}

    return app
