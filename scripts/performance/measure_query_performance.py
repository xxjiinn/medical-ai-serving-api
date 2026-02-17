"""
쿼리 성능 측정 (인덱스 활용)

주요 쿼리의 실행 시간을 측정하고 EXPLAIN 분석
"""

import sys
import time
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from app.database import engine

# 측정 반복 횟수
ITERATIONS = 10


def measure_query(name, query, iterations=ITERATIONS):
    """
    쿼리 실행 시간 측정

    Args:
        name: 쿼리 이름
        query: SQL 쿼리 문자열
        iterations: 반복 횟수

    Returns:
        dict: 측정 결과
    """
    times = []

    with engine.connect() as conn:
        # Warm-up (첫 실행은 캐시 등으로 느릴 수 있음)
        conn.execute(text(query))

        # 측정
        for _ in range(iterations):
            start = time.time()
            conn.execute(text(query))
            elapsed = (time.time() - start) * 1000  # ms
            times.append(elapsed)

    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)
    p95_time = sorted(times)[int(len(times) * 0.95)]

    return {
        'name': name,
        'avg': avg_time,
        'min': min_time,
        'max': max_time,
        'p95': p95_time,
        'times': times
    }


def explain_query(query):
    """쿼리 실행 계획 조회"""
    with engine.connect() as conn:
        result = conn.execute(text(f"EXPLAIN {query}"))
        return list(result)


def run_performance_tests():
    """성능 테스트 실행"""
    print("=" * 70)
    print("⚡ Query Performance Measurement")
    print("=" * 70)
    print(f"Iterations: {ITERATIONS} times per query\n")

    queries = {
        "Q1: 위험군별 통계": """
            SELECT risk_group, COUNT(*) as count
            FROM clean_risk_result
            WHERE invalid_flag = FALSE
            GROUP BY risk_group
        """,
        "Q2: 연령대별 통계": """
            SELECT r.age_group_code, COUNT(*) as count,
                   AVG(c.risk_factor_count) as avg_risk_count
            FROM raw_health_check r
            JOIN clean_risk_result c ON r.id = c.raw_id
            WHERE c.invalid_flag = FALSE
            GROUP BY r.age_group_code
            ORDER BY r.age_group_code
        """,
        "Q3: 페이징 조회": """
            SELECT c.id, r.age_group_code, r.gender_code,
                   c.bmi, c.risk_factor_count, c.risk_group
            FROM clean_risk_result c
            JOIN raw_health_check r ON c.raw_id = r.id
            WHERE c.invalid_flag = FALSE
            ORDER BY c.id
            LIMIT 20 OFFSET 0
        """,
        "Q4: 고위험군 필터": """
            SELECT COUNT(*)
            FROM clean_risk_result
            WHERE risk_group = 'CHD_RISK_EQUIVALENT'
            AND invalid_flag = FALSE
        """,
        "Q5: 연령대 + 위험군 복합": """
            SELECT r.age_group_code, c.risk_group, COUNT(*) as count
            FROM raw_health_check r
            JOIN clean_risk_result c ON r.id = c.raw_id
            WHERE c.invalid_flag = FALSE
            GROUP BY r.age_group_code, c.risk_group
        """
    }

    results = []

    for name, query in queries.items():
        print(f"\n{'=' * 70}")
        print(f"📊 {name}")
        print(f"{'=' * 70}")

        # 성능 측정
        result = measure_query(name, query)
        results.append(result)

        print(f"\n⏱️  Performance:")
        print(f"   Average: {result['avg']:>8.2f} ms")
        print(f"   Min:     {result['min']:>8.2f} ms")
        print(f"   Max:     {result['max']:>8.2f} ms")
        print(f"   P95:     {result['p95']:>8.2f} ms")

        # EXPLAIN 분석
        print(f"\n🔍 EXPLAIN:")
        explain_result = explain_query(query.strip())
        for row in explain_result:
            print(f"   Table: {row.table:20s} | Type: {row.type:10s} | "
                  f"Key: {str(row.key):20s} | Rows: {row.rows:>8,}")

    # 요약
    print("\n" + "=" * 70)
    print("📈 Performance Summary")
    print("=" * 70)
    print(f"\n{'Query':<35s} {'Avg (ms)':>12s} {'P95 (ms)':>12s}")
    print("-" * 70)
    for r in results:
        print(f"{r['name']:<35s} {r['avg']:>12.2f} {r['p95']:>12.2f}")

    # 인덱스 활용도
    print("\n" + "=" * 70)
    print("✅ Index Usage Analysis")
    print("=" * 70)
    print("\n주요 인덱스:")
    print("  - idx_age_group: 연령대 조회 최적화")
    print("  - idx_risk_group: 위험군 조회 최적화")
    print("  - idx_invalid: 유효 데이터 필터링")
    print("  - idx_composite_stats: risk_group + invalid_flag 복합")
    print("\n성능 개선 포인트:")
    if any(r['avg'] > 100 for r in results):ㅎ
        print("  ⚠️  일부 쿼리가 100ms 초과 → 인덱스 추가 고려")
    else:
        print("  ✅ 모든 쿼리가 100ms 이하 → 인덱스 효과적")


if __name__ == '__main__':
    run_performance_tests()
