"""
Stats Blueprint

통계 API (캐싱 대상)
"""

from flask import Blueprint, jsonify
from sqlalchemy import func, case
from app.middleware.auth import require_api_key
from app.database import SessionLocal
from app.models.health_check import RawHealthCheck, CleanRiskResult
from app.cache import cached

stats_bp = Blueprint('stats', __name__)


@stats_bp.route('/risk', methods=['GET'])
@require_api_key
@cached(ttl=60)
def get_risk_stats():
    """
    GET /stats/risk

    위험군별 분포 통계
    """
    db = SessionLocal()

    try:
        # 위험군별 집계 (모든 레코드가 유효함)
        query = db.query(
            CleanRiskResult.risk_group,
            func.count(CleanRiskResult.id).label('count')
        ).group_by(
            CleanRiskResult.risk_group
        ).all()

        # 총 개수 (clean 테이블의 모든 레코드)
        valid_count = sum(row.count for row in query)

        # Raw 테이블 총 레코드 (원본 데이터)
        total_raw = db.query(func.count(RawHealthCheck.id)).scalar()

        # 응답 생성
        risk_distribution = {}
        for row in query:
            risk_distribution[row.risk_group] = {
                'count': row.count,
                'percentage': round(row.count / valid_count * 100, 1) if valid_count > 0 else 0
            }

        return {
            'risk_distribution': risk_distribution,
            'total_records': total_raw,  # Raw 테이블 원본
            'valid_records': valid_count,  # Clean 테이블 (유효한 레코드만)
            'invalid_records': total_raw - valid_count  # 차이
        }

    finally:
        db.close()


@stats_bp.route('/age', methods=['GET'])
@require_api_key
@cached(ttl=60)
def get_age_stats():
    """
    GET /stats/age

    연령대별 통계
    """
    db = SessionLocal()

    try:
        # 연령대별 집계 (모든 레코드가 유효함)
        query = db.query(
            RawHealthCheck.age_group_code,
            func.count(CleanRiskResult.id).label('count'),
            func.avg(CleanRiskResult.risk_factor_count).label('avg_risk_count'),
            func.sum(
                case((CleanRiskResult.risk_group == 'CHD_RISK_EQUIVALENT', 1), else_=0)
            ).label('high_risk_count')
        ).join(
            CleanRiskResult, RawHealthCheck.id == CleanRiskResult.raw_id
        ).group_by(
            RawHealthCheck.age_group_code
        ).order_by(
            RawHealthCheck.age_group_code
        ).all()

        # 총 개수
        total = sum(row.count for row in query)

        # 응답 생성
        age_distribution = []
        for row in query:
            age_distribution.append({
                'age_group': row.age_group_code,
                'age_display': f'{row.age_group_code * 5}세',
                'count': row.count,
                'percentage': round(row.count / total * 100, 1) if total > 0 else 0,
                'avg_risk_factor_count': round(row.avg_risk_count, 1) if row.avg_risk_count else 0,
                'high_risk_count': row.high_risk_count or 0
            })

        return {
            'age_distribution': age_distribution,
            'total_records': total
        }

    finally:
        db.close()
