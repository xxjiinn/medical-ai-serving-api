# JLK 지원용 프로젝트 통합 정리본 (진행 현황 + 기획/설계 가이드 + 면접 Q&A 설계)

- 작성 시각: 2026-02-16 13:35:07
- 대상: JLK 백엔드 개발자(Python/MySQL/SQL, Flask/Django 우대) 지원용 포트폴리오 프로젝트
- 원칙: **뇌피셜(개인 판단) 배제**, **공신력 있는 가이드라인 기준만 사용**, **진단/치료 목적 아님**

## 0. 이 문서의 목적

이 문서는 현재까지의 진행 상황, 확정된 의사결정, 남은 의사결정, 실패 방지 체크리스트(구현 중 확인 포함), 아키텍처/DB/API/기능 범위, 그리고 면접에서 좋은 질문-답변 흐름이 자연스럽게 오갈 수 있도록 설계된 Q&A까지 **빠짐없이** 한 곳에 정리한 통합본이다.
이 문서를 기준으로 GitHub 레포의 `docs/`에 동일 구조로 고정해나가며, 구현 중 변경사항은 **변경 이력** 섹션에 누적 기록한다.

## 1. 현재 나의 상황

- 나는 자바 기반(Spring Boot) 백엔드 개발자이며, 현재는 산업체 기업 취업을 목표로 한다.
- 지원 대상(JLK)은 Python 기반 백엔드 개발자를 모집하고 있으며, 자격요건에 Flask/Django, REST API, RDBMS 이해가 포함된다.
- 나는 Python이 처음이므로, AI 모델 자체 개발보다 **'대용량 의료 데이터 처리 + Serving 구조'**를 보여주는 것이 합리적이라고 판단했다.
- 배포/운영 경험은 Docker+EC2, Railway 둘 다 경험했고, 빠른 피드백 반영을 위해 Railway를 선택했다.

## 2. 최종 선택 주제

**공공 건강검진 데이터 기반 의료 Risk Factor Profiling / Stratification Inference API 서버**

- 한 줄 정의: NHIS 건강검진 데이터를 ETL로 적재하고, **공개 가이드라인 기준**으로 위험요인(고혈압/당뇨/지질/비만/흡연 등)을 판정하여 **risk factor count + 설명형 그룹**을 제공하는 **의료 AI Inference Serving 형태의 백엔드 API 데모 시스템**.
- 포지셔닝: **AI 모델을 '개발'하는 프로젝트가 아니라, 모델/룰 기반 inference를 '서비스'하기 위한 데이터/저장/캐시/버전/응답 구조를 구현**하는 백엔드 프로젝트.

## 3. 현재까지 완료한 작업(팩트)

- GitHub 레포 생성 완료
- NHIS 건강검진정보 2024 CSV 파일 다운로드 완료 (Numbers로 열리는 현상 확인)
- VSCode 개발 환경 사용 확정
- venv 생성 및 활성화
- pandas 설치
- CSV 인코딩(cp949)으로 정상 로드 확인
- 33개 컬럼명을 출력하여 구조 확인 완료
- 배포 플랫폼: Railway Hobby($5) 선택

## 4. 확정된 의사결정(Decisions)

### 4.1 기술 스택

- Framework: Flask
- 구조: Blueprint 분리(라우트/서비스/리포지토리/모델/ETL 분리)
- DB: MySQL
- Cache: Redis
- ORM: SQLAlchemy(기본) + 통계/성능 구간 Raw SQL 병행(면접 설명 용이)
- 배포: Railway(Hobby)
- 인증: API Key 기반(로그인/회원가입 제외)
- 환경: 로컬 venv, 배포 Docker(이미지 기반 재현성)

### 4.2 데이터 처리/적재

- 데이터 소스: NHIS 건강검진 2024 CSV(다운로드형)
- 적재: MySQL에 **raw 테이블 + clean 테이블** 2계층
- 규모: 설계는 대용량 대응(≥100만 행 처리 가능 구조) / 데모는 Railway 리소스 고려해 **샘플 수 고정 가능(예: 30만)**
- ETL: pandas DataFrame **chunk 기반 처리**(메모리 제어)
- 결측/이상치: raw에는 보존, clean에는 `invalid_flag`/NULL로 표시(삭제 지양)

