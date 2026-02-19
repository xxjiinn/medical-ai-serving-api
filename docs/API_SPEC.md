# API 명세서 (API Specification)

작성일: 2026-02-17
Base URL: `http://localhost:5001` (로컬), `https://[railway-domain]` (배포)

---

## 인증 (Authentication)

모든 API 요청은 `X-API-KEY` 헤더 필요

```bash
curl -H "X-API-KEY: your-secret-key" http://localhost:5001/records
```

**응답 (인증 실패)**:
```json
{
  "error": "Unauthorized",
  "message": "Invalid or missing API key"
}
```
**HTTP 상태**: 401 Unauthorized

---

## 1. GET /records

### 설명
검진 데이터 목록 조회 (페이징 지원)

### Query Parameters

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|----------|------|------|--------|------|
| page | int | ❌ | 1 | 페이지 번호 (1부터 시작) |
| limit | int | ❌ | 20 | 페이지당 항목 수 (최대 100) |
| age_group | int | ❌ | - | 연령대 필터 (5~18, 25-29세~90세 초과) |
| gender | int | ❌ | - | 성별 필터 (1: 남성, 2: 여성) |
| risk_group | string | ❌ | - | 위험군 필터 (CHD_RISK_EQUIVALENT, MULTIPLE_RISK_FACTORS, ZERO_TO_ONE_RISK_FACTOR) |

### 요청 예시

```bash
# 기본 조회
GET /records

# 페이징
GET /records?page=2&limit=50

# 필터 (60세, 다중 위험요인)
GET /records?age_group=12&risk_group=MULTIPLE_RISK_FACTORS
```

### 응답 (성공)

```json
{
  "data": [
    {
      "id": 1,
      "age_group": 12,
      "gender": 1,
      "bmi": 27.3,
      "risk_factor_count": 3,
      "risk_group": "MULTIPLE_RISK_FACTORS",
      "flags": {
        "hypertension": true,
        "diabetes": false,
        "high_tc": true,
        "high_tg": false,
        "low_hdl": false,
        "obesity": true,
        "smoking": false
      },
      "created_at": "2026-02-17T10:30:00Z"
    },
    {
      "id": 2,
      "age_group": 10,
      "gender": 2,
      "bmi": 22.1,
      "risk_factor_count": 0,
      "risk_group": "ZERO_TO_ONE_RISK_FACTOR",
      "flags": {
        "hypertension": false,
        "diabetes": false,
        "high_tc": false,
        "high_tg": false,
        "low_hdl": false,
        "obesity": false,
        "smoking": false
      },
      "created_at": "2026-02-17T10:31:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total_items": 340686,
    "total_pages": 17035
  }
}
```

**HTTP 상태**: 200 OK

### 응답 (에러)

```json
{
  "error": "Bad Request",
  "message": "Invalid age_group. Must be between 5 and 18."
}
```
**HTTP 상태**: 400 Bad Request

---

## 2. GET /records/{id}

### 설명
단일 검진 데이터 조회

### Path Parameters

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| id | int | ✅ | 레코드 ID |

### 요청 예시

```bash
GET /records/123
```

### 응답 (성공)

```json
{
  "id": 123,
  "age_group": 12,
  "age_display": "60-64세",
  "gender": 1,
  "gender_display": "남성",
  "height": 170,
  "weight": 80,
  "bmi": 27.7,
  "systolic_bp": 145,
  "diastolic_bp": 92,
  "fasting_glucose": 110,
  "total_cholesterol": 250,
  "triglycerides": 180,
  "hdl_cholesterol": 38,
  "smoking_status": "current",
  "risk_factor_count": 4,
  "risk_group": "MULTIPLE_RISK_FACTORS",
  "flags": {
    "hypertension": true,
    "diabetes": false,
    "high_tc": true,
    "high_tg": false,
    "low_hdl": true,
    "obesity": true,
    "smoking": true
  },
  "rule_version": "guideline-v1",
  "inference_time_ms": 2,
  "created_at": "2026-02-17T10:30:00Z"
}
```

