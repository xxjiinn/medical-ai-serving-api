# Deployment Guide

Railway 플랫폼 배포 가이드

## 사전 요구사항

1. **Railway 계정**: https://railway.app
2. **Railway CLI** (선택):
   ```bash
   npm install -g @railway/cli
   railway login
   ```

## Railway 서비스 구성

### 1. MySQL Database
- Railway 대시보드에서 MySQL 프로비저닝
- 자동으로 `DATABASE_URL` 환경변수 생성됨
- Private URL: `mysql.railway.internal:3306` (프로덕션)
- Public URL: `xxx.proxy.rlwy.net:xxxxx` (로컬 개발)

### 2. Redis Cache
- Railway 대시보드에서 Redis 프로비저닝
- 자동으로 `REDIS_URL` 환경변수 생성됨
- Private URL: `redis.railway.internal:6379` (프로덕션)
- Public URL: `xxx.proxy.rlwy.net:xxxxx` (로컬 개발)

### 3. Flask Application
- GitHub repository 연결
- 자동 빌드 및 배포 설정
- 환경변수 수동 설정 필요

## 환경변수 설정

Railway 대시보드 → Variables 탭에서 다음 환경변수 설정:

```bash
# Database (MySQL 서비스에서 자동 생성됨)
DATABASE_URL=mysql+pymysql://root:xxxxx@mysql.railway.internal:3306/railway

# Redis (Redis 서비스에서 자동 생성됨)
REDIS_URL=redis://default:xxxxx@redis.railway.internal:6379

# API Authentication (직접 생성)
API_KEY=your-production-api-key-here

# Flask Environment
FLASK_ENV=production
FLASK_DEBUG=False

# Port (Railway가 자동으로 할당, 설정 불필요)
# PORT=xxxxx
```

⚠️ **주의**: `API_KEY`는 반드시 강력한 랜덤 키로 설정하세요.

```bash
# 랜덤 API Key 생성 예시
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

## 배포 방법

### Option A: GitHub 연동 (권장)

1. GitHub repository를 Railway에 연결
2. Railway가 자동으로 `Dockerfile` 감지하여 빌드
3. `main` 브랜치 push 시 자동 배포

```bash
git add .
git commit -m "🚀 Deploy to Railway"
git push origin main
```

### Option B: Railway CLI

```bash
# 프로젝트 초기화
railway init

# 환경변수 설정
railway variables set API_KEY="your-api-key"

# 배포
railway up
```

### Option C: Docker로 로컬 테스트

```bash
# Docker 이미지 빌드
docker build -t medical-ai-serving .

# 로컬 실행
docker run -p 5001:5001 \
  -e DATABASE_URL="mysql+pymysql://..." \
  -e REDIS_URL="redis://localhost:6379/0" \
  -e API_KEY="test-key" \
  -e FLASK_ENV="production" \
  medical-ai-serving

# Health check
curl http://localhost:5001/health
```

## 데이터베이스 초기화

### 1. 테이블 생성

Railway MySQL에 연결하여 스키마 생성:

```bash
# Railway CLI 사용
railway connect mysql

# 또는 MySQL 클라이언트 사용
mysql -h xxx.proxy.rlwy.net -P xxxxx -u root -p
```

```sql
-- app/models/health_check.py의 스키마 참조하여 테이블 생성
-- 또는 SQLAlchemy로 자동 생성
```

### 2. 데이터 로드

로컬에서 ETL 스크립트 실행:

```bash
# .env 파일의 DATABASE_URL을 Railway Public URL로 설정
DATABASE_URL=mysql+pymysql://root:xxxxx@xxx.proxy.rlwy.net:xxxxx/railway

# ETL 실행
python scripts/etl/load_raw.py
python scripts/etl/process_clean.py
```

⚠️ **주의**: 대용량 데이터 업로드는 시간이 오래 걸리므로 네트워크 안정성 확인 필요

## 배포 후 검증

### 1. Health Check

```bash
curl https://your-app.railway.app/health
```

Expected response:
```json
{
  "status": "ok"
}
```

### 2. API 테스트

```bash
# Records 조회
curl -H "X-API-KEY: your-api-key" \
  "https://your-app.railway.app/records?page=1&limit=5"