### 4.3 서비스 기능 방향

- 의학적 근거가 있는 가이드라인 기반 cut-off로 위험요인 flag 산출(진단/치료/예측 아님)
- Serving 내부에서 **Inference Layer 분리**(향후 rule→모델 교체 가능)
- `simulate` API 제공(가상 환자 1건 입력 → risk factor 결과 반환)
- 통계 API는 Redis 캐시 적용(성능 개선 수치화 포인트)
- 포트폴리오 산출물: README + ERD + 아키텍처 + 성능리포트(필수)

## 5. 미확정/실행 중 의사결정

- 데모 데이터 수(10만/30만/50만) 최종 확정 및 근거(ETL 시간, DB 용량, 쿼리 성능 측정 가능성)
- 인덱스 구성 최종안(통계/필터 쿼리 기준 2~4개) 확정
- 캐시 TTL 및 무효화 정책(TTL 기반 vs 배치 완료 시 flush) 확정
- 로그/에러 응답 표준(요청 ID, 처리 시간, 예외 코드) 확정

## 6. 실패 방지 체크리스트

### 6.1 완료

- 공공데이터 접근/다운로드가 즉시 가능(승인 지연 없음)
- 데이터 라이선스/제한: 이용허락범위 제한 없음 확인
- CSV 로딩 성공(cp949), 33개 컬럼 확인 완료

### 6.2 구현 중 확인/기록(필수)

- Railway 리소스에서 ETL 완주 가능 여부(Chunk size 조정 기록)
- MySQL/Redis 리소스/비용 제약과 데모 수 조정 근거 기록
- 가이드라인 cut-off **출처 링크/참고문헌**을 문서화(뇌피셜 차단)
- 성능 수치(인덱스/캐시 전후 latency, P95 등) 리포트로 남기기
- 스토리라인(문제→선택→트레이드오프→개선→수치→교훈)을 커밋/문서로 남기기

## 7. 데이터 사전(33개 컬럼 전체)

NHIS 건강검진정보 2024 CSV 컬럼(총 33개) - 현재 확인된 컬럼명 목록:

1. 기준년도
2. 가입자일련번호
3. 시도코드
4. 성별코드
5. 연령대코드(5세단위)
6. 신장(5cm단위)
7. 체중(5kg단위)
8. 허리둘레
9. 시력(좌)
10. 시력(우)
11. 청력(좌)
12. 청력(우)
13. 수축기혈압
14. 이완기혈압
15. 식전혈당(공복혈당)
16. 총콜레스테롤
17. 트리글리세라이드
18. HDL콜레스테롤
19. LDL콜레스테롤
20. 혈색소
21. 요단백
22. 혈청크레아티닌
23. 혈청지오티(AST)
24. 혈청지피티(ALT)
25. 감마지티피
26. 흡연상태
27. 음주여부
28. 구강검진수검여부
29. 치아우식증유무
30. 결손치 유무
31. 치아마모증유무
32. 제3대구치(사랑니) 이상
33. 치석

## 8. 핵심 개념 정리

### 8.1 ETL과 Serving을 분리한다는 의미

- **ETL Layer(배치)**: CSV에서 데이터를 읽고(DataFrame), 정제/파생(BMI 등) 후 DB에 적재(raw/clean 생성)
- **Serving Layer(요청-응답)**: 적재된 DB를 조회/집계하고 API로 응답(캐시 포함)

### 8.2 Serving 내부에서도 Inference Layer를 분리한다는 의미

- **Inference Layer** = 결과를 '판정/계산'하는 계층(현재는 rule 기반 risk factor 판정)
- 목적: API 라우팅/검증 로직과 판정 로직을 분리하여, 향후 실제 모델 서빙으로 교체 가능하게 설계
- 예: `POST /simulate` → (Controller) → (Service) → **(Inference Layer)** → 결과 생성 → 응답