**HTTP 상태**: 200 OK

### 응답 (에러)

```json
{
  "error": "Not Found",
  "message": "Record with id 123 not found"
}
```
**HTTP 상태**: 404 Not Found

---

## 3. GET /stats/risk

### 설명
위험군 분포 통계 (캐시 적용)

### Query Parameters
없음

### 요청 예시

```bash
GET /stats/risk
```

### 응답 (성공)

```json
{
  "risk_distribution": {
    "ZERO_TO_ONE_RISK_FACTOR": {
      "count": 218365,
      "percentage": 64.1
    },
    "MULTIPLE_RISK_FACTORS": {
      "count": 91280,
      "percentage": 26.8
    },
    "CHD_RISK_EQUIVALENT": {
      "count": 31041,
      "percentage": 9.1
    }
  },
  "total_records": 1000000,
  "valid_records": 340686,
  "invalid_records": 659314
}
```

**HTTP 상태**: 200 OK

**캐싱**:
- TTL: 60초
- Redis Key: `stats:risk`

---

## 4. GET /stats/age

### 설명
연령대별 통계 (캐시 적용). clean_risk_result의 유효한 레코드만 포함.

### Query Parameters
없음

### 요청 예시

```bash
GET /stats/age
```

### 응답 (성공)

```json
{
  "age_distribution": [
    {
      "age_group": 5,
      "age_display": "25-29세",
      "count": 5906,
      "percentage": 1.7,
      "avg_risk_factor_count": 1.1,
      "high_risk_count": 412
    },
    {
      "age_group": 9,
      "age_display": "45-49세",
      "count": 58677,
      "percentage": 17.2,
      "avg_risk_factor_count": 1.8,
      "high_risk_count": 4521
    },
    {
      "age_group": 12,
      "age_display": "60-64세",
      "count": 34312,
      "percentage": 10.1,
      "avg_risk_factor_count": 2.3,
      "high_risk_count": 5678
    },
    {
      "age_group": 18,
      "age_display": "90세 초과",
      "count": 2292,
      "percentage": 0.7,
      "avg_risk_factor_count": 2.8,
      "high_risk_count": 891
    }
  ],
  "total_records": 340686
}
```

**HTTP 상태**: 200 OK

**캐싱**:
- TTL: 60초
- Redis Key: `stats:age`

---

## 5. POST /simulate

### 설명
단일 환자 위험요인 계산 (Inference API)

### Request Body

| 필드 | 타입 | 필수 | 설명 | 범위 |
|------|------|------|------|------|
| age_group | int | ✅ | 연령대 코드 (5=25-29세, ..., 18=90세 초과) | 5~18 |
| gender | int | ✅ | 성별 | 1 (남), 2 (여) |
| height | int | ✅ | 신장 (cm) | 140~200 |
| weight | int | ✅ | 체중 (kg) | 30~150 |
| systolic_bp | int | ✅ | 수축기 혈압 (mmHg) | 70~250 |
| diastolic_bp | int | ✅ | 이완기 혈압 (mmHg) | 40~150 |
| fasting_glucose | int | ✅ | 공복혈당 (mg/dL) | 50~400 |
| total_cholesterol | int | ✅ | 총콜레스테롤 (mg/dL) | 100~400 |
| triglycerides | int | ✅ | 중성지방 (mg/dL) | 30~500 |
| hdl_cholesterol | int | ✅ | HDL (mg/dL) | 20~100 |
| smoking_status | string | ✅ | 흡연 상태 | "never", "former", "current" |

### 요청 예시

```bash
POST /simulate
Content-Type: application/json
X-API-KEY: your-secret-key

{
  "age_group": 12,
  "gender": 1,
  "height": 170,
  "weight": 85,
  "systolic_bp": 152,
  "diastolic_bp": 96,
  "fasting_glucose": 131,
  "total_cholesterol": 255,
  "triglycerides": 210,
  "hdl_cholesterol": 38,
  "smoking_status": "current"
}
```

### 응답 (성공)

