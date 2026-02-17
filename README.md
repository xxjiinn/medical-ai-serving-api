# Medical AI Risk Factor Profiling API

> 🏥 의료 AI Inference Serving 백엔드 아키텍처 구현 프로젝트

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0.0-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## ⚠️ Non-Diagnostic Disclaimer

본 시스템은 **의료 진단/치료/예측 도구가 아닙니다**. 공개된 임상 가이드라인의 cut-off 기준으로 위험요인 존재 여부를 요약/프로파일링하는 참고용 시스템입니다. 의료적 판단은 반드시 의료 전문가에게 의뢰하십시오.

---

## 📋 프로젝트 개요

국민건강보험공단(NHIS) 건강검진 데이터(2024)를 기반으로 한 **위험요인 스크리닝 Inference Serving Backend**입니다.

### 핵심 목적
- AI 모델 개발 ❌
- **AI Serving 백엔드 아키텍처 구현** ✅
- ETL 파이프라인, DB 설계, 캐싱 전략, Inference Layer 분리

### 차별화 포인트
1. **ETL/Serving 레이어 분리** - 운영 안정성
2. **Inference Layer 분리** - 향후 ML 모델 교체 가능
3. **가이드라인 기반** - 법적 안정성, 설명 가능성
4. **성능 최적화 수치화** - 인덱스/캐싱 전후 비교

---

## 🏗️ 아키텍처

```
CSV (NHIS 2024)
    ↓ [ETL Layer - Batch]
MySQL raw_health_check (원본 보존)
    ↓ [ETL Layer - 정제/판정]
MySQL clean_risk_result (위험요인 결과)
    ↓ [Flask API - Serving Layer]
    ├─ Inference Layer (위험요인 계산)
    ├─ Service Layer (비즈니스 로직)
    ├─ Repository Layer (DB 접근)
    └─ API Layer (라우팅, 검증)
    ↓
Redis Cache (통계 API)
    ↓
Client (JSON 응답)
```

---

## 🛠️ 기술 스택

| 계층 | 기술 | 버전 |
|------|------|------|
| Framework | Flask | 3.0.0 |
| Database | MySQL | (Railway) |
| Cache | Redis | 5.0.1 |
| ORM | SQLAlchemy | 2.0.25 |
| ETL | pandas | 2.2.0 |
| Test | pytest | 7.4.4 |
| Deploy | Railway + Docker | - |

---

## 🚀 빠른 시작

### 사전 요구사항
- Python 3.11+
- MySQL (Railway)
- Redis (Railway)

### 설치

```bash
# 1. 저장소 클론
git clone https://github.com/xxjiinn/medical-ai-serving-api.git
cd medical-ai-serving-api

# 2. 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 의존성 설치
pip install -r requirements.txt

# 4. 환경변수 설정
cp .env.example .env
# .env 파일을 열어 DATABASE_URL, REDIS_URL, API_KEY 설정

# 5. ETL 실행 (CSV → MySQL)
python scripts/etl/load_raw.py
python scripts/etl/process_clean.py

# 6. Flask 서버 실행
flask run
```

---

## 📡 API Endpoints

### 인증
모든 API는 `X-API-KEY` 헤더 필요

```bash
curl -H "X-API-KEY: your-api-key" http://localhost:5000/records
```

### Endpoints

| Method | Endpoint | Description | Cache |
|--------|----------|-------------|-------|
| GET | `/records` | 검진 데이터 목록 (페이징) | - |
| GET | `/records/{id}` | 단건 조회 | - |
| GET | `/stats/risk` | 위험군 분포 통계 | ✅ |
| GET | `/stats/age` | 연령대 통계 | ✅ |
| POST | `/simulate` | 위험도 계산 (inference) | - |

상세 API 문서: [docs/API_SPEC.md](docs/API_SPEC.md)

---

## 🩺 위험요인 정의 (Guideline-Based)