## 9. 위험요인 기준 확정(뇌피셜 0% / 공신력 기준)

원칙:

- **0~100 점수** 같은 임의 가중치 스코어링은 구현하지 않는다(설명 불가 + 뇌피셜 위험).
- **risk_factor_count(개수)** 중심으로 제공하고, 카테고리는 **설명형(risk group)**으로 보조한다.
- 모든 cut-off는 **가이드라인 문서의 정의/분류 기준을 그대로 사용**한다.

### 9.1 확정 Risk Factors (Flags)

| Risk Factor            |              기준(cut-off) | 데이터 컬럼                  | 비고                            |
| ---------------------- | -------------------------: | ---------------------------- | ------------------------------- |
| Hypertension           |    SBP ≥ 140 또는 DBP ≥ 90 | 수축기혈압, 이완기혈압       | 성인 진단 기준(한국 가이드라인) |
| Diabetes               |       공복혈당 ≥ 126 mg/dL | 식전혈당(공복혈당)           | 진단 기준(국내/ADA)             |
| High Total Cholesterol |             TC ≥ 240 mg/dL | 총콜레스테롤                 | ATP III 분류                    |
| High Triglycerides     |             TG ≥ 200 mg/dL | 트리글리세라이드             | ATP III 분류(High)              |
| Low HDL                |             HDL < 40 mg/dL | HDL콜레스테롤                | ATP III 분류(기본)              |
| Obesity (Asia)         |             BMI ≥ 25 kg/m² | 신장(5cm단위), 체중(5kg단위) | WHO 아시아 기준(파생)           |
| Smoking                | 현재흡연(데이터 코드 매핑) | 흡연상태                     | ATP III 주요 위험요인           |

### 9.2 risk_factor_count 산출 규칙

- `risk_factor_count` = 위 7개 플래그(true/false) 중 true 개수 합
- 예: Hypertension=true, Diabetes=true, Smoking=true → count=3

### 9.3 설명형 risk_group(보조) 규칙

**임의 등급(LOW/MID/HIGH)**은 만들지 않는다. 대신, 가이드라인에서 실제로 쓰는 개념 구조를 차용하여 설명형 그룹을 제공한다.

- `risk_group = CHD_RISK_EQUIVALENT` : Diabetes=true 인 경우(ATP III에서 당뇨는 CHD 동등위험으로 취급)
- `risk_group = MULTIPLE_RISK_FACTORS` : Diabetes=false 이면서 risk_factor_count ≥ 2 인 경우
- `risk_group = ZERO_TO_ONE_RISK_FACTOR` : Diabetes=false 이면서 risk_factor_count ≤ 1 인 경우

### 9.4 Non-Diagnostic Disclaimer(필수)

- 본 시스템은 **의료 진단/치료/예측**을 제공하지 않는다.
- 공개된 임상 가이드라인의 cut-off 기준으로 **위험요인 존재 여부를 요약/프로파일링**한다.
- 결과는 참고용이며, 의료적 판단은 의료 전문가에게 의뢰해야 한다.

### 9.5 Guideline References(README/문서에 반드시 포함)

> 아래는 '어떤 문서의 기준을 가져왔는지'를 명시하기 위한 섹션이다. 구현 단계에서 링크/문헌 정보를 정확히 채워 넣는다.

- Korean Society of Hypertension (고혈압 진단 기준)
- Korean Diabetes Association / ADA (당뇨 진단 기준)
- NCEP ATP III / NHLBI (지질 분류, 위험요인 정의)
- WHO Asia-Pacific obesity criteria (BMI 기준)

## 10. 프로젝트 결과물 형태(ETL 산출물 + API 응답)

### 10.1 ETL 최종 산출물: MySQL 2계층 테이블

#### (1) raw_health_check (원본 보존)

- 목적: CSV 원본을 가능한 그대로 보존(재처리/검증 가능)
- 예시 스키마(요약):

