# DOE Studio 사양서 — Minitab DOE 메뉴 클론

작성일 2026-10-31 · 상태: **0단계(조사·계획) 완료**. 1단계 엔진의 첫 조각(2수준 요인설계 생성)까지 구현·검증됨.

## 1. 목적과 범위

**목적**: 화학기업 연구원이 Minitab 없이도 같은 방식으로 실험을 설계하고 분석할 수 있는 웹앱. Minitab 의 `Stat > DOE` 메뉴가 하는 일을 같은 순서, 같은 옵션, 같은 출력표로 재현하고, 결과 숫자는 Minitab 과 일치시킨다.

**범위 안(단계별)**

| 단계 | Minitab 메뉴 | 핵심 산출물 |
|---|---|---|
| 1 | Factorial › Create Factorial Design(2-level default/specify generators, Plackett-Burman, General full factorial) · Analyze Factorial Design · Factorial Plots · Cube Plot · Display and Modify Design(randomize, replicate, fold) | 설계 생성, 워크시트, 분산분석표, 효과도(Pareto·정규·반정규), 잔차 그림 |
| 2 | Response Surface › Create(CCD, Box-Behnken) · Analyze · Contour/Surface Plot · Overlaid Contour · Response Optimizer · Predict · Display and Modify(add axial points) | 반응표면 적합, 등고선·표면도, 다중반응 만족도 최적화 |
| 3 | Mixtures › Create(simplex centroid/lattice, extreme vertices) · Analyze · Simplex Design Plot · Response Trace Plot · Screening › Create/Analyze Definitive Screening Design · Select Optimal Design · 2-level Split-Plot | 혼합물 설계·분석, 확정적 선별설계, D-최적 설계, 분할구 |
| 보류 | Taguchi · Analyze Binary Response · Analyze Variability · Comparisons · Quick Designs | 참고 문서만 수집 |

**범위 밖**: Minitab 의 범용 통계 메뉴(회귀·관리도·공정능력 등), 매크로/명령어 언어, 벤더 검증 문서.

## 2. 원칙

1. **기능은 같게, 겉모습은 다르게.** 통계 절차·옵션·출력표 구성은 Minitab 문서 그대로 따른다. 이름·로고·아이콘·도움말 문구·화면 디자인은 쓰지 않는다. 제품 작업명은 "DOE Studio"(변경 가능).
2. **숫자는 문서 예제와 일치해야 한다.** Minitab 지원 문서의 예제 출력표(`tests/fixtures/minitab_docs/`)가 정답지다. 표시 자릿수까지 같아야 통과.
3. **엔진과 화면 분리.** `doe_core` 는 UI 없이 pandas DataFrame 과 dataclass 만으로 동작한다. Streamlit 은 1차 화면이고 나중에 교체 가능해야 한다.
4. **한글 UI, 영어 라벨 병기.** 메뉴·대화상자·출력표 제목은 Minitab 한국어판 용어를 쓰고 영어 원문을 괄호로 병기한다(용어표: `docs/research/minitab-menu-tree.md`, 각 요약 문서의 라벨 매핑표).
5. **설계 정보는 워크시트와 함께 저장.** Minitab 처럼 설계 유형·요인·생성자·블록·중앙점 정보를 데이터와 함께 보관해야 "Analyze" 가 설계를 인식한다.
6. **문서에 없는 것은 추측하지 않는다.** 요약 문서에 "문서에 없음/미확인"으로 표시된 항목은 Minitab 실물 또는 교과서로 확인하기 전까지 구현 시 가장 보수적인 선택을 하고 주석으로 남긴다.

## 3. 기준 자료(조사 산출물)

