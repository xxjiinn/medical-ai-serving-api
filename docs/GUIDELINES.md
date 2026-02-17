# 임상 가이드라인 출처 및 기준

작성일: 2026-02-17

---

## ⚠️ 중요 고지

본 시스템의 모든 위험요인 판정 기준은 **공개된 임상 가이드라인의 cut-off 값**을 그대로 사용합니다.

- **임의 가중치 없음**: 0~100 점수 같은 자의적 계산식 사용 안 함
- **진단 목적 아님**: 의료 진단/치료/예측 도구가 아님
- **참고용**: 위험요인 요약/프로파일링만 제공
- **의료 판단**: 반드시 의료 전문가에게 의뢰

---

## 1. 고혈압 (Hypertension)

### 판정 기준

```
flag_hypertension = (수축기혈압 ≥ 140 mmHg) OR (이완기혈압 ≥ 90 mmHg)
```

### 출처

#### 1) 대한고혈압학회 (Korean Society of Hypertension)

- **문서**: 2022 한국 고혈압 진료지침
- **기준**:
  - 정상: 수축기 <120 AND 이완기 <80
  - 주의: 수축기 120-139 OR 이완기 80-89
  - 고혈압: 수축기 ≥140 OR 이완기 ≥90
- **링크**: http://www.koreanhypertension.org/

#### 2) JNC 8 (미국)

- **문서**: 2014 Evidence-Based Guideline for Management of High Blood Pressure in Adults
- **기준**: 동일 (140/90 mmHg)

### 적용 근거

- 한국 고혈압학회의 **진단 기준** (치료 시작 기준 아님)
- 국제적으로 합의된 cut-off 값
- 본 시스템: 진단 아닌 **선별(screening)** 목적

---

## 2. 당뇨 (Diabetes)

### 판정 기준

```
flag_diabetes = (공복혈당 ≥ 126 mg/dL)
```

### 출처

#### 1) 대한당뇨병학회 (Korean Diabetes Association, KDA)

- **문서**: 2023 당뇨병 진료지침
- **기준**:
  - 정상: 공복혈당 <100 mg/dL
  - 전당뇨: 공복혈당 100-125 mg/dL
  - 당뇨: 공복혈당 ≥126 mg/dL
- **링크**: https://www.diabetes.or.kr/

#### 2) ADA (American Diabetes Association)

- **문서**: Standards of Medical Care in Diabetes
- **기준**: 동일 (공복혈당 ≥126 mg/dL)
- **링크**: https://diabetesjournals.org/care/issue/47/Supplement_1

### 적용 근거

- KDA와 ADA의 **진단 기준** 동일
- WHO도 동일 기준 사용
- 본 시스템: 당뇨 "진단" 아닌 **위험 신호** 탐지

---

## 3. 이상지질혈증 (Dyslipidemia)

### 판정 기준

```
flag_tc_high = (총콜레스테롤 ≥ 240 mg/dL)
flag_tg_high = (트리글리세라이드 ≥ 200 mg/dL)
flag_hdl_low = (HDL콜레스테롤 < 40 mg/dL)
```

### 출처

#### NCEP ATP III (미국)

- **문서**: Third Report of the National Cholesterol Education Program (NCEP) Expert Panel on Detection, Evaluation, and Treatment of High Blood Cholesterol in Adults (Adult Treatment Panel III, ATP III)
- **발행**: 2002, NIH Publication No. 02-5215

**분류 기준**:

| 지표             | 분류            | 범위 (mg/dL) |
| ---------------- | --------------- | ------------ |
| **총콜레스테롤** | Desirable       | <200         |
|                  | Borderline High | 200-239      |
|                  | **High**        | **≥240** ✅  |
| **중성지방(TG)** | Normal          | <150         |
|                  | Borderline High | 150-199      |
|                  | **High**        | **≥200** ✅  |
| **HDL**          | Low             | **<40** ✅   |
|                  | High (보호적)   | ≥60          |

