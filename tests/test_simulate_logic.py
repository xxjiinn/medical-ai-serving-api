"""
위험요인 계산 로직 테스트

BMI, 위험요인 플래그, 위험군 분류 테스트
"""

import pytest
from app.blueprints.simulate import calculate_bmi, calculate_risk_factors


class TestBMICalculation:
    """BMI 계산 테스트"""

    def test_normal_bmi(self):
        """정상 BMI 계산"""
        bmi = calculate_bmi(170, 65)
        assert bmi == 22.5

    def test_overweight_bmi(self):
        """과체중 BMI 계산"""
        bmi = calculate_bmi(170, 85)
        assert bmi == 29.4

    def test_invalid_height_low(self):
        """비정상 신장 (낮음)"""
        bmi = calculate_bmi(130, 60)
        assert bmi is None

    def test_invalid_height_high(self):
        """비정상 신장 (높음)"""
        bmi = calculate_bmi(220, 80)
        assert bmi is None

    def test_invalid_weight_low(self):
        """비정상 체중 (낮음)"""
        bmi = calculate_bmi(170, 20)
        assert bmi is None

    def test_invalid_weight_high(self):
        """비정상 체중 (높음)"""
        bmi = calculate_bmi(170, 200)
        assert bmi is None


class TestRiskFactorCalculation:
    """위험요인 계산 테스트"""

    def test_hypertension_systolic(self):
        """고혈압 - 수축기혈압 기준"""
        data = {
            'height': 170, 'weight': 70,
            'systolic_bp': 145, 'diastolic_bp': 80,
            'fasting_glucose': 100,
            'total_cholesterol': 200,
            'triglycerides': 150,
            'hdl_cholesterol': 50,
            'smoking_status': 'never'
        }
        result = calculate_risk_factors(data)
        assert result['flags']['hypertension'] == True
        assert result['count'] >= 1

    def test_hypertension_diastolic(self):
        """고혈압 - 이완기혈압 기준"""
        data = {
            'height': 170, 'weight': 70,
            'systolic_bp': 130, 'diastolic_bp': 95,
            'fasting_glucose': 100,
            'total_cholesterol': 200,
            'triglycerides': 150,
            'hdl_cholesterol': 50,
            'smoking_status': 'never'
        }
        result = calculate_risk_factors(data)
        assert result['flags']['hypertension'] == True

    def test_diabetes(self):
        """당뇨병 - 공복혈당 기준"""
        data = {
            'height': 170, 'weight': 70,
            'systolic_bp': 120, 'diastolic_bp': 80,
            'fasting_glucose': 130,
            'total_cholesterol': 200,
            'triglycerides': 150,
            'hdl_cholesterol': 50,
            'smoking_status': 'never'
        }
        result = calculate_risk_factors(data)
        assert result['flags']['diabetes'] == True
        # 당뇨병이 있으면 무조건 CHD_RISK_EQUIVALENT
        assert result['group'] == 'CHD_RISK_EQUIVALENT'

    def test_high_cholesterol(self):
        """고콜레스테롤 - 총 콜레스테롤 기준"""
        data = {
            'height': 170, 'weight': 70,
            'systolic_bp': 120, 'diastolic_bp': 80,
            'fasting_glucose': 100,
            'total_cholesterol': 250,
            'triglycerides': 150,
            'hdl_cholesterol': 50,
            'smoking_status': 'never'
        }
        result = calculate_risk_factors(data)
        assert result['flags']['high_total_cholesterol'] == True

    def test_high_triglycerides(self):
        """고중성지방"""
        data = {
            'height': 170, 'weight': 70,
            'systolic_bp': 120, 'diastolic_bp': 80,
            'fasting_glucose': 100,
            'total_cholesterol': 200,
            'triglycerides': 220,
            'hdl_cholesterol': 50,
            'smoking_status': 'never'
        }
        result = calculate_risk_factors(data)
        assert result['flags']['high_triglycerides'] == True

    def test_low_hdl(self):
        """저HDL 콜레스테롤"""
        data = {
            'height': 170, 'weight': 70,
            'systolic_bp': 120, 'diastolic_bp': 80,
            'fasting_glucose': 100,
            'total_cholesterol': 200,
            'triglycerides': 150,
            'hdl_cholesterol': 35,
            'smoking_status': 'never'
        }
        result = calculate_risk_factors(data)
        assert result['flags']['low_hdl'] == True

    def test_obesity(self):
        """비만 - BMI 25 이상 (아시아 기준)"""
        data = {
            'height': 170, 'weight': 85,  # BMI 29.4
            'systolic_bp': 120, 'diastolic_bp': 80,
            'fasting_glucose': 100,
            'total_cholesterol': 200,
            'triglycerides': 150,
            'hdl_cholesterol': 50,
            'smoking_status': 'never'
        }
        result = calculate_risk_factors(data)
        assert result['flags']['obesity_asia'] == True
        assert result['bmi'] >= 25

    def test_smoking_current(self):
        """현재 흡연자"""
        data = {
            'height': 170, 'weight': 70,
            'systolic_bp': 120, 'diastolic_bp': 80,
            'fasting_glucose': 100,
            'total_cholesterol': 200,
            'triglycerides': 150,
            'hdl_cholesterol': 50,
            'smoking_status': 'current'
        }
        result = calculate_risk_factors(data)
        assert result['flags']['smoking'] == True

    def test_smoking_former(self):
        """과거 흡연자 - 위험요인 아님"""
        data = {
            'height': 170, 'weight': 70,
            'systolic_bp': 120, 'diastolic_bp': 80,
            'fasting_glucose': 100,
            'total_cholesterol': 200,
            'triglycerides': 150,
            'hdl_cholesterol': 50,
            'smoking_status': 'former'
        }
        result = calculate_risk_factors(data)
        assert result['flags']['smoking'] == False

    def test_healthy_patient_zero_risk(self):
        """정상 환자 - 위험요인 0개"""
        data = {
            'height': 165, 'weight': 60,  # BMI 22.0
            'systolic_bp': 110, 'diastolic_bp': 70,
            'fasting_glucose': 90,
            'total_cholesterol': 180,
            'triglycerides': 120,
            'hdl_cholesterol': 55,
            'smoking_status': 'never'
        }
        result = calculate_risk_factors(data)
        assert result['count'] == 0
        assert result['group'] == 'ZERO_TO_ONE_RISK_FACTOR'

    def test_multiple_risk_factors(self):
        """다중 위험요인 - 2개 이상"""
        data = {
            'height': 170, 'weight': 85,  # obesity
            'systolic_bp': 145, 'diastolic_bp': 95,  # hypertension
            'fasting_glucose': 100,
            'total_cholesterol': 200,
            'triglycerides': 150,
            'hdl_cholesterol': 50,
            'smoking_status': 'never'
        }
        result = calculate_risk_factors(data)
        assert result['count'] >= 2
        assert result['group'] == 'MULTIPLE_RISK_FACTORS'

    def test_all_risk_factors(self):
        """모든 위험요인 보유"""
        data = {
            'height': 170, 'weight': 85,  # obesity
            'systolic_bp': 150, 'diastolic_bp': 95,  # hypertension
            'fasting_glucose': 130,  # diabetes
            'total_cholesterol': 250,  # high cholesterol
            'triglycerides': 220,  # high triglycerides
            'hdl_cholesterol': 35,  # low HDL
            'smoking_status': 'current'  # smoking
        }
        result = calculate_risk_factors(data)
        assert result['count'] == 7
        # 당뇨병이 있으므로 CHD_RISK_EQUIVALENT
        assert result['group'] == 'CHD_RISK_EQUIVALENT'

    def test_explanations_exist(self):
        """설명 메시지 생성 확인"""
        data = {
            'height': 170, 'weight': 85,
            'systolic_bp': 145, 'diastolic_bp': 80,
            'fasting_glucose': 100,
            'total_cholesterol': 200,
            'triglycerides': 150,
            'hdl_cholesterol': 50,
            'smoking_status': 'never'
        }
        result = calculate_risk_factors(data)
        # 고혈압, 비만 2개 위험요인이므로 설명 2개 존재
        assert len(result['explanations']) >= 2
        assert any('Hypertension' in exp for exp in result['explanations'])
        assert any('Obesity' in exp for exp in result['explanations'])