```text
raw_health_check(
  id PK,
  기준년도,
  가입자일련번호,
  성별코드, 연령대코드,
  수축기혈압, 이완기혈압,
  식전혈당,
  총콜레스테롤, 트리글리세라이드, HDL콜레스테롤, LDL콜레스테롤,
  신장, 체중,
  흡연상태,
  ... (필요 컬럼)
)
```

#### (2) clean_risk_result (정제 + 판정 결과)

- 목적: Serving에서 바로 사용 가능한 결과/설명 저장(설명 가능성 확보)
- 예시 스키마(요약):

```text
clean_risk_result(
  id PK,
  raw_id FK,
  bmi,
  flag_hypertension,
  flag_diabetes,
  flag_tc_high,
  flag_tg_high,
  flag_hdl_low,
  flag_obesity,
  flag_smoking,
  risk_factor_count,
  risk_group,
  rule_version,
  inference_time_ms,
  invalid_flag,
  created_at
)
```

### 10.2 JSON 응답 예시

#### (1) `POST /simulate` 요청/응답

요청(JSON):

```json
{
  "reference_year": 2024,
  "gender_code": 1,
  "age_group_code": 12,
  "sbp": 152,
  "dbp": 96,
  "fasting_glucose": 131,
  "total_cholesterol": 255,
  "triglycerides": 210,
  "hdl": 38,
  "height_cm": 170,
  "weight_kg": 85,
  "smoking_status": "current"
}
```

응답(JSON):

```json
{
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
    "Hypertension: SBP>=140 or DBP>=90",
    "Diabetes: fasting glucose>=126",
    "High TC: total cholesterol>=240",
    "High TG: triglycerides>=200",
    "Low HDL: hdl<40",
    "Obesity(Asia): BMI>=25",
    "Smoking: current smoker"
  ],
  "rule_version": "guideline-v1"
}
```

#### (2) `GET /stats/risk` 응답(캐시 대상)

```json
{
  "ZERO_TO_ONE_RISK_FACTOR": 145230,
  "MULTIPLE_RISK_FACTORS": 84210,
  "CHD_RISK_EQUIVALENT": 30450,
  "total": 259890
}
```

## 11. API 목록(확정)

- GET /records : 조건 기반 목록 조회(페이징, 제한된 필터)
- GET /records/{id} : 단건 조회(민감정보 최소화)
- GET /stats/risk : 위험요인 그룹 분포 통계(캐시 1순위)
- GET /stats/age : 연령대별 분포/그룹 통계(캐시 2순위)
- POST /simulate : 가상 환자 1건 입력 → inference 수행 → flags/count/group 반환

## 12. 면접 Q&A 세트(질문이 자연스럽게 나오도록 설계)

### Q. 이건 무슨 서비스에요?

- A. 공공 건강검진 데이터를 기반으로 한 **Risk Factor Profiling/Stratification Inference API 서버 데모**입니다. 의료 AI 기업에서 모델을 서비스할 때 필요한 **데이터 적재, 전처리, 추론(판정) 레이어 분리, 결과 저장, 캐시 최적화, API 제공 구조**를 구현했습니다. 모델 자체보다는 모델을 감싸는 Serving 아키텍처 구현에 초점을 뒀습니다.

### Q. 왜 굳이 이걸 만들었나요?

- A. 의료 AI 기업에서 중요한 것은 모델 정확도만이 아니라 **데이터를 안정적으로 처리하고 결과를 제공하는 Serving 구조**라고 판단했습니다. 그래서 모델 개발이 아니라 inference serving 백엔드 구조를 직접 구현해보고자 했습니다. NHIS 공공데이터는 라이선스 문제가 없고 의료 지표가 명확하여, 가이드라인 기반으로 설명 가능한 시스템을 만들기에 적합했습니다.

### Q. 어떤 공공데이터를 썼고 왜 이 데이터인가요?