- **링크**: https://www.nhlbi.nih.gov/health-topics/all-publications-and-resources/atp-iii-guidelines-at-glance-quick-desk-reference

### 적용 근거

- ATP III는 **전 세계적으로 가장 널리 사용**되는 지질 관리 가이드라인
- 한국 지질동맥경화학회도 ATP III 기반으로 권고안 작성
- "High" 분류 cut-off를 위험요인 flag로 사용

---

## 4. 비만 (Obesity) - 아시아 기준

### 판정 기준

```
BMI = 체중(kg) / (신장(m))^2
flag_obesity = (BMI ≥ 25 kg/m²)
```

### 출처

#### WHO Asia-Pacific Guidelines

- **문서**: The Asia-Pacific Perspective: Redefining Obesity and its Treatment (2000)
- **발행**: World Health Organization, International Association for the Study of Obesity, International Obesity Task Force

**분류 기준**:

| 분류           | BMI (kg/m²) | 비고                  |
| -------------- | ----------- | --------------------- |
| Underweight    | <18.5       |                       |
| Normal         | 18.5-22.9   |                       |
| **Overweight** | **23-24.9** | 아시아 기준           |
| **Obese I**    | **25-29.9** | **✅ 본 시스템 기준** |
| Obese II       | ≥30         |                       |

- **링크**: https://apps.who.int/iris/handle/10665/206936

### 적용 근거

- **서양 기준** (과체중 25, 비만 30)과 다름
- **아시아인**은 같은 BMI에서 체지방률이 높고 대사질환 위험 증가
- WHO가 **아시아-태평양 지역**에 권장하는 기준 사용
- 본 시스템: BMI ≥25를 위험요인으로 플래그

---

## 5. 흡연 (Smoking)

### 판정 기준

```
flag_smoking = (흡연상태 == 3)  # 현재흡연자
```

### 출처

#### 1) NCEP ATP III

- **문서**: ATP III (동일 문서)
- **위치**: Section "Major Risk Factors" (CHD 위험요인)
- **내용**:
  - Cigarette smoking is a major, modifiable risk factor for CHD
  - "Current cigarette smoking" 명시

#### 2) WHO Framework Convention on Tobacco Control

- **문서**: WHO FCTC
- **내용**: 흡연은 심혈관질환의 주요 위험요인

### 적용 근거

- ATP III에서 흡연을 **주요 위험요인(Major Risk Factor)** 로 분류
- "현재 흡연자"만 위험요인으로 간주 (과거 흡연자 제외)
- 보수적 접근: 비흡연 데이터 결측 시 비흡연으로 간주

---

## 6. Risk Group 분류 (ATP III 프레임워크)

### 분류 기준

```
risk_group =
  IF diabetes == true THEN 'CHD_RISK_EQUIVALENT'
  ELSE IF risk_factor_count >= 2 THEN 'MULTIPLE_RISK_FACTORS'
  ELSE 'ZERO_TO_ONE_RISK_FACTOR'
```

### 출처

#### NCEP ATP III - Risk Category

- **문서**: ATP III, Section "Risk Assessment"
- **프레임워크**:
  1. **CHD or CHD Risk Equivalent** (최고 위험)
     - Diabetes ← 본 시스템 적용
     - Peripheral arterial disease
     - 복부 대동맥류 등
  2. **Multiple (2+) Risk Factors** (중등도 위험)
     - 위험요인 2개 이상
  3. **0-1 Risk Factor** (저위험)

- **원문**: "Diabetes is regarded as a CHD risk equivalent"

### 적용 근거

- ATP III에서 당뇨병을 **관상동맥질환과 동등한 위험**으로 취급
- 이는 의학적 합의 사항 (당뇨 환자는 심혈관질환 고위험군)
- 본 시스템: ATP III의 위험 계층화 프레임워크 차용

---

## 7. 주요 위험요인 목록 (ATP III)

ATP III에서 정의한 **Major Risk Factors (CHD 외)**:

