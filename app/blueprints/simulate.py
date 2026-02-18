"""
Simulate Blueprint

위험요인 계산 API (Inference)
"""

import time
from flask import Blueprint, request, jsonify
from app.middleware.auth import require_api_key

simulate_bp = Blueprint('simulate', __name__)


def calculate_bmi(height, weight):
    """BMI 계산"""
    if not height or not weight or height < 140 or height > 200 or weight < 30 or weight > 150:
        return None
    height_m = height / 100.0
    return round(weight / (height_m ** 2), 1)


def calculate_risk_factors(data):
    """
    위험요인 계산 (ETL 로직과 동일)

    Args:
        data: 입력 데이터 dict

    Returns:
        dict: flags, count, group, explanations
    """
    flags = {}
    explanations = []

    # BMI 계산
    bmi = calculate_bmi(data['height'], data['weight'])

    # 1. 고혈압
    flags['hypertension'] = data['systolic_bp'] >= 140 or data['diastolic_bp'] >= 90
    if flags['hypertension']:
        explanations.append(
            f"Hypertension: SBP≥140 or DBP≥90 ({data['systolic_bp']}/{data['diastolic_bp']})"
        )

    # 2. 당뇨
    flags['diabetes'] = data['fasting_glucose'] >= 126
    if flags['diabetes']:
        explanations.append(f"Diabetes: fasting glucose≥126 ({data['fasting_glucose']})")

    # 3. 고콜레스테롤
    flags['high_total_cholesterol'] = data['total_cholesterol'] >= 240
    if flags['high_total_cholesterol']:
        explanations.append(f"High TC: total cholesterol≥240 ({data['total_cholesterol']})")

    # 4. 고중성지방
    flags['high_triglycerides'] = data['triglycerides'] >= 200
    if flags['high_triglycerides']:
        explanations.append(f"High TG: triglycerides≥200 ({data['triglycerides']})")

    # 5. 저HDL
    flags['low_hdl'] = data['hdl_cholesterol'] < 40
    if flags['low_hdl']:
        explanations.append(f"Low HDL: hdl<40 ({data['hdl_cholesterol']})")

    # 6. 비만
    flags['obesity_asia'] = bmi >= 25 if bmi else False
    if flags['obesity_asia']:
        explanations.append(f"Obesity(Asia): BMI≥25 ({bmi})")

    # 7. 흡연
    smoking_map = {'never': 1, 'former': 2, 'current': 3}
    smoking_code = smoking_map.get(data['smoking_status'], 1)
    flags['smoking'] = smoking_code == 3
    if flags['smoking']:
        explanations.append("Smoking: current smoker")

    # 위험요인 개수
    count = sum(flags.values())

    # Risk Group
    if flags['diabetes']:
        group = 'CHD_RISK_EQUIVALENT'
    elif count >= 2:
        group = 'MULTIPLE_RISK_FACTORS'
    else:
        group = 'ZERO_TO_ONE_RISK_FACTOR'

    return {
        'flags': flags,
        'count': count,
        'group': group,
        'explanations': explanations,
        'bmi': bmi
    }


@simulate_bp.route('/simulate', methods=['POST'])
@require_api_key
def simulate():
    """
    POST /simulate

    단일 환자 위험요인 계산

    Request Body:
        {
            "age_group": 12,
            "gender": 1,
            "height": 170,
            "weight": 80,
            "systolic_bp": 145,
            "diastolic_bp": 92,
            "fasting_glucose": 110,
            "total_cholesterol": 250,
            "triglycerides": 180,
            "hdl_cholesterol": 38,
            "smoking_status": "current"
        }
    """
    start_time = time.time()

    # 요청 데이터
    data = request.get_json()

    # 검증
    required_fields = [
        'age_group', 'gender', 'height', 'weight',
        'systolic_bp', 'diastolic_bp', 'fasting_glucose',
        'total_cholesterol', 'triglycerides', 'hdl_cholesterol',
        'smoking_status'
    ]

    missing_fields = [f for f in required_fields if f not in data]
    if missing_fields:
        return jsonify({
            'error': 'Validation Error',
            'message': 'Missing required fields',
            'details': {'missing': missing_fields}
        }), 400

    # 범위 검증
    validations = {
        'age_group': (5, 18),
        'gender': (1, 2),
        'height': (140, 200),
        'weight': (30, 150),
        'systolic_bp': (70, 250),
        'diastolic_bp': (40, 150),
        'fasting_glucose': (50, 400),
        'total_cholesterol': (100, 400),
        'triglycerides': (30, 500),
        'hdl_cholesterol': (20, 100),
    }

    errors = {}
    for field, (min_val, max_val) in validations.items():
        if field in data and not (min_val <= data[field] <= max_val):
            errors[field] = f"Must be between {min_val} and {max_val}"

    if data['smoking_status'] not in ['never', 'former', 'current']:
        errors['smoking_status'] = "Must be 'never', 'former', or 'current'"

    if errors:
        return jsonify({
            'error': 'Validation Error',
            'message': 'Invalid input data',
            'details': errors
        }), 400

    # 위험요인 계산
    result = calculate_risk_factors(data)

    # Inference 시간
    inference_time_ms = int((time.time() - start_time) * 1000)

    # 응답
    return jsonify({
        'input': {
            'age_group': data['age_group'],
            'age_display': f"{data['age_group'] * 5}세",
            'gender': data['gender'],
            'gender_display': '남성' if data['gender'] == 1 else '여성',
            'bmi': result['bmi']
        },
        'result': {
            'risk_factor_count': result['count'],
            'risk_group': result['group'],
            'flags': result['flags'],
            'explanations': result['explanations'],
            'rule_version': 'guideline-v1',
            'inference_time_ms': inference_time_ms
        },
        'disclaimer': 'This is NOT a diagnostic tool. Consult medical professionals for any health concerns.'
    })