| 위험요인 | Cut-off 기준 | 출처 |
|----------|--------------|------|
| 고혈압 | SBP≥140 or DBP≥90 | 대한고혈압학회 |
| 당뇨 | 공복혈당≥126 mg/dL | KDA/ADA |
| 고콜레스테롤 | TC≥240 mg/dL | ATP III |
| 고중성지방 | TG≥200 mg/dL | ATP III |
| 저HDL | HDL<40 mg/dL | ATP III |
| 비만(아시아) | BMI≥25 kg/m² | WHO Asia-Pacific |
| 흡연 | 현재 흡연자 | ATP III |

**risk_group 분류** (ATP III 프레임워크):
- `CHD_RISK_EQUIVALENT`: Diabetes=true
- `MULTIPLE_RISK_FACTORS`: Diabetes=false AND count≥2
- `ZERO_TO_ONE_RISK_FACTOR`: Diabetes=false AND count≤1

전체 가이드라인 출처: [docs/GUIDELINES.md](docs/GUIDELINES.md)

---

## 📊 데이터베이스 설계

### raw_health_check
원본 데이터 보존 (33개 컬럼)

### clean_risk_result
```sql
id, raw_id (FK),
bmi,
flag_hypertension, flag_diabetes, flag_tc_high, flag_tg_high,
flag_hdl_low, flag_obesity, flag_smoking,
risk_factor_count (0-7),
risk_group (enum),
rule_version, inference_time_ms, invalid_flag, created_at
```

ERD: [docs/ERD.md](docs/ERD.md)

---

## 🧪 테스트

```bash
# 전체 테스트
pytest

# 커버리지 포함
pytest --cov=app tests/

# 특정 테스트
pytest tests/test_inference.py -v
```

---

## 📈 성능 최적화

### 인덱스 전략
- `age_group`, `risk_level`, `systolic_bp`

### 캐싱 전략
- 통계 API (TTL: 1시간)

### 측정 결과
- ETL 처리속도: `X rows/sec`
- 인덱스 개선: 쿼리 응답 `Y% 단축`
- 캐시 개선: P95 latency `Z% 단축`

상세 성능 리포트: [docs/PERFORMANCE_REPORT.md](docs/PERFORMANCE_REPORT.md)

---

## 🚢 배포

### Railway 배포
```bash
# Dockerfile 빌드 및 배포
railway up
```

배포 URL: `(배포 후 추가)`

---

## 📚 문서

- [DECISIONS.md](docs/DECISIONS.md) - 기술 선택 및 트레이드오프
- [API_SPEC.md](docs/API_SPEC.md) - API 요청/응답 예시
- [ERD.md](docs/ERD.md) - DB 스키마 설계
- [GUIDELINES.md](docs/GUIDELINES.md) - 가이드라인 출처
- [DATA_DICTIONARY.md](docs/DATA_DICTIONARY.md) - 데이터 컬럼 정의
- [PERFORMANCE_REPORT.md](docs/PERFORMANCE_REPORT.md) - 성능 측정 결과

---

## 🎯 프로젝트 목표 달성

### 백엔드 역량 증명
- ✅ 대용량 ETL 파이프라인 설계
- ✅ RDB 스키마 설계 및 인덱스 최적화
- ✅ REST API 설계 및 구현
- ✅ Redis 캐싱 전략
- ✅ 레이어 분리 아키텍처
- ✅ 성능 최적화 수치화
- ✅ 배포 및 운영 환경 구성

### 의료 도메인 이해
- ✅ 공개 가이드라인 기반 설계
- ✅ 법적 안정성 고려
- ✅ 설명 가능성 확보

---

## 👨‍💻 개발자

**오성진**
- GitHub: [@xxjiinn](https://github.com/xxjiinn)
- Portfolio: JLK 백엔드 개발자 지원용 프로젝트

---

## 📄 라이선스

MIT License

---

## 🙏 감사의 글

- 국민건강보험공단(NHIS) 건강검진 데이터 제공
- 대한고혈압학회, 대한당뇨병학회, NCEP ATP III, WHO 가이드라인

---

**Last Updated**: 2026-02-17