# Stats 조회 (캐싱 확인)
curl -H "X-API-KEY: your-api-key" \
  "https://your-app.railway.app/stats/risk"

# Simulate 테스트
curl -X POST -H "X-API-KEY: your-api-key" \
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
  "https://your-app.railway.app/simulate"
```

### 3. Logs 확인

```bash
# Railway CLI
railway logs

# 또는 Railway 대시보드에서 확인
```

### 4. Redis 캐싱 확인

```bash
# 첫 요청 (Cache Miss)
time curl -H "X-API-KEY: your-api-key" \
  "https://your-app.railway.app/stats/risk"

# 두 번째 요청 (Cache Hit, 훨씬 빠름)
time curl -H "X-API-KEY: your-api-key" \
  "https://your-app.railway.app/stats/risk"
```

## 트러블슈팅

### 1. 배포 실패

- **문제**: Docker 빌드 실패
- **해결**: Railway Logs에서 에러 메시지 확인, `requirements.txt` 및 `Dockerfile` 검증

### 2. Database 연결 실패

- **문제**: `Can't connect to MySQL server`
- **해결**:
  - `DATABASE_URL`이 Private URL(`mysql.railway.internal`)을 사용하는지 확인
  - MySQL 서비스와 Flask 서비스가 같은 Railway 프로젝트에 있는지 확인

### 3. Redis 연결 실패

- **문제**: Redis 캐싱 동작하지 않음
- **해결**:
  - `REDIS_URL` 환경변수 확인
  - Redis 서비스 상태 확인 (Railway 대시보드)
  - Flask 로그에서 "Redis connection failed" 메시지 확인

### 4. 느린 응답 속도

- **문제**: API 응답이 느림
- **해결**:
  - Redis 캐싱이 활성화되었는지 확인 (`cached: true` 필드)
  - Database 인덱스 확인 (`scripts/performance/check_indexes.py`)
  - Railway 리전 확인 (데이터베이스와 앱이 같은 리전인지)

### 5. 502 Bad Gateway

- **문제**: 서비스 시작 실패
- **해결**:
  - Health check endpoint (`/health`) 동작 확인
  - Gunicorn timeout 설정 확인 (120초)
  - Railway Logs에서 시작 에러 확인

## 모니터링

### Railway 대시보드에서 확인 가능한 메트릭:

- **CPU/Memory 사용량**: 리소스 최적화 필요 여부 판단
- **Network Traffic**: API 호출량 모니터링
- **Response Time**: 응답 속도 추이
- **Logs**: 에러 및 경고 메시지 추적

### 권장 모니터링:

1. Health check endpoint를 정기적으로 ping (uptime 모니터링)
2. Redis 캐시 히트율 로그 분석
3. API 응답 시간 측정
4. 데이터베이스 쿼리 성능 분석

## 비용 최적화

- **Hobby Plan**: 월 $5, 512MB RAM, 충분한 소규모 프로젝트용
- **Pro Plan**: 월 $20, 8GB RAM, 프로덕션 환경 권장

### 최적화 팁:

1. **Gunicorn workers 조정**: 메모리에 맞춰 workers 수 조정
2. **Redis 캐싱**: 통계 API의 TTL 조정 (현재 60초)
3. **Database connection pooling**: SQLAlchemy pool size 최적화
4. **로그 레벨 조정**: 프로덕션에서는 INFO 레벨만 출력

## 보안 고려사항

1. **API Key 관리**:
   - Railway Variables에만 저장
   - `.env` 파일은 절대 Git에 커밋하지 않음
   - 정기적으로 API Key 순환

2. **Database 접근**:
   - Private URL만 사용 (앱 내부)
   - Public URL은 로컬 개발/ETL만 사용
   - 강력한 root 패스워드 설정

3. **HTTPS**:
   - Railway가 자동으로 SSL/TLS 제공
   - 모든 API 호출은 HTTPS 사용

4. **Input Validation**:
   - `/simulate` 엔드포인트의 입력값 검증 철저히 수행
   - SQL Injection 방지 (SQLAlchemy ORM 사용)

## 참고 자료

- Railway Docs: https://docs.railway.app
- Flask Deployment: https://flask.palletsprojects.com/en/latest/deploying/
- Gunicorn Configuration: https://docs.gunicorn.org/en/stable/settings.html
