# System Architecture

Medical AI Serving Backend - 시스템 아키텍처

---

## 전체 시스템 구조

```
┌─────────────────────────────────────────────────────────────┐
│                        Client Layer                          │
│  (Browser, Mobile App, API Consumer)                        │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTPS
                       │ X-API-KEY
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                      API Gateway                             │
│                   (Railway Edge)                             │
│               SSL/TLS Termination                            │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                   Flask Application                          │
│            (Gunicorn: 2 Workers × 2 Threads)                 │
│  ┌──────────────────────────────────────────────────┐       │
│  │  API Layer                                       │       │
│  │  ├─ Health Check (/health)                       │       │
│  │  ├─ Records API (/records, /records/{id})        │       │
│  │  ├─ Stats API (/stats/risk, /stats/age)          │       │
│  │  └─ Simulate API (/simulate)                     │       │
│  └──────────────────────────────────────────────────┘       │
│  ┌──────────────────────────────────────────────────┐       │
│  │  Middleware Layer                                │       │
│  │  ├─ API Key Authentication                       │       │
│  │  ├─ CORS Handler                                 │       │
│  │  └─ Error Handler                                │       │
│  └──────────────────────────────────────────────────┘       │
│  ┌──────────────────────────────────────────────────┐       │
│  │  Business Logic Layer                            │       │
│  │  ├─ Risk Factor Calculation (simulate.py)        │       │
│  │  ├─ Cache Decorator (cache.py)                   │       │
│  │  └─ Data Validation                              │       │
│  └──────────────────────────────────────────────────┘       │
└─────┬────────────────────────────┬────────────────────┬─────┘
      │                            │                    │
      ↓                            ↓                    ↓
┌─────────────┐          ┌─────────────────┐   ┌──────────────┐
│   Redis     │          │     MySQL       │   │  In-Memory   │
│   Cache     │          │    Database     │   │  Compute     │
│             │          │                 │   │              │
│ TTL: 60s    │          │ 2 Tables        │   │ BMI Calc     │
│ Hit: 95%+   │          │ 7 Indexes       │   │ Risk Calc    │
│ Latency: 4ms│          │ 405 MB          │   │ Latency: 1ms │
└─────────────┘          └─────────────────┘   └──────────────┘
```

---

## API 요청 흐름

### 1. Simulate 엔드포인트 (In-Memory Calculation)

```
Client
  │
  │ POST /simulate + API Key + JSON Body
  ↓
API Gateway (Railway)
  │
  │ Auth Check
  ↓
Flask App (Gunicorn Worker)
  │
  │ Validate Input (age_group, gender, height, ...)
  ↓
Business Logic
  │
  ├─ Calculate BMI
  ├─ Check 7 Risk Factors
  │   ├─ Hypertension (BP≥140/90)
  │   ├─ Diabetes (FG≥126)
  │   ├─ High TC (TC≥240)
  │   ├─ High TG (TG≥200)
  │   ├─ Low HDL (HDL<40)
  │   ├─ Obesity (BMI≥25)
  │   └─ Smoking (Current)
  ├─ Count Risk Factors
  └─ Classify Risk Group
      └─ If diabetes: CHD_RISK_EQUIVALENT
      └─ Elif count≥2: MULTIPLE_RISK_FACTORS
      └─ Else: ZERO_TO_ONE_RISK_FACTOR
  │
  ↓
Response (12ms)
  │
  └─ JSON: {input, result, disclaimer}
```

**특징**:

- Database 접근 불필요 (Stateless)
- 초저지연 (12ms)
- 무한 확장 가능

---

### 2. Stats 엔드포인트 (Cached Aggregation)

```
Client
  │
  │ GET /stats/risk + API Key
  ↓
API Gateway
  │
  ↓
Flask App
  │
  │ @cached(ttl=60)
  ↓
Redis Check
  │
  ├─ Cache Hit (95%)
  │   └→ Return from Redis (4ms) ───────→ Client
  │
  └─ Cache Miss (5%)
      │
      ↓
    MySQL Query
      │
      │ SELECT risk_group, COUNT(*)
      │ FROM clean_risk_result
      │ GROUP BY risk_group
      │ -- (no invalid_flag filter: only valid records stored)
      ↓
    Aggregation (1.8s)
      │
      ├→ Save to Redis (TTL 60s)
      └→ Return to Client
```

**Cache Key 구조**:

```
cache:get_risk_stats:():{}
cache:get_age_stats:():{}
```

**최적화 효과**:

- Cache Hit: **4ms** (99.8% 개선)
- Cache Miss: 1,800ms → 다음 60초간 캐시 사용

