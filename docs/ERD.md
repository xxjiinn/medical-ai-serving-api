# Entity-Relationship Diagram (ERD)

작성일: 2026-02-17
DBMS: MySQL 8.0+

---

## 설계 원칙

### 1. 2계층 구조 (Two-Tier Architecture)

```
raw_health_check (원본 보존)
    ↓ 1:1
clean_risk_result (판정 결과)
```

**Why 2-Tier?**

- **raw**: CSV 원본 데이터 보존 → 재처리 가능
- **clean**: 위험요인 판정 결과 저장 → API 서빙 최적화

### 2. 데이터 무결성

- Foreign Key: `clean_risk_result.raw_id` → `raw_health_check.id`
- Cascade: raw 삭제 시 clean도 삭제

### 3. 인덱스 전략

- **조회 빈도** 기준 인덱스 추가
- 통계 쿼리 최적화 목표

---

## 테이블 1: raw_health_check

### 목적

CSV 원본 데이터 보존 (최소 처리만 적용)

### 스키마

```sql
CREATE TABLE raw_health_check (
    -- Primary Key
    id                   BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    -- 기본 정보
    reference_year       SMALLINT UNSIGNED NOT NULL DEFAULT 2024,
    subscriber_id        VARCHAR(20),
    province_code        TINYINT UNSIGNED,
    gender_code          TINYINT UNSIGNED NOT NULL,  -- 1: 남, 2: 여
    age_group_code       TINYINT UNSIGNED NOT NULL,  -- 5~18

    -- 신체 계측
    height               SMALLINT UNSIGNED,          -- cm (5cm 단위)
    weight               SMALLINT UNSIGNED,          -- kg (5kg 단위)
    waist_circumference  SMALLINT UNSIGNED,          -- cm

    -- 혈압
    systolic_bp          SMALLINT UNSIGNED,          -- mmHg
    diastolic_bp         SMALLINT UNSIGNED,          -- mmHg

    -- 혈당
    fasting_glucose      SMALLINT UNSIGNED,          -- mg/dL

    -- 지질
    total_cholesterol    SMALLINT UNSIGNED,          -- mg/dL
    triglycerides        SMALLINT UNSIGNED,          -- mg/dL
    hdl_cholesterol      SMALLINT UNSIGNED,          -- mg/dL
    ldl_cholesterol      SMALLINT UNSIGNED,          -- mg/dL (참고용)

    -- 생활습관
    smoking_status       TINYINT UNSIGNED,           -- 1: 비흡연, 2: 과거, 3: 현재

    -- 메타데이터
    created_at           TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- 인덱스 (조회 성능)
    INDEX idx_age_group (age_group_code),
    INDEX idx_gender (gender_code),
    INDEX idx_systolic_bp (systolic_bp)

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### 컬럼 설명

| 컬럼                | 타입            | NULL | 설명                 | 비고          |
| ------------------- | --------------- | ---- | -------------------- | ------------- |
| id                  | BIGINT UNSIGNED | ❌   | 자동 증가 PK         | 1~300,000     |
| reference_year      | SMALLINT        | ❌   | 2024 고정            |               |
| subscriber_id       | VARCHAR(20)     | ✅   | 가입자 ID (비식별화) | Surrogate key |
| province_code       | TINYINT         | ✅   | 시도 코드            | 11~50         |
| gender_code         | TINYINT         | ❌   | 1=남, 2=여           |               |
| age_group_code      | TINYINT         | ❌   | 5~18 (25-29세~90세+) |               |
| height              | SMALLINT        | ✅   | 신장 (cm)            | 5cm 단위      |
| weight              | SMALLINT        | ✅   | 체중 (kg)            | 5kg 단위      |
| waist_circumference | SMALLINT        | ✅   | 허리둘레 (cm)        |               |
| systolic_bp         | SMALLINT        | ✅   | 수축기 혈압          |               |
| diastolic_bp        | SMALLINT        | ✅   | 이완기 혈압          |               |
| fasting_glucose     | SMALLINT        | ✅   | 공복혈당             |               |
| total_cholesterol   | SMALLINT        | ✅   | 총콜레스테롤         |               |
| triglycerides       | SMALLINT        | ✅   | 중성지방             |               |
| hdl_cholesterol     | SMALLINT        | ✅   | HDL                  |               |
| ldl_cholesterol     | SMALLINT        | ✅   | LDL (참고용)         |               |
| smoking_status      | TINYINT         | ✅   | 1~3                  |               |
| created_at          | TIMESTAMP       | ❌   | 적재 시각            |               |

### 데이터 품질

- NULL 허용: 결측값 그대로 저장
- 이상치: 그대로 저장 (clean에서 필터링)
- 재현성: ETL 재실행 가능

---

## 테이블 2: clean_risk_result

### 목적

위험요인 판정 결과 저장 (API 서빙용)

### 스키마

```sql
CREATE TABLE clean_risk_result (
    -- Primary Key
    id                   BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    -- Foreign Key (raw_health_check)
    raw_id               BIGINT UNSIGNED NOT NULL,

    -- 계산 필드
    bmi                  DECIMAL(4, 1),              -- BMI = weight / (height/100)^2

    -- 위험요인 Flags (Boolean)
    flag_hypertension    BOOLEAN NOT NULL DEFAULT FALSE,
    flag_diabetes        BOOLEAN NOT NULL DEFAULT FALSE,
    flag_tc_high         BOOLEAN NOT NULL DEFAULT FALSE,
    flag_tg_high         BOOLEAN NOT NULL DEFAULT FALSE,
    flag_hdl_low         BOOLEAN NOT NULL DEFAULT FALSE,
    flag_obesity         BOOLEAN NOT NULL DEFAULT FALSE,
    flag_smoking         BOOLEAN NOT NULL DEFAULT FALSE,

    -- 집계 필드
    risk_factor_count    TINYINT UNSIGNED NOT NULL,  -- 0~7
    risk_group           ENUM(
                           'ZERO_TO_ONE_RISK_FACTOR',
                           'MULTIPLE_RISK_FACTORS',
                           'CHD_RISK_EQUIVALENT'
                         ) NOT NULL,

    -- 메타데이터
    rule_version         VARCHAR(20) NOT NULL DEFAULT 'guideline-v1',
    inference_time_ms    SMALLINT UNSIGNED,          -- 추론 소요 시간
    invalid_flag         BOOLEAN NOT NULL DEFAULT FALSE,  -- 이상치/결측으로 판정 불가
    created_at           TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Foreign Key 제약
    FOREIGN KEY (raw_id) REFERENCES raw_health_check(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    -- 인덱스 (통계 쿼리 최적화)
    INDEX idx_raw_id (raw_id),
    INDEX idx_risk_group (risk_group),
    INDEX idx_risk_count (risk_factor_count),
    INDEX idx_invalid (invalid_flag),
    INDEX idx_composite_stats (risk_group, invalid_flag)  -- 복합 인덱스

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### 컬럼 설명

| 컬럼              | 타입            | NULL | 설명                     | 비고              |
| ----------------- | --------------- | ---- | ------------------------ | ----------------- |
| id                | BIGINT UNSIGNED | ❌   | 자동 증가 PK             |                   |
| raw_id            | BIGINT UNSIGNED | ❌   | FK → raw_health_check.id | 1:1 관계          |
| bmi               | DECIMAL(4,1)    | ✅   | BMI 계산값               | 예: 27.3          |
| flag_hypertension | BOOLEAN         | ❌   | 고혈압 여부              | SBP≥140 or DBP≥90 |
| flag_diabetes     | BOOLEAN         | ❌   | 당뇨 여부                | 공복혈당≥126      |
| flag_tc_high      | BOOLEAN         | ❌   | 고콜레스테롤             | TC≥240            |
| flag_tg_high      | BOOLEAN         | ❌   | 고중성지방               | TG≥200            |
| flag_hdl_low      | BOOLEAN         | ❌   | 저HDL                    | HDL<40            |
| flag_obesity      | BOOLEAN         | ❌   | 비만                     | BMI≥25            |
| flag_smoking      | BOOLEAN         | ❌   | 현재흡연                 | smoking=3         |
| risk_factor_count | TINYINT         | ❌   | 위험요인 개수            | 0~7 합산          |
| risk_group        | ENUM            | ❌   | 위험 그룹                | ATP III 기반      |
| rule_version      | VARCHAR(20)     | ❌   | 판정 버전                | guideline-v1      |
| inference_time_ms | SMALLINT        | ✅   | 추론 시간                | 성능 측정         |
| invalid_flag      | BOOLEAN         | ❌   | 유효성 플래그            | TRUE면 통계 제외  |
| created_at        | TIMESTAMP       | ❌   | 생성 시각                |                   |

### risk_group ENUM 값

```
'ZERO_TO_ONE_RISK_FACTOR'    -- 저위험 (0~1개)
'MULTIPLE_RISK_FACTORS'       -- 중등도 (2개 이상, 당뇨 없음)
'CHD_RISK_EQUIVALENT'         -- 고위험 (당뇨 있음)
```

---

## 관계 (Relationship)

```
┌─────────────────────┐
│ raw_health_check    │
├─────────────────────┤
│ id (PK)             │
│ subscriber_id       │
│ age_group_code      │
│ gender_code         │
│ height, weight      │
│ systolic_bp, ...    │
└─────────────────────┘
         │ 1
         │
         │ 1 (FK)
         ▼
┌─────────────────────┐
│ clean_risk_result   │
├─────────────────────┤
│ id (PK)             │
│ raw_id (FK)         │◄── ON DELETE CASCADE
│ bmi                 │
│ flag_*              │
│ risk_factor_count   │
│ risk_group          │
└─────────────────────┘
```

**관계 유형**: 1:1 (raw 1개 → clean 1개)

---

## 인덱스 전략

### 1. 단일 컬럼 인덱스

**raw_health_check**:

- `idx_age_group`: 연령대별 통계 (`GROUP BY age_group_code`)
- `idx_systolic_bp`: 혈압 기준 필터링

**clean_risk_result**:

- `idx_risk_group`: 위험군별 통계 (`GROUP BY risk_group`)
- `idx_risk_count`: 위험요인 개수별 분석
- `idx_invalid`: 유효성 플래그 인덱스 (모든 저장 레코드가 valid이므로 실질적으로 미사용)

### 2. 복합 인덱스

**clean_risk_result**:

- `idx_composite_stats (risk_group, invalid_flag)`: 통계 쿼리 최적화
  ```sql
  SELECT risk_group, COUNT(*)
  FROM clean_risk_result
  WHERE invalid_flag = FALSE
  GROUP BY risk_group;
  ```

### 3. 인덱스 크기 추정

30만건 기준:

- `idx_age_group`: ~3MB
- `idx_risk_group`: ~2MB
- `idx_composite_stats`: ~4MB
- **총 인덱스 크기**: ~15MB (전체 DB 대비 10%)

---

## 샘플 쿼리

### 1. 통계 조회 (캐시 대상)

```sql
-- 위험군 분포
SELECT
    risk_group,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) as percentage
FROM clean_risk_result
GROUP BY risk_group;
-- Note: clean_risk_result contains ONLY valid records (invalid records not stored)
```

**인덱스 사용**: `idx_composite_stats`

### 2. 연령대별 통계

```sql
-- 연령대별 평균 위험요인 수
SELECT
    r.age_group_code,
    COUNT(*) as count,
    AVG(c.risk_factor_count) as avg_risk_count,
    SUM(CASE WHEN c.risk_group = 'CHD_RISK_EQUIVALENT' THEN 1 ELSE 0 END) as high_risk_count
FROM raw_health_check r
JOIN clean_risk_result c ON r.id = c.raw_id
GROUP BY r.age_group_code
ORDER BY r.age_group_code;
```

**인덱스 사용**: `idx_age_group`, `idx_invalid`

### 3. 레코드 조회 (페이징)

```sql
-- 페이징 조회
SELECT
    c.id,
    r.age_group_code,
    r.gender_code,
    c.bmi,
    c.risk_factor_count,
    c.risk_group,
    c.created_at
FROM clean_risk_result c
JOIN raw_health_check r ON c.raw_id = r.id
ORDER BY c.id
LIMIT 20 OFFSET 0;
```

**인덱스 사용**: PRIMARY KEY, `idx_invalid`

### 4. 단건 조회

```sql
-- ID로 상세 조회
SELECT
    c.*,
    r.age_group_code,
    r.gender_code,
    r.height,
    r.weight,
    r.systolic_bp,
    r.diastolic_bp,
    r.fasting_glucose,
    r.total_cholesterol,
    r.triglycerides,
    r.hdl_cholesterol,
    r.smoking_status
FROM clean_risk_result c
JOIN raw_health_check r ON c.raw_id = r.id
WHERE c.id = ?;
```

**인덱스 사용**: PRIMARY KEY

---

## 데이터 크기 추정

### raw_health_check

- 행당 크기: ~50 bytes
- 100만건: ~50MB (데이터) + 5MB (인덱스) = **55MB**

### clean_risk_result

- 행당 크기: ~40 bytes
- 34만건: ~14MB (데이터) + 14MB (인덱스) = **28MB**

### 총 DB 크기

- **데이터**: 64MB
- **인덱스**: 19MB
- **총**: ~**83MB** (실제 데이터 기준: raw 100만건, clean 34만건)

Railway Hobby Plan (8GB): 충분

---

## 마이그레이션 전략

### 초기 생성

```sql
-- 1. raw 테이블 생성
CREATE TABLE raw_health_check (...);

-- 2. clean 테이블 생성
CREATE TABLE clean_risk_result (...);

-- 3. 인덱스는 CREATE TABLE에 포함
```

### 인덱스 추가 (나중에)

```sql
-- 성능 측정 후 필요 시 추가
CREATE INDEX idx_additional ON clean_risk_result(column_name);
```

### 백업

```bash
# 데이터 백업
mysqldump -u user -p database_name > backup.sql

# 복원
mysql -u user -p database_name < backup.sql
```

---

## SQLAlchemy 모델 (참고)

```python
# app/models/health_check.py
from sqlalchemy import Column, BigInteger, SmallInteger, ...
from app import db

class RawHealthCheck(db.Model):
    __tablename__ = 'raw_health_check'

    id = Column(BigInteger, primary_key=True)
    age_group_code = Column(SmallInteger, nullable=False)
    # ... 나머지 컬럼

    # Relationship
    clean_result = db.relationship('CleanRiskResult', backref='raw_record', uselist=False)

class CleanRiskResult(db.Model):
    __tablename__ = 'clean_risk_result'

    id = Column(BigInteger, primary_key=True)
    raw_id = Column(BigInteger, ForeignKey('raw_health_check.id'), nullable=False)
    # ... 나머지 컬럼
```

---

**마지막 업데이트**: 2026-02-17
**다음 단계**: ETL 스크립트로 테이블 생성 및 데이터 적재