- A. 국민건강보험공단 건강검진정보 2024 CSV를 사용했습니다. 즉시 다운로드 가능하고 이용허락범위 제한이 없으며, 혈압/혈당/지질/흡연 등 임상적으로 해석 가능한 지표가 포함되어 **가이드라인 기반 risk factor 판정**을 구현할 수 있기 때문입니다.

### Q. 뇌피셜 아닌가요? 기준은 뭔가요?

- A. 임의 가중치 스코어를 만들지 않았고, 모든 위험요인 cut-off는 **공개 임상 가이드라인 기준을 그대로 사용**합니다. 결과는 진단이 아니라 위험요인 요약이며, `risk_factor_count`와 `risk_group(설명형)`으로 제공합니다.

### Q. 프로젝트 하면서 얻은 것은?

- A. (1) 대용량 CSV를 pandas DataFrame chunk로 처리하는 ETL 설계/구현, (2) raw/clean 2계층 데이터 설계, (3) 인덱스/캐시 전후 성능 수치화, (4) Inference Layer 분리로 향후 모델 교체 가능한 구조 설계를 얻었습니다.

### Q. 가장 힘들었던 점은?

- A. (1) cp949 인코딩/툴 호환 문제, (2) Railway 리소스 한계 내에서 ETL/쿼리를 수행하기 위한 chunk size/인덱스/쿼리 설계, (3) 결측/이상치 처리 기준을 유지하면서 설명 가능성을 확보하는 부분이 어려웠습니다. 트레이드오프(데모 데이터 수 고정, TTL 선택 등)는 문서와 커밋으로 남깁니다.

### Q. 왜 로그인/회원가입이 없나요?

- A. 기간 내 핵심 역량(ETL, RDB 설계, 캐시/성능, API 구조)을 증명하는 것이 목표였고, 인증은 **API Key**로 최소화했습니다. 개인정보/보안 리스크도 낮출 수 있습니다.

### Q. 실제 AI 모델이 들어오면 어디에 붙이나요?

- A. Serving 내부에서 **Inference Layer**를 분리했고, 현재는 rule 기반 판정 로직이 들어가 있습니다. 향후 동일 인터페이스로 모델 서버 호출로 교체 가능하며 `rule_version/model_version`으로 결과 버전 관리도 가능하도록 설계합니다.

## 13. 앞으로의 실행 계획(Overview)

### Phase 1 설계 고정(문서/스키마/API)

- `docs/DECISIONS.md`: 왜 이 주제/데이터/구조인지, 트레이드오프 포함
- `docs/DATA_DICTIONARY.md`: 컬럼 매핑, 타입/범위/결측 규칙, 코드값(흡연 등)
- `docs/GUIDELINES.md`: cut-off 기준 + 출처(링크/문헌) 정리
- `docs/API_SPEC.md`: 요청/응답 예시(JSON) 포함
- `docs/ERD.md`: 테이블/인덱스/관계

### Phase 2 ETL 구현

- CSV chunk 로딩 → raw 적재
- 정제/파생(BMI) → clean 적재
- ETL throughput(rows/sec) 측정 및 기록

### Phase 3 DB 최적화

- 주요 쿼리 선정(통계/필터)
- 인덱스 전후 latency(ms) 비교 기록

### Phase 4 API 구현(Flask)

- Blueprint 분리 + service/repository 레이어 구현
- API Key 인증 미들웨어 구현
- 최소 API 5개 구현

### Phase 5 Redis 캐시

- stats API 캐시 적용
- cache hit/miss + P95 개선 수치 기록

### Phase 6 테스트/배포/리포트

- pytest(핵심 로직/에러케이스 포함)
- Railway 배포 + MySQL/Redis 연결
- 성능 리포트(ETL/Index/Cache) 작성
- README: 문제→선택→트레이드오프→개선→수치→교훈 서사 완성

## 14. 변경 이력

- 2026-02-16: 레포/데이터/컬럼 확인 완료. 주제/스택/배포/핵심 범위 확정. 위험요인 기준은 가이드라인 기반으로 고정하고(점수화 제거), `risk_factor_count + risk_group`로 결과 제공 방식 확정.