1. ✅ Cigarette smoking (흡연)
2. ✅ Hypertension (BP ≥140/90 or 항고혈압제 복용)
3. ✅ Low HDL cholesterol (<40 mg/dL)
4. Family history of premature CHD (본 시스템 미사용 - 데이터 없음)
5. Age (남 ≥45, 여 ≥55) (본 시스템 미사용 - 나이 자체는 위험요인 아닌 층화 변수)

**본 시스템 추가**:

- ✅ Diabetes (당뇨) - CHD Risk Equivalent
- ✅ High TC (총콜레스테롤 ≥240)
- ✅ High TG (중성지방 ≥200)
- ✅ Obesity (BMI ≥25, 아시아 기준)

---

## 8. 사용하지 않는 지표

### LDL 콜레스테롤

- **이유**: ATP III에서 LDL은 **치료 목표**이지 위험요인 분류 기준 아님
- **본 시스템**: 총콜레스테롤로 충분 (선별 목적)

### 음주

- **이유**: 가이드라인에 명확한 cut-off 없음
- 적정 음주는 HDL 증가 효과, 과음은 위험
- 데이터: 음주 "여부"만 있고 양/빈도 없음

### 나이

- **이유**: 나이 자체는 위험요인이 아닌 **위험 층화 변수**
- ATP III: 나이는 Framingham 점수 계산에 사용
- 본 시스템: 통계 분석용, 위험요인 플래그 아님

---

## 9. 제한 사항

### 본 시스템이 하지 않는 것

1. **10년 심혈관질환 위험 예측** (Framingham Risk Score 등)
   - 이유: 복잡한 계산식, 검증 필요
2. **치료 권고**
   - 이유: 의료 행위에 해당
3. **가족력, 약물 복용 고려**
   - 이유: 데이터 없음
4. **종합 진단**
   - 이유: 선별(screening) 목적만

### 본 시스템이 하는 것

- ✅ 가이드라인 기반 위험요인 **존재 여부** 확인
- ✅ 위험요인 **개수 집계** (risk_factor_count)
- ✅ ATP III 프레임워크 기반 **위험 그룹 분류**

---

## 10. 면접 대비 Q&A

**Q. 이 기준들은 어디서 가져왔나요?**
A. 대한고혈압학회, 대한당뇨병학회, NCEP ATP III, WHO 등 공개 임상 가이드라인의 **진단/분류 기준**을 그대로 사용했습니다.

**Q. 왜 점수를 안 만들었나요?**
A. 임의 가중치는 의학적 근거가 없고, 진단 도구로 오해받을 위험이 있습니다. 대신 **가이드라인 기반 flag + count**로 제공합니다.

**Q. 당뇨가 있으면 무조건 고위험인가요?**
A. ATP III에서 당뇨를 "CHD Risk Equivalent"로 정의합니다. 이는 의학적 합의 사항으로, 본 시스템은 이 프레임워크를 차용했습니다.

**Q. 아시아 BMI 기준은 왜 다른가요?**
A. 아시아인은 같은 BMI에서 체지방률이 높고 대사질환 위험이 증가합니다. WHO가 아시아-태평양 지역에 권장하는 기준(25)을 사용했습니다.

---

## 11. 참고 문헌

1. Korean Society of Hypertension. (2022). 2022 한국 고혈압 진료지침.
2. Korean Diabetes Association. (2023). 당뇨병 진료지침.
3. American Diabetes Association. Standards of Medical Care in Diabetes. Diabetes Care.
4. National Cholesterol Education Program (NCEP) Expert Panel. (2002). Third Report of the NCEP Expert Panel on Detection, Evaluation, and Treatment of High Blood Cholesterol in Adults (ATP III). NIH Publication No. 02-5215.
5. World Health Organization. (2000). The Asia-Pacific Perspective: Redefining Obesity and its Treatment.
6. WHO Framework Convention on Tobacco Control.

---

**마지막 업데이트**: 2026-02-17

**중요**: 본 문서는 구현 중 가이드라인 변경 시 즉시 업데이트해야 합니다.