---

### 3. Records 엔드포인트 (Paginated Query)

```
Client
  │
  │ GET /records?page=1&limit=20 + API Key
  ↓
Flask App
  │
  │ Validate: 1≤page, 1≤limit≤100
  ↓
MySQL Query
  │
  │ SELECT clean_risk_result.*
  │ FROM clean_risk_result
  │ JOIN raw_health_check
  │ ORDER BY id
  │ LIMIT 20 OFFSET 0
  │ -- (no invalid_flag filter: only valid records stored)
  ↓
Response (305ms)
  │
  └─ JSON: {data: [...], pagination: {...}}
```

**인덱스 사용**:

- PRIMARY KEY (id) → LIMIT/OFFSET 최적화
- idx_invalid_flag → WHERE 절 최적화

---

## 데이터 흐름

### ETL Pipeline

```
┌──────────────────┐
│  Raw CSV Data    │
│  (1,000,000 rows)│
└────────┬─────────┘
         │
         │ scripts/etl/load_raw.py
         │ Chunk: 10,000 rows
         │ Speed: 6,033 rows/sec
         ↓
┌──────────────────────────┐
│  raw_health_check Table  │
│  ┌────────────────────┐  │
│  │ id (PK)            │  │
│  │ age_group_code     │  │
│  │ gender_code        │  │
│  │ height, weight     │  │
│  │ blood_pressure     │  │
│  │ glucose, lipids    │  │
│  │ smoking_status     │  │
│  └────────────────────┘  │
└────────┬─────────────────┘
         │
         │ scripts/etl/process_clean.py
         │ Validation + Risk Calculation
         │ Speed: 594 rows/sec
         ↓
┌──────────────────────────────┐
│  clean_risk_result Table     │
│  ┌────────────────────────┐  │
│  │ id (PK)                │  │
│  │ raw_id (FK)            │  │
│  │ bmi (calculated)       │  │
│  │ flag_hypertension      │  │
│  │ flag_diabetes          │  │
│  │ flag_tc_high           │  │
│  │ flag_tg_high           │  │
│  │ flag_hdl_low           │  │
│  │ flag_obesity           │  │
│  │ flag_smoking           │  │
│  │ risk_factor_count      │  │
│  │ risk_group (ENUM)      │  │
│  │ invalid_flag           │  │
│  └────────────────────────┘  │
└──────────────────────────────┘
```

**데이터 품질**:

- Input: 1,000,000 rows
- Valid: 340,686 rows (34%)
- Invalid: 659,314 rows (66%) → 범위 초과, NULL 값

---

## 캐싱 아키텍처

### Cache-Aside Pattern

```
┌─────────────────────────────────────────┐
│           Application                    │
│                                         │
│  1. Check Cache ──────────┐            │
│         │                  │            │
│         │ Hit?             │ Miss       │
│         ↓                  ↓            │
│    Return Data      2. Query DB         │
│                          │              │
│                          ↓              │
│                     3. Store to Cache   │
│                          │              │
│                          ↓              │
│                     Return Data         │
└─────────────────────────────────────────┘
         │                   │
         ↓                   ↓
    ┌─────────┐         ┌─────────┐
    │  Redis  │         │  MySQL  │
    │  (4ms)  │         │ (1.8s)  │
    └─────────┘         └─────────┘
```

**TTL 전략**:

- Stats API: 60초 (통계는 실시간성 불필요)
- 60초마다 자동 갱신 → 항상 최신 데이터 보장

**Cache Invalidation**:

- ETL 실행 시: 수동 캐시 삭제
- TTL 만료 시: 자동 캐시 갱신

---

## 데이터베이스 스키마

### ER Diagram

```
┌─────────────────────────┐
│   raw_health_check      │
│─────────────────────────│
│ id (PK, BIGINT)         │◄───┐
│ reference_year          │    │
│ subscriber_id           │    │
│ province_code           │    │
│ gender_code             │    │
│ age_group_code ◄────────┼────┼── idx_age_group
│ height                  │    │
│ weight                  │    │
│ waist_circumference     │    │
│ systolic_bp ◄───────────┼────┼── idx_systolic_bp
│ diastolic_bp            │    │
│ fasting_glucose         │    │
│ total_cholesterol       │    │
│ triglycerides           │    │
│ hdl_cholesterol         │    │
│ ldl_cholesterol         │    │
│ smoking_status          │    │
│ created_at              │    │
└─────────────────────────┘    │
                               │ FK
┌─────────────────────────┐    │
│  clean_risk_result      │    │
│─────────────────────────│    │
│ id (PK, BIGINT)         │    │
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
│ risk_group ◄────────────┼────── idx_risk_group
│ invalid_flag ◄──────────┼────── idx_invalid_flag
│ rule_version            │
│ inference_time_ms       │
│ created_at              │
└─────────────────────────┘
        ↑
        └────── idx_composite_stats (risk_group, invalid_flag)
```

