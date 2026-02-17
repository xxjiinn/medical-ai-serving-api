# Railway 배포 설정 가이드

## 1. Railway 계정 생성

1. https://railway.app 접속
2. GitHub 계정으로 로그인
3. Hobby Plan ($5/월) 선택

---

## 2. MySQL 데이터베이스 생성

1. Railway 대시보드 → **New Project**
2. **Add Service** → **Database** → **MySQL**
3. 생성 후 **Variables** 탭에서 연결 정보 확인:
   - `MYSQL_URL` 복사 (형식: `mysql://user:password@host:port/railway`)

4. `.env` 파일에 추가:
```bash
DATABASE_URL=mysql+pymysql://user:password@host:port/railway
```

---

## 3. Redis 캐시 생성

1. 같은 프로젝트에서 **Add Service** → **Database** → **Redis**
2. 생성 후 **Variables** 탭에서 연결 정보 확인:
   - `REDIS_URL` 복사 (형식: `redis://host:port`)

3. `.env` 파일에 추가:
```bash
REDIS_URL=redis://host:port/0
```

---

## 4. Flask 앱 배포 (ETL 완료 후)

1. **Add Service** → **GitHub Repo** 선택
2. `medical-ai-serving-api` 레포 연결
3. **Settings** → **Environment Variables** 설정:
   - `DATABASE_URL`: MySQL URL
   - `REDIS_URL`: Redis URL
   - `API_KEY`: 임의의 강력한 키 생성
   - `FLASK_ENV`: `production`

4. **Settings** → **Deploy** → **Dockerfile** 선택

---

## 5. 연결 테스트

로컬에서 Railway DB 연결 테스트:

```bash
# .env 파일 설정 후
python scripts/etl/load_raw.py
```

성공 시 Railway MySQL에 데이터 적재 완료.

---

## 6. 리소스 제한 고려

Railway Hobby Plan 제약:
- 메모리: 512MB ~ 8GB (사용량 기반 과금)
- CPU: Shared
- 네트워크: 100GB/월

**권장**:
- 데모 데이터: 30만건 이하
- ETL chunk size: 10,000 rows
- 쿼리 최적화 필수
