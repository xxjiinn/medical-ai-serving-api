# Railway 배포 체크리스트

## 배포 전 준비

### 1. 코드 준비
- [ ] 모든 테스트 통과 확인 (`pytest tests/`)
- [ ] `.env` 파일이 `.gitignore`에 포함되어 있는지 확인
- [ ] `requirements.txt` 최신 상태 확인
- [ ] `Dockerfile` 및 `railway.toml` 확인

### 2. Railway 계정 및 프로젝트
- [ ] Railway 계정 생성 (https://railway.app)
- [ ] 새 프로젝트 생성
- [ ] GitHub repository 연결

### 3. Railway 서비스 프로비저닝
- [ ] MySQL 서비스 추가
- [ ] Redis 서비스 추가
- [ ] Flask 서비스 추가 (GitHub 연결)

## 환경변수 설정

### Flask 서비스
- [ ] `API_KEY` 설정 (강력한 랜덤 키)
- [ ] `FLASK_ENV=production` 설정
- [ ] `FLASK_DEBUG=False` 설정
- [ ] `DATABASE_URL` 자동 연결 확인 (MySQL 서비스)
- [ ] `REDIS_URL` 자동 연결 확인 (Redis 서비스)

### API Key 생성 예시
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

## 데이터베이스 초기화

### 1. 로컬 환경 설정
- [ ] `.env` 파일에 Railway Public URL 설정
  ```
  DATABASE_URL=mysql+pymysql://root:xxxxx@xxx.proxy.rlwy.net:xxxxx/railway
  ```

### 2. 테이블 생성
- [ ] SQLAlchemy 모델로 자동 생성 또는
- [ ] SQL 스크립트 직접 실행

### 3. 데이터 로드
- [ ] `python scripts/etl/load_raw.py` 실행
- [ ] `python scripts/etl/process_clean.py` 실행
- [ ] 데이터 로드 성공 확인

### 4. 인덱스 확인
- [ ] `python scripts/performance/check_indexes.py` 실행
- [ ] 필요한 인덱스 모두 생성되었는지 확인

## 배포 실행

### GitHub Push 배포
- [ ] `main` 브랜치에 push
- [ ] Railway 자동 빌드 시작 확인
- [ ] 빌드 로그에서 에러 없는지 확인
- [ ] 배포 완료 확인

### 배포 URL 확인
- [ ] Railway에서 자동 생성된 도메인 확인
- [ ] 예시: `https://medical-ai-serving-production.up.railway.app`

## 배포 후 검증

### 1. Health Check
```bash
curl https://your-app.railway.app/health
```
- [ ] `{"status": "ok"}` 응답 확인

### 2. API 인증 테스트
```bash
# 잘못된 키 - 401 에러 예상
curl https://your-app.railway.app/records

# 올바른 키 - 200 OK 예상
curl -H "X-API-KEY: your-api-key" \
  "https://your-app.railway.app/records?page=1&limit=5"
```
- [ ] 인증 없이 요청 시 401 에러
- [ ] 올바른 API Key 사용 시 정상 응답

### 3. Records 조회
```bash
curl -H "X-API-KEY: your-api-key" \
  "https://your-app.railway.app/records?page=1&limit=5"
```
- [ ] 페이징 응답 정상 확인
- [ ] `data`, `pagination` 필드 존재 확인

### 4. Stats 조회 (캐싱 확인)
```bash
# 첫 번째 요청 (Cache Miss)
time curl -H "X-API-KEY: your-api-key" \
  "https://your-app.railway.app/stats/risk"

# 두 번째 요청 (Cache Hit)
time curl -H "X-API-KEY: your-api-key" \
  "https://your-app.railway.app/stats/risk"
```
- [ ] 첫 요청: `cached: false`, 1-2초 소요
- [ ] 두 번째 요청: `cached: true`, <100ms 소요
- [ ] 캐싱 정상 작동 확인

### 5. Simulate 테스트
```bash
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
- [ ] 위험도 계산 정상 응답
- [ ] `risk_factor_count: 7` 확인
- [ ] `risk_group: CHD_RISK_EQUIVALENT` 확인

### 6. Logs 확인
```bash
railway logs
```
- [ ] 에러 로그 없는지 확인
- [ ] Redis 연결 성공 확인
- [ ] Database 쿼리 정상 실행 확인

## 모니터링 설정

### Railway 대시보드
- [ ] CPU/Memory 사용률 모니터링
- [ ] Response Time 확인
- [ ] 로그 정기 확인 설정

### Uptime 모니터링 (선택)
- [ ] UptimeRobot 등 외부 모니터링 도구 설정
- [ ] Health check endpoint ping 설정

## 트러블슈팅

### 배포 실패
- [ ] Railway 로그에서 빌드 에러 확인
- [ ] `Dockerfile` 문법 오류 확인
- [ ] `requirements.txt` 의존성 문제 확인

### Database 연결 실패
- [ ] `DATABASE_URL`이 Private URL 사용하는지 확인
- [ ] MySQL 서비스 상태 확인
- [ ] 환경변수 값 재확인

### Redis 연결 실패
- [ ] `REDIS_URL` 환경변수 확인
- [ ] Redis 서비스 상태 확인
- [ ] Private URL 사용 확인

### 502 Bad Gateway
- [ ] Health check endpoint 동작 확인
- [ ] Gunicorn timeout 설정 확인
- [ ] 앱 시작 시 에러 로그 확인

## 보안 체크

### 민감 정보
- [ ] `.env` 파일이 Git에 커밋되지 않았는지 확인
- [ ] API Key가 강력한 랜덤 값인지 확인
- [ ] Database 패스워드가 안전한지 확인

### 접근 제어
- [ ] 모든 API 엔드포인트가 인증 필요한지 확인 (health check 제외)
- [ ] Railway Private Networking 사용 확인

### HTTPS
- [ ] 모든 요청이 HTTPS로 처리되는지 확인
- [ ] Railway SSL 인증서 자동 발급 확인

## 성능 최적화

### 캐싱
- [ ] Redis 캐시 히트율 확인
- [ ] TTL 값 조정 필요 여부 검토

### Database
- [ ] 인덱스 성능 확인
- [ ] 느린 쿼리 확인 및 최적화

### 리소스
- [ ] Gunicorn workers/threads 수 조정
- [ ] Memory 사용량 확인 후 plan 조정

## 완료!

- [ ] 배포 URL 문서화
- [ ] API 사용 가이드 작성
- [ ] 팀원에게 공유

**배포 URL**: _____________________________________

**API Key**: (안전하게 보관)

**배포 날짜**: _____________________________________