**인덱스 전략**:

1. **PRIMARY KEY**: 단일 레코드 조회
2. **idx_age_group**: 연령대 필터링
3. **idx_risk_group**: 위험군 필터링
4. **idx_invalid_flag**: 유효 데이터만 조회
5. **idx_composite_stats**: 통계 쿼리 최적화 (risk_group + invalid_flag)

---

## 보안 아키텍처

```
┌─────────────────────────────────────────┐
│             Client                       │
└──────────────┬──────────────────────────┘
               │
               │ 1. HTTPS (TLS 1.3)
               ↓
┌─────────────────────────────────────────┐
│        Railway Edge (SSL)                │
└──────────────┬──────────────────────────┘
               │
               │ 2. API Key Validation
               ↓
┌─────────────────────────────────────────┐
│      Flask Middleware                    │
│  ┌─────────────────────────────┐        │
│  │  require_api_key Decorator   │        │
│  │  - Header: X-API-KEY         │        │
│  │  - Compare with env var      │        │
│  │  - Return 401 if invalid     │        │
│  └─────────────────────────────┘        │
└──────────────┬──────────────────────────┘
               │
               │ 3. Input Validation
               ↓
┌─────────────────────────────────────────┐
│      Business Logic                      │
│  - Range validation                      │
│  - Type checking                         │
│  - SQL injection prevention (ORM)        │
└──────────────┬──────────────────────────┘
               │
               │ 4. Private Network
               ↓
┌─────────────────────────────────────────┐
│   Database (Railway Internal)            │
│   - mysql.railway.internal               │
│   - Not exposed to public                │
└─────────────────────────────────────────┘
```

**보안 레이어**:

1. **Transport**: HTTPS/TLS
2. **Authentication**: API Key
3. **Authorization**: Header-based
4. **Validation**: Input sanitization
5. **Network**: Private networking
6. **Database**: ORM (SQL injection 방지)

---

## 확장성 설계

### Horizontal Scaling

```
                    ┌─────────────┐
                    │ Load Balancer│
                    │   (Nginx)    │
                    └──────┬───────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ↓                ↓                ↓
    ┌─────────┐      ┌─────────┐      ┌─────────┐
    │ Flask 1 │      │ Flask 2 │      │ Flask 3 │
    │ 2W×2T   │      │ 2W×2T   │      │ 2W×2T   │
    └────┬────┘      └────┬────┘      └────┬────┘
         │                │                │
         └────────────────┼────────────────┘
                          │
              ┌───────────┴───────────┐
              │                       │
              ↓                       ↓
        ┌──────────┐            ┌──────────┐
        │  Redis   │            │  MySQL   │
        │ (Shared) │            │ (Shared) │
        └──────────┘            └──────────┘
```

**예상 처리량**:

- 1 Instance: 166 req/sec
- 3 Instances: 500 req/sec
- 10 Instances: 1,660 req/sec

---

## 모니터링 포인트

```
┌─────────────────────────────────────────┐
│            Monitoring                    │
│                                         │
│  ┌────────────────────────────┐        │
│  │  Application Metrics        │        │
│  │  - API Response Time (P95)  │        │
│  │  - Request Rate (req/s)     │        │
│  │  - Error Rate (%)           │        │
│  └────────────────────────────┘        │
│                                         │
│  ┌────────────────────────────┐        │
│  │  Cache Metrics              │        │
│  │  - Hit Rate (%)             │        │
│  │  - Miss Rate (%)            │        │
│  │  - Eviction Count           │        │
│  └────────────────────────────┘        │
│                                         │
│  ┌────────────────────────────┐        │
│  │  Database Metrics           │        │
│  │  - Query Latency (ms)       │        │
│  │  - Connection Pool Usage    │        │
│  │  - Slow Query Count         │        │
│  └────────────────────────────┘        │
│                                         │
│  ┌────────────────────────────┐        │
│  │  System Metrics             │        │
│  │  - CPU Usage (%)            │        │
│  │  - Memory Usage (%)         │        │
│  │  - Disk I/O                 │        │
│  └────────────────────────────┘        │
└─────────────────────────────────────────┘
```

---

**문서 버전**: 1.0
**최종 업데이트**: 2026-02-17
