"""
인덱스 확인 및 DB 상태 조회
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from app.database import engine

def check_indexes():
    """현재 생성된 인덱스 확인"""
    print("=" * 70)
    print("📊 Database Index Status")
    print("=" * 70)

    with engine.connect() as conn:
        # raw_health_check 인덱스
        print("\n[raw_health_check 테이블]")
        result = conn.execute(text("SHOW INDEX FROM raw_health_check"))
        for row in result:
            if row.Key_name != 'PRIMARY':
                print(f"  - {row.Key_name}: {row.Column_name}")

        # clean_risk_result 인덱스
        print("\n[clean_risk_result 테이블]")
        result = conn.execute(text("SHOW INDEX FROM clean_risk_result"))
        for row in result:
            if row.Key_name != 'PRIMARY':
                print(f"  - {row.Key_name}: {row.Column_name}")

        # 테이블 크기
        print("\n" + "=" * 70)
        print("💾 Table Size")
        print("=" * 70)
        result = conn.execute(text("""
            SELECT
                TABLE_NAME,
                ROUND((DATA_LENGTH + INDEX_LENGTH) / 1024 / 1024, 2) AS size_mb,
                ROUND(DATA_LENGTH / 1024 / 1024, 2) AS data_mb,
                ROUND(INDEX_LENGTH / 1024 / 1024, 2) AS index_mb,
                TABLE_ROWS
            FROM information_schema.tables
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME IN ('raw_health_check', 'clean_risk_result')
        """))
        for row in result:
            print(f"\n{row.TABLE_NAME}:")
            print(f"  Total:  {row.size_mb:>8.2f} MB")
            print(f"  Data:   {row.data_mb:>8.2f} MB")
            print(f"  Index:  {row.index_mb:>8.2f} MB")
            print(f"  Rows:   {row.TABLE_ROWS:>8,}")

if __name__ == '__main__':
    check_indexes()
