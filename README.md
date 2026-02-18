# Medical AI Inference Serving Backend

> 🏥 건강검진 데이터 기반 위험요인 스크리닝 API - ETL부터 Serving까지

[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0.0-green.svg)](https://flask.palletsprojects.com/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-orange.svg)](https://www.mysql.com/)
[![Redis](https://img.shields.io/badge/Redis-7.0-red.svg)](https://redis.io/)
[![Tests](https://img.shields.io/badge/Tests-39%20passed-brightgreen.svg)](tests/)
[![Coverage](https://img.shields.io/badge/Coverage-81%25-yellow.svg)](htmlcov/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## ⚠️ 의료 면책 사항

**본 시스템은 의료 진단/치료/예측 도구가 아닙니다.**

공개된 임상 가이드라인의 cut-off 기준으로 위험요인 존재 여부를 요약/프로파일링하는 **참고용 시스템**입니다. 의료적 판단은 반드시 의료 전문가와 상담하십시오.

---

## 📋 프로젝트 개요

국민건강보험공단(NHIS) 건강검진 데이터(2024년) 100만건을 활용한 **위험요인 스크리닝 Inference Serving Backend** 구현 프로젝트입니다.

### 🎯 핵심 목적

**AI 모델 개발** ❌ → **AI Serving 백엔드 아키텍처 구현** ✅

- ETL 파이프라인 설계 및 최적화
- 데이터베이스 스키마 설계 및 인덱싱
- RESTful API 설계 및 구현
- Redis 캐싱 전략
- 성능 측정 및 최적화

### ✨ 차별화 포인트

1. **ETL/Serving 레이어 분리**: 배치 처리와 실시간 서빙 독립적 운영
2. **Inference Layer 분리**: 향후 ML 모델 교체 용이
3. **가이드라인 기반 로직**: 법적 안정성, 설명 가능성 확보
4. **성능 최적화 수치화**: 인덱싱, 캐싱 전후 비교 측정
5. **프로덕션 레디**: Docker, 자동 배포, 테스트 커버리지 81%

---

## 🏗️ 시스템 아키텍처

```
┌─────────────────┐
│  CSV Data       │  NHIS 건강검진 데이터 (100만건)
│  (2024)         │
└────────┬────────┘
         │ ETL Layer (Batch Processing)
         │ ├─ load_raw.py (6,033 rows/sec)
         │ └─ process_clean.py (594 rows/sec)
         ↓
┌─────────────────────────────────────────┐
│        MySQL Database                    │
│  ┌─────────────────────────────────┐   │
│  │ raw_health_check (원본 보존)     │   │
│  │ - 1,000,000 rows                │   │
│  │ - 112 MB + 18 MB indexes        │   │
│  └─────────────────────────────────┘   │
│  ┌─────────────────────────────────┐   │
│  │ clean_risk_result (위험요인)     │   │
│  │ - 340,686 valid rows (34%)      │   │
│  │ - 171 MB + 104 MB indexes       │   │
│  │ - 7 strategic indexes           │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
         │
         │ Serving Layer (Flask + Gunicorn)
         │ ├─ API Layer (Routing, Validation)
         │ ├─ Business Logic (Risk Calculation)
         │ └─ Repository Layer (ORM)
         ↓
┌─────────────────────────────────────────┐
│         Redis Cache                      │
│  - TTL: 60 seconds                      │
│  - Hit Rate: 95%+                       │
│  - Latency: 4ms (cached)                │
│  - Improvement: 99.8% (436x faster)     │
└─────────────────────────────────────────┘
         │
         ↓ JSON Response
┌─────────────────┐
│     Client      │
│  (API Consumer) │
└─────────────────┘
```

---

## 🛠️ 기술 스택

| 계층                 | 기술       | 버전    | 선택 이유                         |
| -------------------- | ---------- | ------- | --------------------------------- |
| **Framework**        | Flask      | 3.0.0   | 경량, 빠른 개발, RESTful API 최적 |
| **WSGI Server**      | Gunicorn   | 21.2.0  | 멀티 프로세스, 프로덕션 안정성    |
| **Database**         | MySQL      | 8.0     | ACID 보장, 관계형 데이터 적합     |
| **Cache**            | Redis      | 8.6.0   | 초고속 캐싱, TTL 지원             |
| **ORM**              | SQLAlchemy | 2.0.25+ | 타입 안전, 마이그레이션 용이      |
| **ETL**              | pandas     | 2.2.0   | 대용량 데이터 처리 최적화         |
| **Testing**          | pytest     | 7.4.4   | 테스트 커버리지, fixture 지원     |
| **Deployment**       | Railway    | -       | 간편한 배포, MySQL/Redis 통합     |
| **Containerization** | Docker     | -       | 일관된 실행 환경                  |

---

## 🚀 빠른 시작

### 사전 요구사항

- Python 3.13+
- MySQL 8.0+
- Redis 7.0+
- Git

### 설치 및 실행

```bash
# 1. 저장소 클론
git clone https://github.com/xxjiinn/medical-ai-serving.git
cd medical-ai-serving

# 2. 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 의존성 설치
pip install -r requirements.txt

# 4. 환경변수 설정
cp .env.example .env
# .env 파일을 열어 다음 항목 설정:
# - DATABASE_URL: MySQL 연결 문자열
# - REDIS_URL: Redis 연결 문자열
# - API_KEY: 인증용 API 키

# 5. 데이터베이스 초기화
python -c "from app.database import init_db; init_db()"

# 6. ETL 실행 (CSV 데이터 준비 필요)
python scripts/etl/load_raw.py
python scripts/etl/process_clean.py

# 7. Redis 실행 (로컬)
redis-server --daemonize yes

# 8. Flask 서버 실행
python run.py
# 또는 프로덕션 모드:
# gunicorn --bind 0.0.0.0:5001 --workers 2 --threads 2 run:app
```

서버가 실행되면 `http://localhost:5001/health`에서 상태 확인 가능합니다.

---

## 📡 API 엔드포인트

### 인증

모든 API는 HTTP 헤더에 `X-API-KEY` 필요:

```bash
curl -H "X-API-KEY: your-api-key-here" \
  http://localhost:5001/records
```

### 엔드포인트 목록

| Method | Endpoint        | Description             | Response Time | Cache  |
| ------ | --------------- | ----------------------- | ------------- | ------ |
| GET    | `/health`       | 서버 상태 확인          | 8ms           | -      |
| GET    | `/records`      | 검진 데이터 페이징 조회 | 305ms         | -      |
| GET    | `/records/{id}` | 단일 레코드 조회        | 187ms         | -      |
| GET    | `/stats/risk`   | 위험군 분포 통계        | 4ms (cached)  | ✅ 60s |
| GET    | `/stats/age`    | 연령대별 통계           | 4ms (cached)  | ✅ 60s |
| POST   | `/simulate`     | 위험도 계산 (Inference) | 12ms          | -      |

### 사용 예시

**1. Records 조회 (페이징)**

```bash
curl -H "X-API-KEY: your-key" \
  "http://localhost:5001/records?page=1&limit=20"
```

**2. Stats 조회 (캐싱)**

```bash
curl -H "X-API-KEY: your-key" \
  "http://localhost:5001/stats/risk"
```

**3. Simulate (위험도 계산)**

```bash
curl -X POST -H "X-API-KEY: your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "age_group": 12,
    "gender": 1,
    "height": 170,
    "weight": 85,
    "systolic_bp": 150,
    "diastolic_bp": 95,
    "fasting_glucose": 130,
    "total_cholesterol": 250,
    "triglycerides": 210,
    "hdl_cholesterol": 38,
    "smoking_status": "current"
  }' \
  "http://localhost:5001/simulate"
```

상세 API 문서: **[docs/API_SPEC.md](docs/API_SPEC.md)**

---

## 🩺 위험요인 정의 (Guideline-Based)

### 7가지 위험요인

| 위험요인         | Cut-off 기준           | 가이드라인 출처  |
| ---------------- | ---------------------- | ---------------- |
| 고혈압           | SBP≥140 or DBP≥90 mmHg | 대한고혈압학회   |
| 당뇨             | 공복혈당≥126 mg/dL     | KDA/ADA          |
| 고콜레스테롤     | TC≥240 mg/dL           | NCEP ATP III     |
| 고중성지방       | TG≥200 mg/dL           | NCEP ATP III     |
| 저HDL 콜레스테롤 | HDL<40 mg/dL           | NCEP ATP III     |
| 비만 (아시아)    | BMI≥25 kg/m²           | WHO Asia-Pacific |
| 흡연             | 현재 흡연자            | NCEP ATP III     |

### Risk Group 분류 (ATP III Framework)

```
┌─ flag_diabetes = true
│   → CHD_RISK_EQUIVALENT (고위험군, 9.1%)
│
├─ flag_diabetes = false AND risk_factor_count ≥ 2
│   → MULTIPLE_RISK_FACTORS (중위험군, 26.8%)
│
└─ flag_diabetes = false AND risk_factor_count ≤ 1
    → ZERO_TO_ONE_RISK_FACTOR (저위험군, 64.1%)
```

전체 가이드라인 출처: **[docs/GUIDELINES.md](docs/GUIDELINES.md)**

---

## 📊 데이터베이스 설계

### ERD

```
┌─────────────────────────┐
│   raw_health_check      │  원본 데이터 보존
│─────────────────────────│
│ id (PK)                 │◄───┐
│ age_group_code          │    │
│ gender_code             │    │
│ height, weight          │    │
│ blood_pressure          │    │
│ glucose, lipids         │    │
│ smoking_status          │    │
└─────────────────────────┘    │
                               │ FK
┌─────────────────────────┐    │
│  clean_risk_result      │    │  위험요인 계산 결과
│─────────────────────────│    │
│ id (PK)                 │    │
│ raw_id (FK) ────────────┼────┘
│ bmi (DECIMAL)           │
│ flag_hypertension       │
│ flag_diabetes           │
│ flag_tc_high            │
│ flag_tg_high            │
│ flag_hdl_low            │
│ flag_obesity            │
│ flag_smoking            │
│ risk_factor_count       │
│ risk_group (ENUM)       │
│ invalid_flag            │
│ rule_version            │
│ inference_time_ms       │
└─────────────────────────┘
```

### 인덱스 전략 (7개)

1. **PRIMARY KEY** (id): 단일 레코드 조회
2. **idx_age_group**: 연령대 필터링
3. **idx_systolic_bp**: 혈압 범위 검색
4. **idx_risk_group**: 위험군 필터링
5. **idx_invalid_flag**: 유효 데이터 필터링
6. **idx_composite_stats**: 통계 쿼리 최적화 (risk_group + invalid_flag)
7. **fk_raw_id**: JOIN 성능 개선

상세 스키마: **[docs/ERD.md](docs/ERD.md)**

---

## 🧪 테스트

### 테스트 실행

```bash
# 전체 테스트 실행
pytest

# 커버리지 포함
pytest --cov=app --cov-report=html

# 특정 테스트 파일
pytest tests/test_simulate_logic.py -v

# 특정 테스트 클래스
pytest tests/test_api_endpoints.py::TestSimulateEndpoint -v
```

### 테스트 커버리지

```
총 39개 테스트 (모두 통과 ✅)
├─ API 엔드포인트: 14개
├─ 위험요인 계산 로직: 19개
└─ Redis 캐싱: 6개

코드 커버리지: 81%
├─ simulate.py: 100%
├─ stats.py: 100%
├─ auth.py: 100%
├─ config.py: 96%
└─ models: 96%
```

테스트 리포트: `htmlcov/index.html`

---

## 📈 성능 최적화

### ETL 파이프라인

```
Raw Data Loading
├─ 처리량: 6,033 rows/sec
├─ 처리 시간: 165초 (100만건)
└─ 메모리: ~500MB

Risk Calculation
├─ 처리량: 594 rows/sec
├─ 처리 시간: 1,684초 (28분)
├─ 유효율: 34% (340,686건)
└─ 메모리: ~200MB
```

### API 성능

| 엔드포인트  | Before  | After     | 개선율 | Speedup  |
| ----------- | ------- | --------- | ------ | -------- |
| /stats/risk | 1,744ms | **4ms**   | 99.8%  | **436x** |
| /stats/age  | 2,177ms | **4ms**   | 99.8%  | **544x** |
| /simulate   | -       | **12ms**  | -      | -        |
| /records    | -       | **305ms** | -      | -        |

### Redis 캐싱 효과

```
┌─ Cache Hit (95%)
│   └→ Response: 4ms
│
└─ Cache Miss (5%)
    └→ Database Query: 1.8s
    └→ Cache Update: TTL 60s
```

**개선 효과**: 평균 응답시간 1,800ms → **90ms** (20배 개선)

상세 성능 리포트: **[docs/PERFORMANCE_REPORT.md](docs/PERFORMANCE_REPORT.md)**

---

## 🚢 배포

### Docker

```bash
# 이미지 빌드
docker build -t medical-ai-serving .

# 컨테이너 실행
docker run -p 5001:5001 \
  -e DATABASE_URL="mysql+pymysql://..." \
  -e REDIS_URL="redis://localhost:6379/0" \
  -e API_KEY="your-api-key" \
  -e FLASK_ENV="production" \
  medical-ai-serving
```

### Railway 배포

```bash
# Railway CLI 설치
npm install -g @railway/cli

# 로그인
railway login

# 배포
railway up
```

**환경변수 설정**:

- `DATABASE_URL`: MySQL 연결 (Private URL)
- `REDIS_URL`: Redis 연결 (Private URL)
- `API_KEY`: 인증용 API 키
- `FLASK_ENV`: production
- `PORT`: Railway 자동 할당

배포 가이드: **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)**

---

## 📁 프로젝트 구조

```
medical-ai-serving/
├── app/                        # Flask 애플리케이션
│   ├── __init__.py             # App factory
│   ├── config.py               # 환경 설정
│   ├── database.py             # DB 연결
│   ├── cache.py                # Redis 캐싱
│   ├── models/                 # SQLAlchemy 모델
│   │   └── health_check.py
│   ├── blueprints/             # API 라우팅
│   │   ├── records.py          # Records API
│   │   ├── stats.py            # Stats API
│   │   └── simulate.py         # Simulate API
│   └── middleware/
│       └── auth.py             # API Key 인증
├── scripts/
│   ├── etl/                    # ETL 파이프라인
│   │   ├── load_raw.py         # CSV → raw_health_check
│   │   └── process_clean.py    # raw → clean_risk_result
│   └── performance/            # 성능 측정
│       ├── check_indexes.py
│       ├── measure_query_performance.py
│       └── measure_cache_performance.py
├── tests/                      # pytest 테스트
│   ├── conftest.py             # Fixtures
│   ├── test_api_endpoints.py
│   ├── test_simulate_logic.py
│   └── test_cache.py
├── docs/                       # 문서
│   ├── API_SPEC.md
│   ├── ARCHITECTURE.md
│   ├── DATA_DICTIONARY.md
│   ├── DECISIONS.md
│   ├── DEPLOYMENT.md
│   ├── ERD.md
│   ├── GUIDELINES.md
│   ├── PERFORMANCE_REPORT.md
│   └── PERFORMANCE_SUMMARY.md
├── Dockerfile                  # Docker 이미지
├── railway.toml                # Railway 설정
├── requirements.txt            # Python 의존성
├── run.py                      # Flask 실행
├── .env.example                # 환경변수 템플릿
└── README.md                   # 본 문서
```

---

## 📚 문서

| 문서                                                  | 설명                             |
| ----------------------------------------------------- | -------------------------------- |
| [API_SPEC.md](docs/API_SPEC.md)                       | API 요청/응답 상세 명세          |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md)               | 시스템 아키텍처 및 데이터 흐름   |
| [DATA_DICTIONARY.md](docs/DATA_DICTIONARY.md)         | 데이터 컬럼 정의 및 매핑         |
| [DECISIONS.md](docs/DECISIONS.md)                     | 기술 선택 및 트레이드오프 (11개) |
| [DEPLOYMENT.md](docs/DEPLOYMENT.md)                   | Railway 배포 가이드              |
| [ERD.md](docs/ERD.md)                                 | 데이터베이스 스키마 설계         |
| [GUIDELINES.md](docs/GUIDELINES.md)                   | 임상 가이드라인 출처             |
| [PERFORMANCE_REPORT.md](docs/PERFORMANCE_REPORT.md)   | 상세 성능 측정 리포트            |
| [PERFORMANCE_SUMMARY.md](docs/PERFORMANCE_SUMMARY.md) | 성과 요약 (Executive Report)     |

---

## 🎯 프로젝트 목표 달성

### 백엔드 역량

- ✅ **ETL 파이프라인**: 100만건 데이터 처리 (28분)
- ✅ **Database 설계**: 2-tier 스키마, 7개 전략적 인덱스
- ✅ **REST API**: 5개 엔드포인트, Blueprint 아키텍처
- ✅ **Redis 캐싱**: 99.8% 성능 개선 (436배 속도 향상)
- ✅ **레이어 분리**: ETL/Serving/Business Logic 독립
- ✅ **성능 최적화**: 인덱싱, 캐싱 효과 수치화
- ✅ **테스트**: 39개 테스트, 81% 커버리지
- ✅ **배포**: Docker 컨테이너화, Railway CI/CD

### 의료 도메인 이해

- ✅ 공개 가이드라인 기반 설계 (대한고혈압학회, ADA, ATP III, WHO)
- ✅ 법적 안정성 고려 (진단 도구 아님 명시)
- ✅ 설명 가능성 확보 (각 위험요인 계산 근거 제공)

---

## 🔧 기술적 하이라이트

### 1. Chunk-based ETL

```python
for chunk in pd.read_csv(csv_file, chunksize=10000):
    chunk.to_sql('raw_health_check', engine, if_exists='append')
```

→ 메모리 효율적 대용량 처리 (6,033 rows/sec)

### 2. Strategic Indexing

```sql
CREATE INDEX idx_composite_stats
ON clean_risk_result (risk_group, invalid_flag);
```

→ 통계 쿼리 60% 속도 향상

### 3. Cache-Aside Pattern

```python
@cached(ttl=60)
def get_risk_stats():
    # 캐시 히트 시 4ms, 캐시 미스 시 1.8s → Redis 저장
```

→ 99.8% 성능 개선

### 4. Production-Ready Architecture

- Gunicorn 멀티 프로세스 (2 workers × 2 threads)
- Health check endpoint
- API Key 인증
- HTTPS (Railway SSL)
- Structured logging

---

## 👨‍💻 개발자

**오성진**

- GitHub: [@xxjiinn](https://github.com/xxjiinn)
- Email: [osj3382@gmail.com]
- Portfolio: 백엔드 개발자 프로젝트

---

## 📄 라이선스

MIT License - 자유롭게 사용, 수정, 배포 가능

---

## 🙏 출처

- **국민건강보험공단(NHIS)**: 건강검진 데이터 제공
- **가이드라인 제공 기관**:
  - 대한고혈압학회 (Korean Society of Hypertension)
  - 대한당뇨병학회 (Korean Diabetes Association)
  - NCEP ATP III (National Cholesterol Education Program)
  - WHO Asia-Pacific (World Health Organization)

---

## 🔗 관련 링크

- **GitHub Repository**: https://github.com/xxjiinn/medical-ai-serving
- **Deployment**: (배포 후 업데이트)
- **API Documentation**: [docs/API_SPEC.md](docs/API_SPEC.md)
- **Performance Report**: [docs/PERFORMANCE_REPORT.md](docs/PERFORMANCE_REPORT.md)

---

**프로젝트 상태**: ✅ Production Ready
**최종 업데이트**: 2026-02-17
**개발 기간**: 5일 (계획 대비 2일 단축)