| 자료 | 위치 | 내용 |
|---|---|---|
| 메뉴 트리(en/ko), 문서 구성, 데이터셋 목록 | `docs/research/minitab-menu-tree.md` | 좌측 메뉴 `nav_*` 페이지를 양 언어로 수집해 슬러그로 1:1 대응 |
| 문서 원문 텍스트 226편(en-us) + 48편(ko-kr) | `research/minitab_docs/` | git 제외(저작권). `research/fetch_pages.py` + `urls_*.txt` 로 재수집 |
| 예제 출력표 JSON 48개 | `tests/fixtures/minitab_docs/` | `research/extract_fixtures.py` 로 자동 추출. 각 파일: url, title, steps, tables[{heading, header, rows}]. 파일명은 문서 경로에서 `doe__how-to__` 를 떼고, `using-fitted-models` 는 `ufm__`, `supporting-topics` 는 `topic__`, `interpret-the-results__all-statistics-and-graphs` 는 `asg` 로 줄인 것 |
| A. 설계 생성 계열 상세 | `docs/spec/A_factorial_create.md` (1,129줄) | Create Factorial 5종·Define Custom·Display and Modify·Quick Designs·DSD 생성의 대화상자 전 필드, 가용 설계표·생성자표 원문, 중앙점·블록·접기·분할구 규칙, 출력 레이아웃, 예제 설계표 9개, 한국어 라벨 60여 항목 |
| B. 분석·그래프·최적화 상세 | `docs/spec/B_analysis_plots_optimizer.md` (886줄) | Analyze Factorial/Screening/Variability 대화상자, 출력표 형식, 텍스트로 남은 공식, 효과도·잔차·요인그림·입방체도·등고선·표면·중첩 등고선 사양, Response Optimizer·Predict, 예제 수치, 라벨 매핑 |
| C. 반응표면·혼합물·최적설계 상세 | `docs/spec/C_rsm_mixture_optimal.md` (1,955줄) | CCD·BBD 카탈로그와 블록·α 규칙, Analyze RS 출력, 혼합물 설계 3종·단위 변환·제약·증강, Analyze Mixture 출력, Select Optimal Design 기준·지표, Taguchi 카탈로그 |
| 샘플 데이터(.MWX) | 미수령 | 8절 참고 |

## 4. 조사에서 확인된 제약과 함정

구현할 때 반드시 알고 있어야 하는 것들이다. 근거는 각 요약 문서의 "구현 시 주의할 점".

