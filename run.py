"""
Flask 애플리케이션 실행

Usage:
    python run.py
"""

import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    # Railway나 다른 플랫폼이 PORT 환경변수를 제공할 수 있음
    port = int(os.getenv('PORT', 5001))
    debug = os.getenv('FLASK_ENV', 'development') == 'development'

    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