```json
{
  "input": {
    "age_group": 12,
    "age_display": "60-64세",
    "gender": 1,
    "gender_display": "남성",
    "bmi": 29.4
  },
  "result": {
    "risk_factor_count": 7,
    "risk_group": "CHD_RISK_EQUIVALENT",
    "flags": {
      "hypertension": true,
      "diabetes": true,
      "high_total_cholesterol": true,
      "high_triglycerides": true,
      "low_hdl": true,
      "obesity_asia": true,
      "smoking": true
    },
    "explanations": [
      "Hypertension: SBP≥140 or DBP≥90 (152/96)",
      "Diabetes: fasting glucose≥126 (131)",
      "High TC: total cholesterol≥240 (255)",
      "High TG: triglycerides≥200 (210)",
      "Low HDL: hdl<40 (38)",
      "Obesity(Asia): BMI≥25 (29.4)",
      "Smoking: current smoker"
    ],
    "rule_version": "guideline-v1",
    "inference_time_ms": 3
  },
  "disclaimer": "This is NOT a diagnostic tool. Consult medical professionals for any health concerns."
}
```

**HTTP 상태**: 200 OK

### 응답 (에러 - 유효성 검증 실패)

```json
{
  "error": "Validation Error",
  "message": "Invalid input data",
  "details": {
    "systolic_bp": "Must be between 70 and 250",
    "fasting_glucose": "Must be between 50 and 400"
  }
}
```
**HTTP 상태**: 400 Bad Request

### 응답 (에러 - 생물학적 범위 이상)

```json
{
  "error": "Invalid Data",
  "message": "Input values are outside biological range",
  "details": {
    "systolic_bp": 280,
    "message": "Systolic BP > 250 is not realistic"
  }
}
```
**HTTP 상태**: 422 Unprocessable Entity

---

## 공통 에러 응답

### 400 Bad Request
요청 데이터 형식 오류

```json
{
  "error": "Bad Request",
  "message": "Invalid JSON format"
}
```

### 401 Unauthorized
API Key 누락 또는 잘못됨

```json
{
  "error": "Unauthorized",
  "message": "Invalid or missing API key"
}
```

### 404 Not Found
리소스 없음

```json
{
  "error": "Not Found",
  "message": "Endpoint not found"
}
```

### 500 Internal Server Error
서버 오류

```json
{
  "error": "Internal Server Error",
  "message": "An unexpected error occurred",
  "request_id": "req_abc123"
}
```

---

## 응답 헤더

모든 응답에 포함:

```
Content-Type: application/json
X-Request-ID: req_abc123
X-Response-Time: 24ms
```

---

## Rate Limiting (향후 추가 가능)

현재 미구현, 추후 필요 시 추가:
- 제한: 100 requests/min/key
- 헤더: `X-RateLimit-Remaining`, `X-RateLimit-Reset`

---

## 테스트 가이드

### Postman Collection
```json
{
  "info": {
    "name": "Medical AI API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Get Records",
      "request": {
        "method": "GET",
        "header": [
          {"key": "X-API-KEY", "value": "{{api_key}}"}
        ],
        "url": "{{base_url}}/records?page=1&limit=20"
      }
    }
    // ... 나머지 엔드포인트
  ]
}
```

### curl 테스트

```bash
# 환경변수 설정
export API_KEY="your-secret-key"
export BASE_URL="http://localhost:5001"

# 1. 목록 조회
curl -H "X-API-KEY: $API_KEY" "$BASE_URL/records?page=1&limit=5"

# 2. 단건 조회
curl -H "X-API-KEY: $API_KEY" "$BASE_URL/records/1"

# 3. 통계 조회
curl -H "X-API-KEY: $API_KEY" "$BASE_URL/stats/risk"
curl -H "X-API-KEY: $API_KEY" "$BASE_URL/stats/age"

# 4. 시뮬레이션
curl -X POST "$BASE_URL/simulate" \
  -H "X-API-KEY: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
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
  }'
```

---

**마지막 업데이트**: 2026-02-17
