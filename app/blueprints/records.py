"""
Records Blueprint

검진 데이터 조회 API
"""

from flask import Blueprint, request, jsonify
from app.middleware.auth import require_api_key
from app.database import SessionLocal
from app.models.health_check import RawHealthCheck, CleanRiskResult

records_bp = Blueprint('records', __name__)


@records_bp.route('', methods=['GET'])
@require_api_key
def get_records():
    """
    GET /records

    Query Parameters:
        - page: 페이지 번호 (default: 1)
        - limit: 페이지당 항목 수 (default: 20, max: 100)
        - age_group: 연령대 필터 (9~18)
        - risk_group: 위험군 필터
    """
    # 파라미터
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)
    age_group = request.args.get('age_group', type=int)
    risk_group = request.args.get('risk_group', type=str)

    # 검증
    if page < 1:
        return jsonify({'error': 'Bad Request', 'message': 'page must be >= 1'}), 400
    if limit < 1 or limit > 100:
        return jsonify({'error': 'Bad Request', 'message': 'limit must be 1-100'}), 400

    db = SessionLocal()

    try:
        # 쿼리 빌드
        query = db.query(CleanRiskResult).join(RawHealthCheck).filter(
            CleanRiskResult.invalid_flag == False
        )

        # 필터 적용
        if age_group:
            query = query.filter(RawHealthCheck.age_group_code == age_group)
        if risk_group:
            query = query.filter(CleanRiskResult.risk_group == risk_group)

        # 총 개수
        total_items = query.count()

        # 페이징
        offset = (page - 1) * limit
        items = query.order_by(CleanRiskResult.id).offset(offset).limit(limit).all()

        # 응답 생성
        data = []
        for clean in items:
            raw = clean.raw_record
            data.append({
                'id': clean.id,
                'age_group': raw.age_group_code,
                'gender': raw.gender_code,
                'bmi': float(clean.bmi) if clean.bmi else None,
                'risk_factor_count': clean.risk_factor_count,
                'risk_group': clean.risk_group,
                'flags': {
                    'hypertension': clean.flag_hypertension,
                    'diabetes': clean.flag_diabetes,
                    'high_tc': clean.flag_tc_high,
                    'high_tg': clean.flag_tg_high,
                    'low_hdl': clean.flag_hdl_low,
                    'obesity': clean.flag_obesity,
                    'smoking': clean.flag_smoking
                },
                'created_at': clean.created_at.isoformat()
            })

        return jsonify({
            'data': data,
            'pagination': {
                'page': page,
                'limit': limit,
                'total_items': total_items,
                'total_pages': (total_items + limit - 1) // limit
            }
        })

    finally:
        db.close()


@records_bp.route('/<int:record_id>', methods=['GET'])
@require_api_key
def get_record(record_id):
    """
    GET /records/{id}

    단일 레코드 조회
    """
    db = SessionLocal()

    try:
        clean = db.query(CleanRiskResult).filter_by(id=record_id).first()

        if not clean:
            return jsonify({
                'error': 'Not Found',
                'message': f'Record with id {record_id} not found'
            }), 404

        raw = clean.raw_record

        # 응답
        return jsonify({
            'id': clean.id,
            'age_group': raw.age_group_code,
            'age_display': f'{(raw.age_group_code * 5)}세',
            'gender': raw.gender_code,
            'gender_display': '남성' if raw.gender_code == 1 else '여성',
            'height': raw.height,
            'weight': raw.weight,
            'bmi': float(clean.bmi) if clean.bmi else None,
            'systolic_bp': raw.systolic_bp,
            'diastolic_bp': raw.diastolic_bp,
            'fasting_glucose': raw.fasting_glucose,
            'total_cholesterol': raw.total_cholesterol,
            'triglycerides': raw.triglycerides,
            'hdl_cholesterol': raw.hdl_cholesterol,
            'smoking_status': {1: 'never', 2: 'former', 3: 'current'}.get(raw.smoking_status),
            'risk_factor_count': clean.risk_factor_count,
            'risk_group': clean.risk_group,
            'flags': {
                'hypertension': clean.flag_hypertension,
                'diabetes': clean.flag_diabetes,
                'high_tc': clean.flag_tc_high,
                'high_tg': clean.flag_tg_high,
                'low_hdl': clean.flag_hdl_low,
                'obesity': clean.flag_obesity,
                'smoking': clean.flag_smoking
            },
            'rule_version': clean.rule_version,
            'inference_time_ms': clean.inference_time_ms,
            'created_at': clean.created_at.isoformat()
        })

    finally:
        db.close()
