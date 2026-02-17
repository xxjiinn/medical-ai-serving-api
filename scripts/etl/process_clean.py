"""
ETL Step 2: raw → clean_risk_result

raw_health_check 데이터로 위험요인 판정 수행
- 7개 위험요인 flag 계산
- risk_factor_count, risk_group 산출
- Inference 시간 측정
"""

import sys
import time
from pathlib import Path

# 프로젝트 루트 경로
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from app.database import engine, SessionLocal
from app.models.health_check import RawHealthCheck, CleanRiskResult
from app.config import get_config

# 설정
config = get_config()
BATCH_SIZE = 1000  # 한 번에 처리할 행 수


def calculate_bmi(height, weight):
    """
    BMI 계산

    Args:
        height: 신장 (cm)
        weight: 체중 (kg)

    Returns:
        float or None: BMI 값 (계산 불가 시 None)
    """
    if not height or not weight:
        return None
    if height < 140 or height > 200:  # 이상치
        return None
    if weight < 30 or weight > 150:  # 이상치
        return None

    height_m = height / 100.0
    bmi = weight / (height_m ** 2)
    return round(bmi, 1)


def is_valid_data(raw_data):
    """
    데이터 유효성 검증 (생물학적 범위)

    Args:
        raw_data: RawHealthCheck 객체

    Returns:
        bool: 유효하면 True, 이상치면 False
    """
    # 필수 값 확인
    if not raw_data.height or not raw_data.weight:
        return False
    if not raw_data.systolic_bp or not raw_data.diastolic_bp:
        return False
    if not raw_data.fasting_glucose:
        return False
    if not raw_data.total_cholesterol:
        return False
    if not raw_data.hdl_cholesterol:
        return False

    # 생물학적 범위 검증
    if raw_data.systolic_bp < 70 or raw_data.systolic_bp > 250:
        return False
    if raw_data.diastolic_bp < 40 or raw_data.diastolic_bp > 150:
        return False
    if raw_data.fasting_glucose < 50 or raw_data.fasting_glucose > 400:
        return False
    if raw_data.total_cholesterol < 100 or raw_data.total_cholesterol > 400:
        return False

    return True


def calculate_risk_factors(raw_data, bmi):
    """
    7개 위험요인 flag 계산 (가이드라인 기반)

    Args:
        raw_data: RawHealthCheck 객체
        bmi: BMI 값

    Returns:
        dict: {
            'flag_hypertension': bool,
            'flag_diabetes': bool,
            ...
        }
    """
    flags = {}
#
    # 1. 고혈압 (SBP≥140 or DBP≥90)
    flags['flag_hypertension'] = (
        raw_data.systolic_bp >= 140 or raw_data.diastolic_bp >= 90
    )

    # 2. 당뇨 (공복혈당≥126)
    flags['flag_diabetes'] = raw_data.fasting_glucose >= 126

    # 3. 고콜레스테롤 (TC≥240)
    flags['flag_tc_high'] = raw_data.total_cholesterol >= 240

    # 4. 고중성지방 (TG≥200)
    flags['flag_tg_high'] = (
        raw_data.triglycerides >= 200 if raw_data.triglycerides else False
    )

    # 5. 저HDL (HDL<40)
    flags['flag_hdl_low'] = raw_data.hdl_cholesterol < 40

    # 6. 비만 (BMI≥25, 아시아 기준)
    flags['flag_obesity'] = bmi >= 25 if bmi else False

    # 7. 흡연 (현재흡연자=3)
    flags['flag_smoking'] = raw_data.smoking_status == 3 if raw_data.smoking_status else False

    return flags


def calculate_risk_group(flags):
    """
    Risk Group 계산 (ATP III 프레임워크)

    Args:
        flags: 위험요인 dict

    Returns:
        tuple: (risk_factor_count, risk_group)
    """
    # 위험요인 개수
    count = sum(flags.values())

    # Risk Group 분류
    if flags['flag_diabetes']:
        # 당뇨 있음 → CHD Risk Equivalent (최고 위험)
        group = 'CHD_RISK_EQUIVALENT'
    elif count >= 2:
        # 위험요인 2개 이상 → Multiple Risk Factors
        group = 'MULTIPLE_RISK_FACTORS'
    else:
        # 위험요인 0~1개 → 저위험
        group = 'ZERO_TO_ONE_RISK_FACTOR'

    return count, group


def process_single_record(raw_data):
    """
    단일 레코드 처리 (Inference 로직)

    Args:
        raw_data: RawHealthCheck 객체

    Returns:
        CleanRiskResult: 판정 결과 객체
    """
    inference_start = time.time()

    # 1. 유효성 검증
    valid = is_valid_data(raw_data)

    if not valid:
        # 유효하지 않은 데이터 → invalid_flag=True, 기본값 저장
        clean_result = CleanRiskResult(
            raw_id=raw_data.id,
            bmi=None,
            flag_hypertension=False,
            flag_diabetes=False,
            flag_tc_high=False,
            flag_tg_high=False,
            flag_hdl_low=False,
            flag_obesity=False,
            flag_smoking=False,
            risk_factor_count=0,
            risk_group='ZERO_TO_ONE_RISK_FACTOR',
            invalid_flag=True,
            inference_time_ms=0
        )
    else:
        # 2. BMI 계산
        bmi = calculate_bmi(raw_data.height, raw_data.weight)

        # 3. 위험요인 flag 계산
        flags = calculate_risk_factors(raw_data, bmi)

        # 4. Risk Group 계산
        count, group = calculate_risk_group(flags)

        # 5. Inference 시간 측정
        inference_time = int((time.time() - inference_start) * 1000)  # ms

        # 6. 결과 객체 생성
        clean_result = CleanRiskResult(
            raw_id=raw_data.id,
            bmi=bmi,
            risk_factor_count=count,
            risk_group=group,
            invalid_flag=False,
            inference_time_ms=inference_time,
            **flags  # flag_* 컬럼들
        )

    return clean_result


