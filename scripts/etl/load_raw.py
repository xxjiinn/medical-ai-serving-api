"""
ETL Step 1: CSV → raw_health_check

국민건강보험공단 건강검진 CSV를 MySQL raw 테이블에 적재
- Chunk 기반 처리 (메모리 제어)
- 처리속도 측정
"""

import sys
import os
import time
from pathlib import Path

# 프로젝트 루트 경로를 sys.path에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
from sqlalchemy import text
from app.database import engine, init_db
from app.config import get_config

# 설정
config = get_config()
CHUNK_SIZE = config.ETL_CHUNK_SIZE  # 10,000 rows

# CSV 파일 경로 (프로젝트 루트)
CSV_FILE = project_root / "국민건강보험공단_건강검진정보_2024.CSV"


def validate_csv():
    """CSV 파일 존재 확인"""
    if not CSV_FILE.exists():
        print(f"❌ CSV file not found: {CSV_FILE}")
        sys.exit(1)
    print(f"✅ CSV file found: {CSV_FILE}")


def load_csv_to_raw():
    """
    CSV → raw_health_check 테이블 적재

    Returns:
        tuple: (총 처리 행 수, 처리 시간(초))
    """
    start_time = time.time()
    total_rows = 0

    print(f"\n📊 Starting ETL: CSV → raw_health_check")
    print(f"   🔥 Chunk size: {CHUNK_SIZE:,} rows")
    print(f"   Encoding: cp949\n")

    # 컬럼 매핑 (CSV → DB)
    column_mapping = {
        '기준년도': 'reference_year',
        '가입자일련번호': 'subscriber_id',
        '시도코드': 'province_code',
        '성별코드': 'gender_code',
        '연령대코드(5세단위)': 'age_group_code',
        '신장(5cm단위)': 'height',
        '체중(5kg단위)': 'weight',
        '허리둘레': 'waist_circumference',
        '수축기혈압': 'systolic_bp',
        '이완기혈압': 'diastolic_bp',
        '식전혈당(공복혈당)': 'fasting_glucose',
        '총콜레스테롤': 'total_cholesterol',
        '트리글리세라이드': 'triglycerides',
        'HDL콜레스테롤': 'hdl_cholesterol',
        'LDL콜레스테롤': 'ldl_cholesterol',
        '흡연상태': 'smoking_status',
    }

    # Chunk 단위로 CSV 읽기
    chunk_num = 0
    for chunk in pd.read_csv(
        CSV_FILE,
        encoding='cp949',
        chunksize=CHUNK_SIZE,
        usecols=column_mapping.keys()  # 필요한 컬럼만 읽기
    ):
        chunk_num += 1
        chunk_start = time.time()

        # 컬럼명 변경
        chunk = chunk.rename(columns=column_mapping)

        # NULL 처리 (pandas NaN → None)
        chunk = chunk.where(pd.notnull(chunk), None)

        # MySQL에 삽입
        chunk.to_sql(
            'raw_health_check',
            con=engine,
            if_exists='append',  # 기존 데이터에 추가
            index=False,  # DataFrame 인덱스 제외
            method='multi'  # 다중 INSERT (성능 개선)
        )

        chunk_rows = len(chunk)
        total_rows += chunk_rows
        chunk_time = time.time() - chunk_start

        print(f"   Chunk {chunk_num}: {chunk_rows:,} rows | {chunk_time:.2f}s | {chunk_rows/chunk_time:.0f} rows/s")

    elapsed_time = time.time() - start_time
    throughput = total_rows / elapsed_time if elapsed_time > 0 else 0

    print(f"\n✅ ETL Complete!")
    print(f"   Total rows: {total_rows:,}")
    print(f"   Total time: {elapsed_time:.2f}s")
    print(f"   Throughput: {throughput:.0f} rows/s\n")

    return total_rows, elapsed_time


def verify_data():
    """데이터 적재 검증"""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM raw_health_check"))
        count = result.scalar()
        print(f"🔍 Verification: {count:,} rows in raw_health_check")

        # 샘플 데이터 확인
        sample = conn.execute(text("SELECT * FROM raw_health_check LIMIT 3"))
        print("\n📋 Sample data:")
        for row in sample:
            print(f"   ID {row.id}: age={row.age_group_code}, gender={row.gender_code}, "
                  f"sbp={row.systolic_bp}, glucose={row.fasting_glucose}")


def main():
    """메인 실행"""
    print("=" * 70)
    print("ETL Script 1: Load CSV to raw_health_check")
    print("=" * 70)

    # 1. CSV 파일 확인
    validate_csv()

    # 2. 테이블 생성 (없으면 생성)
    print("\n🔧 Creating database tables...")
    init_db()

    # 3. 기존 데이터 확인
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM raw_health_check"))
        existing_count = result.scalar()
        if existing_count > 0:
            print(f"\n⚠️  Warning: {existing_count:,} rows already exist in raw_health_check")
            response = input("   Continue? (y/n): ")
            if response.lower() != 'y':
                print("   Aborted.")
                sys.exit(0)
            # 기존 데이터 삭제
            conn.execute(text("TRUNCATE TABLE raw_health_check"))
            conn.commit()
            print("   ✅ Existing data cleared")

    # 4. CSV → raw 적재
    total_rows, elapsed_time = load_csv_to_raw()

    # 5. 검증
    verify_data()

    # 6. 성능 리포트
    print("\n" + "=" * 70)
    print("📈 Performance Report")
    print("=" * 70)
    print(f"Total Rows:    {total_rows:,}")
    print(f"Elapsed Time:  {elapsed_time:.2f} seconds")
    print(f"Throughput:    {total_rows/elapsed_time:.0f} rows/second")
    print("=" * 70)


if __name__ == '__main__':
    main()
