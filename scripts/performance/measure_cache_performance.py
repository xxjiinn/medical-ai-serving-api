"""
Redis 캐싱 성능 측정

Cache Miss vs Cache Hit 응답시간 비교
"""

import time
import requests
import redis

# 설정
BASE_URL = "http://localhost:5001"
API_KEY = "medical-ai-secret-key-2026"
HEADERS = {"X-API-KEY": API_KEY}

# Redis 클라이언트
r = redis.from_url("redis://localhost:6379/0")


def clear_cache():
    """모든 캐시 삭제"""
    keys = r.keys("cache:*")
    if keys:
        r.delete(*keys)
        print(f"✓ Cleared {len(keys)} cache keys")


def measure_endpoint(endpoint, name):
    """
    엔드포인트 성능 측정

    Args:
        endpoint (str): API 엔드포인트 경로
        name (str): 측정 이름
    """
    print(f"\n{'=' * 60}")
    print(f"Testing: {name}")
    print(f"Endpoint: {endpoint}")
    print(f"{'=' * 60}")

    # 1. Cache Miss 측정 (3회)
    cache_miss_times = []
    for i in range(3):
        clear_cache()
        time.sleep(0.1)  # Redis 처리 대기

        start = time.time()
        response = requests.get(f"{BASE_URL}{endpoint}", headers=HEADERS)
        elapsed = (time.time() - start) * 1000  # ms

        if response.status_code == 200:
            data = response.json()
            cached = data.get('cached', False)
            cache_miss_times.append(elapsed)
            print(f"  Cache Miss #{i+1}: {elapsed:.0f}ms (cached={cached})")
        else:
            print(f"  Error: {response.status_code}")

    avg_miss = sum(cache_miss_times) / len(cache_miss_times)

    # 2. Cache Hit 측정 (5회)
    clear_cache()
    # Warm up cache
    requests.get(f"{BASE_URL}{endpoint}", headers=HEADERS)
    time.sleep(0.1)

    cache_hit_times = []
    for i in range(5):
        start = time.time()
        response = requests.get(f"{BASE_URL}{endpoint}", headers=HEADERS)
        elapsed = (time.time() - start) * 1000  # ms

        if response.status_code == 200:
            data = response.json()
            cached = data.get('cached', False)
            cache_hit_times.append(elapsed)
            print(f"  Cache Hit #{i+1}: {elapsed:.0f}ms (cached={cached})")

    avg_hit = sum(cache_hit_times) / len(cache_hit_times)

    # 결과
    improvement = ((avg_miss - avg_hit) / avg_miss) * 100
    print(f"\n{'─' * 60}")
    print(f"Results:")
    print(f"  Avg Cache Miss: {avg_miss:.0f}ms")
    print(f"  Avg Cache Hit:  {avg_hit:.0f}ms")
    print(f"  Improvement:    {improvement:.1f}%")
    print(f"  Speedup:        {avg_miss / avg_hit:.1f}x faster")
    print(f"{'─' * 60}")


if __name__ == '__main__':
    print("Redis Cache Performance Measurement")
    print(f"Target: {BASE_URL}")
    print(f"Redis: localhost:6379")

    # 캐시 초기화
    clear_cache()

    # 측정
    measure_endpoint("/stats/risk", "Risk Distribution Stats")
    measure_endpoint("/stats/age", "Age Distribution Stats")

    print("\n" + "=" * 60)
    print("✓ Performance measurement complete!")
    print("=" * 60)