def process_all_records():
    """
    모든 raw 레코드 처리

    Returns:
        tuple: (처리 행 수, 유효 행 수, 무효 행 수, 처리 시간)
    """
    start_time = time.time()
    total_rows = 0
    valid_rows = 0
    invalid_rows = 0

    db = SessionLocal()

    try:
        # raw 테이블 총 행 수
        total_count = db.query(RawHealthCheck).count()
        print(f"\n📊 Processing {total_count:,} records from raw_health_check\n")

        # Batch 단위로 처리
        offset = 0
        batch_num = 0

        while True:
            batch_num += 1
            batch_start = time.time()

            # Batch 조회
            raw_batch = db.query(RawHealthCheck).offset(offset).limit(BATCH_SIZE).all()

            if not raw_batch:
                break

            # Batch 처리
            clean_batch = []
            for raw_data in raw_batch:
                clean_result = process_single_record(raw_data)
                clean_batch.append(clean_result)

                total_rows += 1
                if clean_result.invalid_flag:
                    invalid_rows += 1
                else:
                    valid_rows += 1

            # DB에 저장
            db.bulk_save_objects(clean_batch)
            db.commit()

            batch_time = time.time() - batch_start
            throughput = len(raw_batch) / batch_time if batch_time > 0 else 0

            print(f"   Batch {batch_num}: {len(raw_batch):,} rows | "
                  f"{batch_time:.2f}s | {throughput:.0f} rows/s")

            offset += BATCH_SIZE

    finally:
        db.close()

    elapsed_time = time.time() - start_time

    print(f"\n✅ Processing Complete!")
    print(f"   Total rows:   {total_rows:,}")
    print(f"   Valid rows:   {valid_rows:,} ({valid_rows/total_rows*100:.1f}%)")
    print(f"   Invalid rows: {invalid_rows:,} ({invalid_rows/total_rows*100:.1f}%)")
    print(f"   Total time:   {elapsed_time:.2f}s")
    print(f"   Throughput:   {total_rows/elapsed_time:.0f} rows/s\n")

    return total_rows, valid_rows, invalid_rows, elapsed_time


def verify_results():
    """결과 검증"""
    db = SessionLocal()

    try:
        # 통계 조회
        total = db.query(CleanRiskResult).count()
        valid = db.query(CleanRiskResult).filter_by(invalid_flag=False).count()
        invalid = db.query(CleanRiskResult).filter_by(invalid_flag=True).count()

        print(f"🔍 Verification:")
        print(f"   Total:   {total:,} rows")
        print(f"   Valid:   {valid:,} rows")
        print(f"   Invalid: {invalid:,} rows\n")

        # Risk Group 분포
        print(f"📊 Risk Group Distribution:")
        for group in ['ZERO_TO_ONE_RISK_FACTOR', 'MULTIPLE_RISK_FACTORS', 'CHD_RISK_EQUIVALENT']:
            count = db.query(CleanRiskResult).filter_by(
                risk_group=group,
                invalid_flag=False
            ).count()
            pct = count / valid * 100 if valid > 0 else 0
            print(f"   {group:30s}: {count:6,} ({pct:5.1f}%)")

        # 샘플 데이터
        print(f"\n📋 Sample Results:")
        samples = db.query(CleanRiskResult).filter_by(invalid_flag=False).limit(3).all()
        for sample in samples:
            print(f"   ID {sample.id}: count={sample.risk_factor_count}, "
                  f"group={sample.risk_group}, bmi={sample.bmi}")

    finally:
        db.close()


def main():
    """메인 실행"""
    print("=" * 70)
    print("ETL Script 2: Process raw → clean_risk_result")
    print("=" * 70)

    # 1. 기존 데이터 확인
    db = SessionLocal()
    existing_count = db.query(CleanRiskResult).count()
    db.close()

    if existing_count > 0:
        print(f"\n⚠️  Warning: {existing_count:,} rows already exist in clean_risk_result")
        response = input("   Clear and reprocess? (y/n): ")
        if response.lower() != 'y':
            print("   Aborted.")
            sys.exit(0)
        # 기존 데이터 삭제
        with engine.connect() as conn:
            conn.execute(text("TRUNCATE TABLE clean_risk_result"))
            conn.commit()
            print("   ✅ Existing data cleared")

    # 2. 처리 실행
    total, valid, invalid, elapsed = process_all_records()

    # 3. 검증
    verify_results()

    # 4. 성능 리포트
    print("\n" + "=" * 70)
    print("📈 Performance Report")
    print("=" * 70)
    print(f"Total Processed:  {total:,}")
    print(f"Valid Records:    {valid:,} ({valid/total*100:.1f}%)")
    print(f"Invalid Records:  {invalid:,} ({invalid/total*100:.1f}%)")
    print(f"Elapsed Time:     {elapsed:.2f} seconds")
    print(f"Throughput:       {total/elapsed:.0f} rows/second")
    print("=" * 70)


if __name__ == '__main__':
    main()