1. **공식 본문은 이미지다.** methods-and-formulas 페이지의 수식은 PNG 라 텍스트에 없다. 텍스트로 남은 것(Effect = 2×Coef, Lenth PSE 4단계, ME = t·PSE, 정규/반정규/Pareto 작도 규칙, Adj SS 분해, 순수오차 DF, 레버리지 기준, 단위 변환, DF 규칙)만 문서에서 왔고, 나머지(SE Coef, VIF, PRESS, R² 계열, Cook's D, DFITS, AICc/BIC, 신뢰·예측구간, 만족도 함수 세부)는 표준 선형모형 정의로 구현한 뒤 **예제 숫자로 검증**한다.
2. **기본 생성자표에 오류가 있다.** 13요인 128런 행은 12요인 행의 블록 지정을 복사한 것이라, 실제 생성자(M=ACEF, N=ABC …)로 계산하면 2블록은 해상도 III(문서 IV), 8·16블록은 블록이 주효과와 교락된다. `doe_core/designs/catalog.py` 는 로드 시 모든 블록 지정을 생성자와 대조해 해상도를 바로잡거나(corrected) 제외(dropped)하고 `CATALOG_ERRATA` 에 기록한다. 5요인 16런 행은 문서에 중복으로 실려 있다(카탈로그 49행).
3. **예제 워크시트 발췌의 StdOrder 는 믿지 않는다.** Create 예제의 워크시트 6행은 표준(Yates) 순서와 맞지 않고(전부 −1 인 런이 StdOrder 6 등), 블록 예제의 첫 4행은 블록 생성자 부호가 블록 안에서 일정하지 않다. 설계 검증은 런 **집합**·블록 배정·별칭 구조·중앙점 수로 하고, 랜덤화 OFF 일 때 Yates 순서가 맞는지만 확인한다.
4. **CCD 요약표에 산식과 안 맞는 행이 있다.** "3요인 Full 14런 1블록" 행은 cube 8 + axial 6 + center 6 = 20 이어야 하나 14로 적혀 있다(나머지 43행은 산식과 일치). 이 한 행은 Minitab 실물로 확인 전까지 산식 값을 쓴다.
5. **라벨 표기가 문서마다 다르다.** ANOVA 그룹 행이 `2-Way Interaction`(RS) / `2-Way Interactions`(Factorial) 로 공존하고, 한국어판은 `혼합` vs `혼합물 설계`, 설계표 `Run` 이 `런`/`실행` 으로 갈린다. 명령별로 문서에 나온 표기를 그대로 따르고 UI 용어표에 명시한다.
6. **문자 건너뛰기 규칙**: 요인 문자는 I 를 건너뛴다(A~H, J~P). 혼합물 성분 문자는 T 를 건너뛰고, 공정변수는 X1~X7 이다.
7. **중앙점 규칙**: 2수준 요인설계는 블록당 지정 수 × 텍스트 요인 수준 조합(2^Q). 반복을 늘려도 중앙점은 늘지 않는다. PB 는 반복마다, DSD 는 숫자만 1·텍스트 포함 2 로 고정, 분할구는 불가.
8. **블록 규칙**: 블록 수가 반복 수의 배수이면 반복이 블록이 된다(생성자 불필요, 해상도 유지). 블록 생성자 부호가 전부 + 인 런이 블록 1. 다중 생성자의 블록 번호 대응은 문서에 없어 (+,+)=1, (+,−)=2, (−,+)=3, (−,−)=4 로 정한다.
9. **별칭표 기본 차수 상한**: 요인 ≤7 전부, 8~10 은 3차, 11~15 는 2차. 사용자가 차수를 지정하면 제목이 `Alias Structure (up to order n)` 가 되고 사슬 안에서도 그 차수 이하만 남긴다.
10. **포화 모형**: 오차 자유도 0 이면 p 값은 `*`, 효과도는 Lenth PSE 기준(ME = t·PSE, df = 효과 수/3). Stepwise 는 포화 모형에서 ¼(최대 9) 항을 먼저 제거한다.
11. **혼합물 모형은 절편이 없다**: 계수표에 Constant 없음, 선형항 T/P 는 `*`, Seq SS 와 Adj SS 둘 다 표시, Model Summary 에 PRESS 포함, ANOVA 에 `Component Only` / `Component * X` 그룹 제목 행.
12. **PB 생성열**: 문서의 40런 생성열은 부호 수가 맞지 않으므로 "20런 설계 복제" 규칙으로 재생성해 검증한다. 28런은 9×27 블록 순환.

## 5. 아키텍처

```
doe_core/
  designs/   words.py(단어 비트마스크·정의관계·해상도)  catalog.py(기본 생성자표 49행 + 로드 시 검증)
             factorial.py(2수준 완전·부분, 블록, 중앙점, 반복, 랜덤화, Design Summary, Alias Structure)   ← 구현됨
             plackett_burman.py  general_full.py  split_plot.py  response_surface.py(CCD·BBD)  mixture.py  screening.py(DSD)  optimal.py
  analysis/  model.py(항 생성: 차수·교호작용·제곱·블록·공변량)  fit.py(OLS, 코드화 단위)
             anova.py(Adj SS·Seq SS·Lack-of-fit·Pure error·Curvature)  effects.py(Effect, Lenth PSE, ME)
             diagnostics.py(표준화·삭제 잔차, 레버리지, Cook, DFITS, R/X 플래그)  alias.py(분석 시 별칭 제거)
  optimize/  desirability.py(개별·종합 만족도)  optimizer.py  predict.py(Fit, SE Fit, CI, PI)
  plots/     pareto.py normal.py main_effects.py interaction.py cube.py contour.py surface.py residuals.py
  io/        worksheet.py(설계 메타데이터 + 데이터, JSON/CSV/Excel)
app/         Home.py, pages/(설계 생성 · 데이터 입력 · 분석 · 그래프 · 최적화)
tests/       픽스처 기반 수치 검증 + 엔진 자체 검증
```

**핵심 데이터 모델**
- `Factor(name, low, high, numeric)` — 텍스트 요인은 numeric=False, low/high 가 수준 이름.
- `TwoLevelDesign(factors, runs, coded, entry, base_runs, generators, block_generators, alias, n_blocks, center_points_per_block, replicates, seed)` — `runs` 는 실제 수준값 워크시트, `coded` 는 −1/0/+1 코드. 같은 패턴으로 RS·혼합물 설계 클래스를 둔다.
- `FittedModel(design, response, terms, coef_coded, coef_uncoded, anova, summary, diagnostics, alias)` (1단계 후반).

**워크시트 열 규약(Minitab 과 동일)**: C1 `StdOrder`, C2 `RunOrder`, C3 `CenterPt`(2수준 요인설계: 1=모서리, 0=중앙점) 또는 `PtType`(PB·DSD·분할구·일반완전요인·반응표면·혼합물: 1 모서리/꼭지점, 0 중앙점, −1 축점, 2 모서리 중점, 3 triple blend), C4 `Blocks`, C5~ 요인열. 분할구는 `WP` 추가. StdOrder 는 블록별로 묶은 뒤 1부터, RunOrder 는 블록 안에서만 랜덤.

## 6. 기능 사양(단계별 합격 기준)

세부 사양은 A/B/C 요약 문서에 있고, 여기서는 구현 순서와 합격 기준만 적는다.

### 6.1 요인설계 생성 (1단계) — 2수준 부분 **완료**
- 상세: A 문서 1~3절(대화상자·표·알고리즘), 5절(출력 레이아웃).
- 합격 기준: 문서 예제의 Design Summary·Design Generators·Alias Structure 를 글자 단위로 재현. 가용 설계표와 기본 생성자표를 내장하고, 생성자로부터 재계산한 해상도가 표와 일치.
- 현재 상태: `create_two_level_design` 이 6요인 16런 1/4(E=ABC F=BCD, 해상도 IV, 별칭 16줄), 5요인 16런 1/2 블록 4(E=ABCD, AB·AC, 블록 포함 해상도 III, Blk1~3) 예제를 통과. 카탈로그 49행 해상도·블록 해상도 재계산 일치(오류 3건은 `CATALOG_ERRATA`). 텍스트 요인 중앙점 2^Q, 반복-블록 규칙, 별칭 차수 상한, NOTE 문구 구현. 남은 것: PB, 일반 완전요인, specify-generators 의 fraction 번호, 접기(fold), 분할구.
- 픽스처: `factorial__create-factorial-design__create-2-level-factorial-default-generators__example-of-a-2-level-fraction…`, `…example-of-a-2-level-design-w…`, `…create-plackett-burman…example`(9요인 12런+중앙점 3), `…create-general-full-factorial…example`(3×3×3), `…create-2-level-split-plot…example`(4요인 1 HTC, 32런), `topic__factorial-and-screening-designs__available-2-level-factorial-designs`, `topic__factorial-and-screening-designs__design-generators-for-2-level-designs`.

### 6.2 요인설계 분석 (1단계)
- 상세: B 문서 1~3절(대화상자·출력표·공식), 7절(예제 수치).
- 합격 기준: InsulationProperties 예제(Strength, 2차 항까지 + 공변량 MeasTemp)의 Coded Coefficients(Effect·Coef·SE Coef·T·P·VIF), Model Summary(S=1.51005, R-sq 98.02%, adj 92.57%, pred 70.86%), ANOVA(Model 11 / 451.357 … Error 4 / 9.121, Total 15 / 460.478), 비코드화 회귀식, 별칭 구조를 표시 자릿수까지 일치. 설계행렬 열 순서(Constant → Covariates → Blocks → Factors → Interactions)가 표 순서와 별칭 제거의 기준.
- 픽스처: `factorial__analyze-factorial-design__example`, `screening__analyze-screening-design__example`(DSD 7요인), `factorial__analyze-factorial-design__asg__*`(계수표·ANOVA·Means·잔차 그림 설명).

### 6.3 그래프 (1·2단계)
- 상세: B 문서 4절.
- 효과도: Pareto(표준화 효과, 기준선 t(1−α/2, df_E); df_E=0 이면 ME=t·PSE), 정규·반정규 확률도. 주효과·교호작용 그림은 적합 평균 기준(데이터 평균 옵션). 입방체도(예제 28.3558). 잔차 4종. 등고선·표면도는 두 요인 축 + 나머지 고정값(hold), 중첩 등고선도는 반응별 low/high. 중앙점 항이 모형에 남아 있으면 등고선·표면·중첩 비활성.

### 6.4 반응 최적화기·예측 (2단계)
- 상세: B 문서 5~6절.
- 목표(Maximize/Minimize/Target), Lower/Target/Upper(기본값 데이터 최소/최대), Weight·Importance 0.1~10, 공변량은 평균 고정. 출력 Parameters·Solution·Multiple Response Prediction(Fit, SE Fit, 95% CI, 95% PI).
- 픽스처: `ufm__response-optimizer__example-with-regression-models`(East 32.2129, South 34.9758, North 18.3831, D=1), `ufm__predict__example-with-a-regression-model`.

### 6.5 반응표면 (2단계)
- 상세: C 문서 1~3절.
- CCD 카탈로그(요인 수·fraction·블록 수별 cube/center/axial/α/회전성)를 룩업으로 고정. α 우선순위: 블록 없음 → 회전성(α = F^0.25), 블록 있음 → 직교 블록, Face Centered α=1, Custom. 범주형 요인은 수준마다 연속 설계 복제. BBD 허용 블록 수 고정. ANOVA 행: Model → (Blocks) → Linear → Square → 2-Way Interaction → Error → Lack-of-Fit → Pure Error → Total.
- 픽스처: `response-surface__analyze-response-surface-design__example`(SealStrength: S=4.40228, R-sq 78.58%, Lack-of-Fit 10 / 308.20, Pure Error 6 / 1.88, Total 30 / 1447.60), `topic__response-surface-designs__summary-of-central-composite-designs`, `topic__response-surface-designs__summary-of-box-behnken-designs`, `…create-central-composite-design…example`(3요인 2블록 20런), `…create-box-behnken-design…example`.

### 6.6 혼합물·선별·최적설계·분할구 (3단계)
- 상세: C 문서 4~6절, A 문서(DSD·분할구).
- 혼합물: simplex centroid / lattice(degree) / extreme vertices, 성분 상·하한, 선형 제약(최대 10), 공정변수 X1~X7, 증강(축점·중앙점 기본 ON), 단위 3종(amount/proportion/pseudocomponent), 모형 linear~full quartic, 역항 조건. 최적설계: 후보점·지시자 열 규약, D/A/G/V/최대 레버리지/조건수.
- 픽스처: `mixtures__analyze-mixture-design__example`(FondueRecipe Flavor: R-sq 99.98%, PRESS 2.65322), `…create-mixture-design…example-for-*`, `topic__factorial-and-screening-designs__available-definitive-screening-designs`, `…create-definitive-screening-design…example`, `…select-optimal-design…example-of-*`.

## 7. 수치 검증 전략

1. **설계 생성**: 생성자·정의관계·별칭 구조·런 수·블록 배정은 결정적이므로 문자열 비교. 랜덤화는 시드 고정 옵션(Minitab 의 "Base for random data generator")을 두되 Minitab 난수열과 같을 필요는 없다.
2. **엔진 자체 검증**: 카탈로그의 모든 행에 대해 생성자로부터 해상도·블록 포함 해상도를 재계산해 표와 대조한다(현재 통과, 오류 3건 기록).
3. **분석**: 예제 데이터로 적합한 뒤 표에 표시된 자릿수로 반올림해 비교한다(계수 소수 3~4자리, p 값 3자리, 퍼센트 2자리). 자릿수 규칙 자체도 Minitab 을 따른다(유효숫자 기반).
4. **데이터 확보 전 대체 정답지**: NIST/SEMATECH e-Handbook 5.4.7 예제와 Montgomery 교과서 예제(데이터·분산분석표 공개)로 분석 엔진을 먼저 검증하고, Minitab .MWX 를 받으면 문서 예제와 재대조한다.
5. 모든 테스트는 `python -m pytest`. 픽스처 로더는 `tests/conftest.py` 의 `load_fixture`, `table`.

## 8. 미해결 사항·결정 필요

1. **샘플 데이터 다운로드(사용자 승인 필요)**: InsulationProperties.MWX, SealStrength.MWX, FondueRecipe.MWX, ultrasonic_cleaner.MWX, ThermalEnergyTest.MWX, CrystalGrowth.MWX. 출처 support.minitab.com 데이터셋 라이브러리(`/en-us/datasets/media/generated-content/datasets/`), 각 수 KB. .MWX 는 zip 안의 XML 이라 Python 으로 읽을 수 있다. 저장 위치 `data/minitab_samples/`(git 제외).
2. **제품 이름**: 작업명 "DOE Studio".
3. **UI 프레임워크**: Streamlit 으로 시작, 워크시트 편집 UX 한계 시 FastAPI + React 전환 검토.
4. **Minitab 실물 확인이 필요한 항목**: 4절 2·4번(문서 오류 행), 다중 블록 생성자의 블록 번호 대응, Display Available Designs 대화상자의 표, Analyze Mixture 의 나머지 라디오 라벨, Response Trace Plot 의 Piepel 라벨, 한국어 실제 UI 문자열. Minitab 시험판을 설치하면 한 번에 확인 가능.

## 9. 단계별 계획과 완료 기준

| 단계 | 내용 | 완료 기준 |
|---|---|---|
| 0 | 조사·사양서·픽스처·뼈대 | **완료**(2026-10-31) |
| 1 | 2수준 요인설계 생성(완료) → PB·일반 완전요인·접기 → 워크시트 저장/불러오기 → 모형 적합·ANOVA·효과도·잔차 → 요인그림·입방체도 → Streamlit 화면 3개(설계 생성 → 데이터 입력 → 분석) | 6.1·6.2·6.3(요인) 픽스처 전부 통과, 화면에서 InsulationProperties 예제 재현 |
| 2 | CCD·BBD 생성, RS 분석, 등고선·표면·중첩 등고선, 반응 최적화기, 예측, 축점 추가 | 6.4·6.5 픽스처 통과 |
| 3 | 혼합물 생성·분석·궤적도, DSD, D-최적 설계, 분할구 | 6.6 픽스처 통과 |
| 4 | 보고서 내보내기(Excel/PDF), 한글/영어 전환, 사용자 피드백 반영 | 화학 연구원 2~3명 시범 사용 |

### 1단계 작업 목록(권장 커밋 단위)
1. [x] `designs/words.py`, `catalog.py`, `factorial.py` + 테스트 15개
2. [ ] `designs/plackett_burman.py`(12~48런 생성열, 중앙점은 반복마다) + 픽스처 테스트
3. [ ] `designs/general_full.py`(수준 수 임의, 설계표 1,2,3 표기) + 픽스처 테스트
4. [ ] 접기(fold)·반복 추가·재랜덤화(Display and Modify Design 의 요인설계 부분)
5. [ ] `io/worksheet.py`(설계 메타데이터 + 데이터 JSON/CSV)
6. [ ] `analysis/model.py`·`fit.py`·`anova.py`·`effects.py`·`diagnostics.py` — NIST 예제로 1차 검증 → InsulationProperties 로 2차 검증
7. [ ] `plots/` Pareto·정규·반정규·잔차 4종·주효과·교호작용·입방체도
8. [ ] `app/` 화면 3개

## 10. 저장소 시작 절차(제안)

사용자가 직접 저장소를 만들고 커밋할 때 참고할 사항.
- 첫 커밋에 넣을 것: `README.md`, `pyproject.toml`, `.gitignore`, `docs/`(사양서·요약·메뉴 트리), `doe_core/`, `tests/`(픽스처 JSON 포함), `research/*.py`·`research/urls_*.txt`.
- 넣지 않을 것(`.gitignore` 에 이미 있음): `research/minitab_docs/`(Minitab 문서 원문 사본), `data/minitab_samples/*.MWX`, 가상환경·캐시.
- 브랜치 예: `feat/designs-plackett-burman`, `feat/analysis-anova` 처럼 9절의 작업 단위마다 하나.
- 커밋 전 확인: `python -m pytest -q` 전부 통과.
