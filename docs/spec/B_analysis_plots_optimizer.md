# B. Analyze Factorial Design · 효과도/그래프 · Response Optimizer · Predict — Minitab 지원 문서 요약

작성 기준: `scratchpad/minitab_pages/en-us/` 의 텍스트 덤프(첫 줄 URL, 둘째 줄 TITLE, `[TABLE] … [/TABLE]` 표). 한국어 라벨은 `scratchpad/minitab_pages/ko-kr/` 의 같은 이름 파일에서 가져옴. 각 절 끝의 괄호가 근거 파일명. 문서에 없는 내용은 **문서에 없음**으로 표기.

---

## 0. 소스 범위와 주의

### 0.1 읽은 파일(en-us, 중복 해시본 포함 전부)

| 주제 | 파일 (해시 이름이 같은 내용인 경우 `=`로 표시) |
|---|---|
| 예제 | `doe__how-to__factorial__analyze-factorial-design__before-you-start__example.txt` |
| 대화상자 | `…perform-the-analysis__enter-your-data.txt`, `…__specify-the-model-terms.txt` (= `_1f5dc04f`), `…perform-the-analysis_926e140e.txt`(Hierarchy 프롬프트), `…__specify-covariates.txt`, `…__specify-the-analysis-options.txt` (= `_925a099d`), `…perform-the-analysis_f72c7156.txt`(Stepwise), `…__select-the-graphs-to-display.txt` (= `_86096c84`), `…__select-the-results-to-display.txt` (= `_7cca0ef9`), `…__store-statistics.txt` |
| 결과 해석 | `…interpret-the-results__key-results.txt`, `…interpret-the-result_e999876e.txt`(Method), `_dbb7aa4f`(Coefficients), `_3f8a664d`(Model summary), `_e8cb6bbc`(ANOVA), `_e92c6ce8`(Regression equation), `_d9296586`(Alias structure), `_13160164`(Fits and diagnostics), `_759ba43a`(Means), `_e6bb8b6d`(Effects plots), `_bd77adff`(Residual plots) |
| 공식 | `…methods-and-formulas__model-information.txt`, `…__analysis-of-variance.txt` (= `_fda57b56`), `…__goodness-of-fit-statistics.txt` (= `_36c5a147`), `…__fits-and-residuals.txt`, `…__diagnostic-measures.txt` (= `_7637fc22`), `…__effects-plots.txt`, `…__stepwise.txt` |
| 스크리닝 | `doe__how-to__screening__analyze-screening-design__before-you-start__example.txt`, `doe__how-to__screening__analyze-plackett-burman-design.txt` |
| 변동성 | `doe__how-to__factorial__analyze-variability__before-you-start__example.txt`, `doe__how-to__factorial__pre-process-responses-for-analyze-variability__6ad57ef4.txt` |
| 지원 주제 | `doe__supporting-topics__basics__coded-units-and-uncoded-units.txt`, `…basics__how-is-a-coefficient-for-a-main-effect-calculated.txt`, `…factorial-and-screening-designs__how-error-is-partitioned.txt` |
| using-fitted-models | Predict 4개(example, enter-your-data, all-statistics, methods-and-formulas), Factorial Plots 3개(example = `_b8e734f2`, key-results, `_94b53e84` graphs), Cube Plot 1개, Contour Plot 4개(regression example = `_1399b7e7`, mixture example, define-the-contour-values, specify-settings), Surface Plot 1개(`_7e44223b`), Overlaid Contour Plot 3개(`_24dfe365` regression, `_e9f914cd` mixture, `_41bc65ff` contours), Response Optimizer 8개(example = `_9bf1079a`, `_0d1405be` Desirability, `_ed409c24` Options, `_38561a0d` Optimizer, `_66569390` all statistics, `_767d6302` individual desirabilities, `_3318f8d9` composite desirability, average-importance) |

### 0.2 담당 목록에 있었지만 폴더에 **없는** 파일
- `doe__supporting-topics__factorial-and-screening-designs__how-minitab-handles-center-points-in-a-2-level-factorial-design.txt` → **폴더에 없음** (유사 이름 `how-minitab-adds-center-points.txt`는 설계 생성 주제라 담당 밖).
- `doe__supporting-topics__factorial-and-screening-designs__determine-the-number-of-terms-in-a-saturated-model.txt` → **폴더에 없음**.
→ 중앙점·포화 모형 처리는 다른 페이지(Terms, Graphs 주의문, Stepwise 공식, ANOVA DF, Coefficients CenterPt, error-partition)에 흩어진 문장만으로 §3.11에 정리.

### 0.3 수식은 전부 PNG 이미지
methods-and-formulas 페이지의 수식 본문은 `<img src="/en-us/minitab/png/….png">` 로만 존재하며 텍스트 덤프에는 **표기법(Notation) 표와 산문만** 남아 있다(HTML에 MathML·alt 없음, 로컬에 PNG 0개). 아래 §3에서 "[수식 이미지]"로 표시한 곳은 **문서 텍스트에 공식이 없음**을 뜻하며, 복원용으로 이미지 파일명을 부록 A에 적어 두었다. 텍스트로 남아 있는 공식(`Effect = Coefficient * 2`, `ME = t*PSE`, `F(x) = 2Φ(x) – 1`, `1 − P(F ≤ fj)`, Adj SS 분해식 등)은 원문 그대로 옮겼다.

---

## 1. Analyze Factorial Design 대화상자

메뉴: `Stat > DOE > Factorial > Analyze Factorial Design` (ko: `통계분석 > 실험계획법 > 요인 설계 > 요인 설계 분석`).

### 1.1 메인 — Responses (`…perform-the-analysis__enter-your-data.txt`)
- **Responses**: 요인으로 설명/예측할 숫자 데이터 열. 반응을 여러 개 넣으면 **반응마다 별도 모형**을 적합. (Y 변수라고도 함.)
- 예시 워크시트(열 구조가 설계 워크시트의 표준 형식):

| C1 | C2 | C3 | C4 | C5-T | C6-T | C7-T | C8 |
|---|---|---|---|---|---|---|---|
| StdOrder | RunOrder | CenterPt | Blocks | Material | Temp | Pressure | Strength |
| 1 | 2 | 1 | 1 | A | low | high | 74.32 |
| 2 | 7 | 1 | 1 | B | low | low | 76.73 |
| 3 | 3 | 1 | 1 | A | high | low | 79.85 |
| 4 | 4 | 1 | 1 | B | high | high | 75.12 |
| 5 | 1 | 1 | 1 | A | low | high | 74.33 |
| 6 | 5 | 1 | 1 | B | low | low | 75.11 |
| 7 | 6 | 1 | 1 | A | high | low | 79.66 |
| 8 | 8 | 1 | 1 | B | high | high | 75.42 |

(ko 열 이름: 표준 순서 / 런 순서 / 중앙점 / 블럭 / 원자재 / 온도 / 압력 / 강도.) 메인 대화상자의 그 밖의 필드는 문서에 없음.

### 1.2 Terms (`…__specify-the-model-terms.txt`)
- **Include terms in the model up through order**: 모형 차수 선택. 선택하면 Selected Terms 목록이 바뀜. 예: 2 선택 → Selected Terms = 모든 주효과 + 2-way 교호작용, Available Terms = 그보다 높은 차수의 교호작용 전부. (기본값은 문서에 없음.)
- **Available Terms** / **Selected Terms**: 화살표 단추(단일 화살표: 선택 항 이동, 이중 화살표: 전부 이동), 더블클릭 이동.
- **Include blocks in the model**: 설계의 블록 열에 값이 여러 개일 때만 체크박스 활성화.
- **Include center points in the model**: 중앙점 열(CenterPt)에 0이 있을 때만 활성화. 중앙점 = 숫자 요인이 low·high 중간에 설정된 런. **Note: 분할구(split-plot) 설계에서는 중앙점 사용 불가.**
- ko 라벨: 모형에 포함되는 항의 최대 차수 / 사용 가능한 항 / 선택 항 / 모형에 블럭 포함 / 모형에 중앙점 포함.

### 1.3 Terms > 비계층 모형 지정 시 Hierarchy 프롬프트 (`…perform-the-analysis_926e140e.txt`)
경로: `… > Terms > Non-Hierarchical Model Specified > Hierarchy`.
- 계층 모형 정의: 고차 항을 구성하는 모든 저차 항이 포함된 모형(A*B*C 포함 시 A, B, C, A*B, A*C, B*C 필요).
- **코드화되지 않은(uncoded) 단위의 식을 얻으려면 모형이 계층적이어야 함.**
- **Would you like Minitab to make your model hierarchical?**
  - `Add terms to make the model hierarchical (recommended)`: 표시된 항을 추가.
  - `Use the specified non-hierarchical model`: 추가하지 않음.
- **Use this choice from now on**: 기본값으로 저장, 이후 대화상자 생략(`File > Options > Linear Models > Model Hierarchy`에서 변경).

### 1.4 Covariates (`…__specify-covariates.txt`)
- **Covariates**: 공변량 열 선택, **최대 50개**. 측정 가능하지만 제어 어려운 연속 변수를 넣어 오차 분산을 줄임.

### 1.5 Options (`…__specify-the-analysis-options.txt`)
- **Weights**: 가중 회귀용 숫자 열. 가중치 ≥ 0, 반응 열과 행 수 동일. **분할구 설계에서는 사용 불가.**
- **Confidence level for all intervals**: 계수·적합치 신뢰구간 수준. 보통 95%. (신뢰구간을 표시하려면 Results > Display of Results > Expanded tables.)
- **Type of confidence interval**: `Two-sided` / `Lower bound` / `Upper bound`.
- **Box-Cox transformation** (모든 반응 > 0 필요):
  - `No transformation`
  - `Optimal λ`: 기본적으로 최적 λ를 0.5 또는 가장 가까운 정수로 반올림(–1, –0.5, 0, 0.5, 1 …). 반올림 대신 최적값 사용은 `File > Options > Linear Models > Display of Results`.
  - `λ = 0 (natural log)`
  - `λ = 0.5 (square root)`
  - `λ`: 임의값(제곱 λ=2, 역제곱근 λ=−0.5, 역수 λ=−1 등). 보통 −2~2 범위 밖은 쓰지 않음.
- **Means table**: 주효과만 / 주효과+2-way 교호작용 / 모형의 모든 항 / `Specified terms`(Available Terms ↔ Selected Terms) / 없음. 목록에 없는 항은 모형에 먼저 추가해야 함.
- ko 라벨: 가중치 / 모든 구간에 대한 신뢰 수준 / 신뢰 구간의 유형(양측·하한·상한) / Box-Cox 변환(변환 없음·최적 λ·λ = 0(자연 로그)·λ = 0.5(제곱근)·λ) / 평균 표.
- "코드화 단위 표시" 옵션: **문서에 없음**(계수는 항상 코드화 단위로 표시되고, 회귀식은 계층 모형이면 uncoded, 아니면 coded — §2.5).

### 1.6 Stepwise (`…perform-the-analysis_f72c7156.txt`)
- **분할구 설계에서는 Stepwise 사용 불가.** Terms에서 지정한 항이 후보.
- **Method**:
  - `None`: Terms의 모든 항으로 적합.
  - `Forward information criteria`: 매 단계 p-값이 가장 작은 항 추가(비계층 항 고려 + 계층 요구 설정이면 한 단계에 여러 항 진입 가능). 단계마다 정보 기준 계산. 보통 다음 중 하나가 되면 종료: (1) **8단계 연속** 기준의 새 최소값을 못 찾음, (2) 완전 모형 적합, (3) 오차 자유도 1을 남기는 모형 적합. "매 단계 계층 요구 + 한 번에 한 항만 진입" 설정이면 완전 모형 또는 오차 DF 1까지 계속. 선택한 기준(AICc 또는 BIC)이 최소인 모형의 결과를 표시.
  - `Stepwise`: 빈 모형(또는 initial/every 지정 항)에서 시작, 단계마다 항 추가 또는 제거. 모형 밖 변수의 p-값이 모두 Alpha to enter 초과이고 모형 안 변수의 p-값이 모두 Alpha to remove 이하이면 정지.
  - `Forward selection`: 빈 모형에서 시작, 가장 유의한 항 추가. 밖의 p-값이 모두 Alpha to enter 초과면 정지.
  - `Backward elimination`: 모든 후보 항에서 시작, 가장 덜 유의한 항 제거. 안의 p-값이 모두 Alpha to remove 이하면 정지. **포화 모형에 Backward elimination을 선택하면 오차 자유도를 최소한 확보하기 위해 효과가 작은 항 몇 개를 먼저 제거.**
- **Potential terms**: 항 목록과 표시자. `E = Include term in every model`(p-값 무관 강제 포함), `I = Include term in the initial model`(초기 모형 포함, 제거 가능; Method=Stepwise일 때만).
- **Criterion**: `AICc` / `BIC` (Forward information criteria용). 모수가 표본에 비해 적으면 BIC 벌점이 더 커서 BIC 최소 모형이 작음; 스크리닝처럼 모수가 많으면(예: 13-run DSD, 6개 이상 모수) AICc 최소 모형이 더 작음.
- **Alpha to enter**(Stepwise/Forward), **Alpha to remove**(Stepwise/Backward). 기본값 숫자는 문서에 없음.
- **Hierarchy** 단추(Terms에서 비계층 모형을 지정하면 비활성):
  - Hierarchical Model: `Require a hierarchical model at each step` / `Add terms at the end to make the model hierarchical`(Forward information criteria와 함께 선택하면 **오류**) / `Do not require a hierarchical model`.
  - Require hierarchy for the following terms: `All terms` / `Terms with categorical predictors`.
  - How many terms can enter at each step: `At most one term can enter at each step` / `Extra terms can enter to maintain hierarchy`.
- **Display the table of model selection details**: `Details about the method` / `Include details for each step`(단계별 계수·p-값·모형 요약).
- 참고문헌: Burnham & Anderson (2004) Sociological Methods & Research 33(2), 261-304.

### 1.7 Graphs (`…__select-the-graphs-to-display.txt`)
- **Effects Plots**: `Pareto` / `Normal` / `Half Normal` (체크 다중 선택).
  - 유의수준 α: Stepwise를 쓰지 않으면 α = 1 − (분석 신뢰수준). Backward/Stepwise 사용 시 α = Alpha to remove, Forward 사용 시 α = Alpha to enter.
  - Note: 2-수준 설계에서 **항 수 = 런 수**이면 표준화 효과 계산 불가 → 비표준화 효과 표시 + Lenth 방법으로 기준선. 일반 완전 요인 설계에서 같은 상황이면 **Pareto 차트를 만들지 않음**.
  - 2-수준 요인/Plackett-Burman: `Display only model terms` / `Display all terms`.
  - 분할구: `Display all terms, subplot effects only` / `Display all terms, subplot and whole-plot effects` / `Display only model terms, subplot effects only` / `Display only model terms, subplot and whole-plot effects`.
- **Residuals for Plots**: `Regular` / `Standardized` / `Deleted`(Studentized deleted).
- **Residual Plots**: `Individual plots` 하위 — `Histogram`, `Normal plot`, `Residuals versus fits`(이항 반응이면 logit of fits), `Residuals versus order`(x축 = 행 번호); `Four in one`; `Residuals versus variables`(변수 1개 이상 입력 — 모형 안 변수(곡면성 확인) 또는 모형 밖 중요 변수).
- 기본 선택값은 문서에 없음(예제에서는 Four in one을 수동 선택).
- ko 라벨: 효과도(Pareto 차트 / 정규 분포 / 1/2 정규 분포; 모형 항만 표시 / 모든 항 표시), 사용할 잔차(정규 잔차 / 표준화 잔차 / 외적 스튜던트화 잔차), 잔차 그림(개별 그림: 히스토그램 / 정규 확률도 / 잔차 대 적합치 / 잔차 대 순서; 네 개 모두; 잔차 대 변수).

### 1.8 Results (`…__select-the-results-to-display.txt`)
- **Display of Results**: `Simple tables` / `Expanded tables`(ANOVA, Coefficients, Model summary, Fits and Diagnostics의 확장판).
- **Method**: 기본값이 아닌 설정 요약 표.
- **Analysis of variance**.
- **Model summary**: 확장판에 PRESS, AICc, BIC 포함.
- **Coefficients**: 드롭다운 `Default coefficients`(선형 독립 계수만) / `Full set of coefficients`(마지막 선형 종속 수준 포함).
- **Regression equation**.
- **Alias structure**: `Display default interactions`(요인 2~6개: 모든 교호작용, 7~10개: 3-way까지, 10개 초과: 2-way) / `Display interactions up through order`(드롭다운; 기본보다 크면 계산 시간 증가 주의).
- **Fits and diagnostics**: `Only for unusual observations` / `For all observations`.
- **Means**: Options에서 지정한 최소제곱평균(적합 평균).
- ko 라벨: 결과 표시(단순 표 / 확장된 표) / 방법 / 분산 분석 / 모형 요약 / 계수(기본 계수 / 계수의 전체 집합) / 회귀 방정식 / 별칭 구조(기본 교호작용 표시 / 교호작용의 최대 차수 표시) / 적합치 및 진단(비정상 관측치에만 / 모든 관측치에) / 평균.

### 1.9 Storage (`…__store-statistics.txt`)
저장 열은 마지막 데이터 열 뒤, 같은 통계량을 반복 저장하면 이름 끝 번호 증가.

| 체크 항목 | 저장 열 | ko |
|---|---|---|
| Fits | `FITS` | 적합치 |
| Residuals | `RESI` | 잔차 |
| Standardized residuals | `SRES` | 표준화 잔차 |
| Deleted residuals | `TRES` | 외적 스튜던트화 잔차 |
| Leverages | `HI` | 레버리지 |
| Cook's distance | `COOK` | Cook의 거리 |
| DFITS | `DFIT` | DFITS |
| Effects | `EFFE` | 효과 |
| Coefficients | `COEF` | 계수 |
| Design matrix | 행렬 `XMAT` (`Data > Display Data`, `Data > Copy > Matrix to Columns`) | 설계 행렬 |
| Means | `SMEA` | 평균 |
| Box-Cox transformation of response | `BCRE` | 반응 변수의 Box-Cox 변환 |
| Fits for original response | `BFIT` | 원래 반응의 적합치 |
| Means for original response | `BSME` | 원래 반응의 평균 |

### 1.10 Analyze Screening Design / Plackett-Burman / Analyze Variability 대화상자 차이
- **Analyze Screening Design**(DSD 예제): Terms에 `Include the following terms` 드롭다운이 있고 예제에서 `Linear` 선택(ko: 포함할 항 → 선형). Graphs의 Residuals versus variables에 `Quiet`, `Sweep` 입력. 그 외 필드는 문서에 없음. (`doe__how-to__screening__analyze-screening-design__before-you-start__example.txt`)
- **Analyze Plackett-Burman Design**: 옵션·결과가 요인 설계 분석과 가장 유사하다고만 기술. (`doe__how-to__screening__analyze-plackett-burman-design.txt`)
- **Analyze Variability**: 메인 필드 `Response (standard deviations)`; Terms는 동일한 `Include terms in the model up through order`; Graphs에 Effects Plots `Pareto`, Residual Plots `Three in one` 선택지 존재. 선행 단계 **Pre-Process Responses for Analyze Variability**: `Standard deviations to use for analysis` → `Standard deviations already in worksheet`, `Use Std Devs in`(= Std), `Use Counts`(= N). 전처리는 출력이 없음. (`doe__how-to__factorial__analyze-variability__before-you-start__example.txt`, `…pre-process-responses-for-analyze-variability__6ad57ef4.txt`)

---

## 2. 출력표의 정확한 형식

### 2.1 Method 표 (`…interpret-the-result_e999876e.txt`, Results 페이지)
- 기본값이 아닌 설정을 요약. Box-Cox 사용 시 행: **Rounded λ**, **Estimated λ**, **95% CI for λ**. Analyze Variability 예제에서는 `Estimation | Least squares` 한 행.
- 기본적으로 최적 λ를 가장 가까운 0.5 단위로 반올림. 반올림 λ와 변환 대응:

| Lambda | Transformation |
|---|---|
| -2 | −Y^-2 = −1 / Y² |
| -1 | −Y^-1 = −1 / Y |
| -0.5 | −Y^-0.5 = −1 / (square root of Y) |
| 0 | log (Y) |
| 0.5 | Y^0.5 = square root of Y |
| 1 | Y |
| 2 | Y² |

### 2.2 Coded Coefficients (`…interpret-the-result_dbb7aa4f.txt`)
- 제목 `Coded Coefficients` (Box-Cox/변동성 시 `Coded Coefficients for Ln(Std)` 처럼 변환 반응명 붙음).
- 열: `Term | Effect | Coef | SE Coef | T-Value | P-Value | VIF`. 확장표에서는 **95% CI** 열 추가(`Confidence Interval for coefficient (95% CI)`). Analyze Variability에서는 `Effect` 뒤에 `Ratio Effect` 열 추가.
- 행 순서(예제): Constant → 공변량 → 주효과(요인) → 2-way 교호작용 … (설계행렬 순서와 같음: Constant, Covariates, Blocks, Factors, Interactions).
- **Effect**: 요인·요인 간 교호작용에만 계산. low→high 변화에 따른 평균 반응 변화. **Effect = 2 × 코드화 계수.** Constant·공변량·블록·CenterPt는 Effect 비어 있음(계수만).
- **Coef**: 다중공선성 최소화를 위해 **모두 코드화 단위**. 공변량 계수는 공변량의 원단위. 블록은 (−1, 0, +1) 코딩, 각 계수 = 블록 평균 − 전체 평균. **CenterPt는 (0, 1) 코딩: 요인점(factorial points)에서 1(기준 수준), 중앙점에서 0.** CenterPt 계수는 요인 수만큼의 2차 효과가 별칭이라 보통 해석하지 않음.
- **SE Coef**, **T-value** = Coef / SE Coef, **P-Value**(귀무가설: 계수 = 0).
- **VIF**: 대부분의 요인 설계에서 1. 공변량 포함, botched run, 이항 반응에서 증가. 지침표: `VIF = 1` Not correlated / `1 < VIF < 5` Moderately correlated / `VIF > 5` Highly correlated. Constant 행의 VIF는 비어 있음.
- DSD(screening) 예제의 Coded Coefficients에는 **Effect 열이 없음**(`Term | Coef | SE Coef | T-Value | P-Value | VIF`).

### 2.3 Model Summary (`…interpret-the-result_3f8a664d.txt`)
- 기본 열: `S | R-sq | R-sq(adj) | R-sq(pred)`. 확장표: **PRESS, AICc, BIC** 추가(단계별 상세에도 표시). 분할구 설계: **S(WP), R-sq(SP), R-sq(WP)** 추가, 분할구에서는 AICc/BIC 표시 안 함. Mallows' Cp는 설명만 있고 어느 표에 나오는지 문서에 없음(단계별 선택 맥락).
- R-sq(adj), R-sq(pred)의 계산값이 음수면 **0으로 표시**.
- S(WP) = 전구(whole plot) 간 오차 표준편차 추정치; 분할구에서 S = 하위구(subplot) 오차 표준편차.

### 2.4 Analysis of Variance (`…interpret-the-result_e8cb6bbc.txt`, 예제들)
- 열: `Source | DF | Adj SS | Adj MS | F-Value | P-Value`. 확장표/옵션: `Seq SS`, `Contribution`(각 Source의 총 Seq SS 대비 %). 설계 분석에서는 p-값 계산에 **Adj SS만** 사용(Seq SS는 표시용).
- Source 행 종류와 순서(예제에서 확인된 것):
  1. `Model`
  2. `Covariates` (그룹) → 개별 공변량 행(예: `MeasTemp`)
  3. `Blocks` (문서에 F·P 해석 있음; 위치는 문서상 명시 없으나 설계행렬 순서 Covariates→Blocks→Factors를 따름)
  4. `Linear` (그룹) → 개별 주효과 행
  5. `2-Way Interactions` (그룹) → 개별 2-way 행; 이어서 `3-Way Interactions` 등(그룹 이름 패턴은 예제의 2-Way만 확인됨)
  6. `Curvature` — 중앙점 항이 모형에 있으면 Model 쪽, 없으면 Error 쪽에 속함. DF는 항상 1.
  7. `Error` → 하위 `Lack-of-Fit`, `Pure Error` (조건 충족 시)
  8. `Total`
- Error 분할 조건(둘 다 충족 시 Lack-of-Fit/Pure Error 행 생성): (1) 현재 모형에 없지만 데이터로 적합 가능한 항이 있음(블록이 설계에 있으나 모형에 없는 경우 등; CenterPt 항은 항상 Curvature용이라 여기 해당 안 함). (2) 데이터에 반복(replicates)이 있음 — 블록·공변량을 포함해 모든 예측변수 값이 같은 관측치(같은 블록의 중앙점 2개는 반복; 다른 블록이고 블록 항이 모형에 있으면 반복 아님).
- Adj SS 정의(원문): Model = 총 SS − 오차 SS(= 항들의 Seq SS 합); 그룹 = 그룹 내 항의 Seq SS 합; 항 = 다른 항만 있는 모형 대비 모형 SS 증가분; Error = 잔차 제곱합; Curvature = 중앙점 항이 설명하는 변동; Pure Error = 요인·블록·공변량 값이 같은 관측치 내 변동; Total = Model + Error.
- Adj MS of Error = MSE = s².
- Lack-of-fit 검정: 블록이나 공변량이 stepwise로 제거되었으면 그 항들도 LOF에 포함.
- Curvature p-값이 유의하지 않으면 보통 중앙점 항을 제거. **중앙점 항을 모형에 남기면 Contour Plot, Surface Plot, Overlaid Contour Plot 사용 불가, Response Optimizer는 요인 수준 사이를 보간하지 않음.**

### 2.5 Regression Equation (`…interpret-the-result_e92c6ce8.txt`)
- 제목 `Regression Equation in Uncoded Units`(계층 모형) / 비계층 모형이면 **코드화 단위**로 표시(제목은 문서에 없음, "in coded units").
- 형식: `[반응] | = | 52.7 - 1.229 MeasTemp + 10.43 Material + …` (한 행, 항 사이 공백·부호).
- uncoded 식에서 범주형 변수는 −1/+1, CenterPt 변수는 모든 연속 요인이 중점이면 1 아니면 0, **블록은 평균화되어 식에 없음**. coded 식에서도 공변량은 항상 원단위.
- Box-Cox/변동성: `Ln(Std) | = | …`.

### 2.6 Fits and Diagnostics for Unusual Observations (`…interpret-the-result_13160164.txt`, 진단 공식 페이지)
- 열(문서의 항목 순서): `Fit`, `SE Fit`, 확장표 `95% CI`, `Resid`, `Std Resid`, `Del Resid`(deleted Studentized), `Hi`(leverage), `Cook's D`, `DFITS`. (Obs·관측값 열 등 표 머리글 전체는 예제가 없어 문서에 없음.)
- 플래그 기준:
  - **R**: 표준화 잔차 |Std Resid| > 2 (deleted Studentized도 |·| > 2면 큼). 대략 5%가 R로 표시될 것으로 기대.
  - **X**: 레버리지 Hi > **3p/n 또는 0.99 중 작은 값**(p = 계수 수(상수 포함), n = 관측치 수).
  - Cook's D 참고 기준: D > F-분포 중앙값 F(0.5, p, n−p). (표 플래그 아님.)
  - DFITS 참고 기준: 문서에 공식 이미지(`Term: p = number of model terms, n = number of observations`)만 있음 → 수치 기준은 **문서 텍스트에 없음**.

### 2.7 Alias Structure (`…interpret-the-result_d9296586.txt`, 예제들)
- 두 표: `Factor | Name`(A, B, C… ↔ 요인 이름), `Aliases`(한 줄에 한 식: `I + ABC`, `A + BC` …).
- 표시 범위: 요인 ≤ 7 → 모든 별칭; 8–10 → 3-factor 교호작용까지; 11–15 → 2-factor까지. (Results 대화상자 기본값 설명과 약간 다르게 적혀 있음 — 대화상자: 2~6 전부, 7~10 3-way, >10 2-way.) 제목에 `Alias Structure (up to order 2)`처럼 차수 표기(DSD 예제).
- 완전 별칭은 계수 1; **부분 별칭**(공변량 포함 요인 설계, 이항 반응, Plackett-Burman, DSD)은 1이 아닌 계수(`I - 5.42 ABC + 28.92 ABD …`). 계수는 모형 밖 항이 모형 내 항 추정을 편향시키는 정도.
- 블록 설계: `Block 1 - ABC`, `Block 2 + ABC`, `Block 3 - ABC` 형식. 블록 항은 교호작용보다 먼저 모형에 들어가므로 블록과 별칭인 ABC는 포함되지 않음. 완전 별칭 항을 함께 넣으면 항 목록에서 **뒤에 있는 항을 제거**.

### 2.8 Means (`…interpret-the-result_759ba43a.txt`)
- 열: `Term | Fitted Mean | SE Mean`. 요인 행(빈 값) 아래 수준 행; 교호작용은 수준 조합을 공백으로 나열(`85 25`). 공변량 행은 `Data Mean`(공변량 평균, 적합 평균 계산 시 이 값으로 고정)과 `Standard Deviation (StDev)` 표시.
- 예제(InsulationProperties Strength, 축소 모형):

| Term | Fitted Mean | SE Mean |
|---|---|---|
| Material | | |
| Formula1 | 26.269 | 0.480 |
| Formula2 | 32.998 | 0.480 |
| InjPress | | |
| 75 | 26.980 | 0.480 |
| 150 | 32.287 | 0.480 |
| InjTemp | | |
| 85 | 27.487 | 0.480 |
| 100 | 31.780 | 0.480 |
| CoolTemp | | |
| 25 | 31.593 | 0.480 |
| 45 | 27.674 | 0.480 |
| InjTemp*CoolTemp | | |
| 85 25 | 30.351 | 0.679 |
| 100 25 | 32.834 | 0.679 |
| 85 45 | 24.623 | 0.679 |
| 100 45 | 30.726 | 0.679 |

### 2.9 한국어 출력 라벨 매핑 (ko-kr 예제·ANOVA·계수 페이지)

| 영어 | 한국어 |
|---|---|
| Coded Coefficients | 코드화된 계수 |
| Term / Effect / Coef / SE Coef / T-Value / P-Value / VIF | 항 / 효과 / 계수 / SE 계수 / T-값 / P-값 / VIF |
| Constant | 상수 |
| Model Summary | 모형 요약 |
| S / R-sq / R-sq(adj) / R-sq(pred) | S / R-제곱 / R-제곱(수정) / R-제곱(예측) |
| R-sq(WP) / R-sq(SP) / PRESS / Log-likelihood / Mallows' Cp | R-제곱(WP) / R-제곱(SP) / PRESS / 로그 우도 / Mallows의 Cp |
| Analysis of Variance | 분산 분석 |
| Source / DF / Adj SS / Adj MS / F-Value / P-Value | 출처 / DF / Adj SS / Adj MS / F-값 / P-값 |
| Seq SS / Contribution | Seq SS / 기여 |
| Model / Covariates / Blocks / Linear / 2-Way Interactions / Curvature / Error / Lack-of-Fit / Pure Error / Total | 모형 / 공변량 / 블럭 / 선형 / 2차 교호작용 / 곡면성 / 오차 / 적합성 결여 / 순수 오차 / 총계 |
| Regression Equation in Uncoded Units | 코드화되지 않은 단위의 회귀 방정식 |
| Alias Structure (up to order 2) | 별칭 구조(2차까지) |
| Factor / Name / Aliases | 요인 / 이름 / 별칭 |
| Means / Fitted Mean | 평균 / 적합 평균 |
| Fits and Diagnostics (for Unusual Observations) | 적합치 및 진단 (비정상 관측치) |
| Fit / SE Fit / Resid / Std Resid / Deleted residual / Hi (leverage) / Cook's distance / DFITS | 적합치 / SE 적합치 / 잔차 / 표준화 잔차 / 외적 스튜던트화 잔차 / 레버리지 / Cook의 거리 / DFITS |
| Method / Estimation / Least squares | 방법 / (문서에 없음) |
| Pareto Chart of the Standardized Effects / …of the Effects | 표준화된 효과의 Pareto 차트 / 효과의 Pareto 차트 |
| Normal Plot of the Standardized Effects / Normal Plot of the Effects | 표준화된 효과의 정규 확률도 / 효과의 정규 확률도 |
| Half Normal Plot of the Standardized Effects | 표준화된 효과의 1/2 정규 확률도 |
| Lenth's pseudo standard error (PSE) / margin of error (ME) | Lenth의 유사 표준 오차(PSE) / 오차 한계 |
| Residuals versus fits / order / variables; Histogram; Normal plot | 잔차 대 적합치 / 순서 / 변수; 히스토그램; 정규 확률도 |
| 예제 요인/반응 이름 | Strength=강도, MeasTemp=측정온도, Material=재료, InjPress=주입압력, InjTemp=주입온도, CoolTemp=냉각온도, Insulation=절연, Formula1/2=공식1/2; DSD: Power=동력, Train=훈련, Degas=가스 제거, Burst=파열, Quiet=무음, Center=중심, Bandwidth=대역폭, Sweep=제거; Heat Flux=열량, Insolation=일사량, East/South/North=동쪽/남쪽/북쪽 |

---

## 3. 공식 (methods-and-formulas 원문 — 텍스트로 남은 부분 그대로)

### 3.1 모형 정보 (`…methods-and-formulas__model-information.txt`)
**Design matrix**: GLM과 같은 방식. X의 열 = 모형 항. 열 순서: **Constant → Covariates → Blocks → Factors → Interactions**. Constant·covariate·continuous factor는 각 1열. 블록은 (블록 수 − 1)열. 2-수준 설계: 범주형 요인 1열, 교호작용도 1열. 일반 요인 설계: 범주형 요인은 (수준 수 − 1)열, 4수준 A의 코딩:

| Level of A | A1 | A2 | A3 |
|---|---|---|---|
| 1 | 1 | 0 | 0 |
| 2 | 0 | 1 | 0 |
| 3 | 0 | 0 | 1 |
| 4 | -1 | -1 | -1 |

교호작용 열 = 구성 요인 열들의 곱(A 6수준·C 3수준·D 4수준 → A*C*D는 5×2×3=30열). 분할구: 설계행렬 2종(일반 2-수준용 + 전구(whole plot) 열 블록 포함판; 전구 열은 hard-to-change 요인·그 교호작용 열 뒤). 이항 반응 분할구는 분석 안 함.

**Effects**: 2-수준 모형에서만 계산(일반 요인 모형은 없음). 원문: `Effect = Coefficient * 2`

**Coefficients (Coef)**: 요인마다 k − 1개(k = 수준 수). 2-요인 2-수준 완전요인 모형의 계수·SE 공식은 [수식 이미지]. Notation: (ȳ_A+) 요인 A high 수준에서 y 평균 / (ȳ) 전체 평균 / (ȳ_B+) B high 수준 평균 / (ȳ_AB+) A·B 모두 high 평균 / MSE 평균제곱오차 / n = 추정 항에 대한 (공분산 행렬의) −1과 1의 수. 그 이상은 Montgomery (1991) 3판 참조.

**Box-Cox transformation**: 잔차 제곱합을 최소화하는 λ 선택 [수식 이미지]. 변환 = λ ≠ 0이면 Y^λ, λ = 0이면 ln(Y). **λ < 0이면 변환값에 −1을 곱해 원 반응의 순서 유지.** 최적값 탐색 범위 −2 ~ 2. 표: λ = 2 → Y′ = Y², λ = 0.5 → Y′ = √Y [이미지], λ = 0 → Y′ = ln(Y), λ = −0.5 → [이미지], λ = −1 → Y′ = −1 / Y.

**Weighted regression**: 분산 큰 관측치에 작은 가중치, 작은 분산에 큰 가중치. 통상 가중치 = 순수 오차 분산의 역수. 추정 계수 공식 [수식 이미지] = 가중 SS Error 최소화와 동치. Notation: X 설계행렬, X′ 전치, W 대각 가중치 n×n, Y 반응 벡터, n, wi, yi, ŷi.

### 3.2 분산분석 (`…methods-and-formulas__analysis-of-variance.txt`)
**Sum of squares (SS)**: 완전요인 2-요인(A, B) 모형 기준. SS Total = 총 변동; SS(A), SS(B) = 추정 요인 수준 평균의 전체 평균 대비 편차 제곱합; SS Error = 잔차 제곱합(처리 내 오차) [수식 이미지들]. 반복이 있으면 SS Pure Error [이미지]; 축소 모형이면 SS Lack of Fit [이미지]; 중앙점이 있으면 SS Curvature [이미지]; 분할구는 전구/하위구 오차 SS [이미지]. Notation: a, b = 수준 수; n = 총 반복 수; ȳi. = A i수준 평균; ȳ = 전체 평균; ȳ.j = B j수준 평균; yijk = A i수준·B j수준·k번째 반복 관측치; ȳij = 셀 평균; ȳC = **중앙점 평균 반응**; ȳF = **요인점 평균 반응**; nF = 요인점 수.

**Sequential sum of squares**: 항 입력 순서에 의존; 앞선 항이 주어졌을 때 그 항이 설명하는 SS Regression의 고유 부분.

**Adjusted sum of squares** (원문):
```
SSR(X3 | X1, X2) = SSE (X1, X2) - SSE (X1, X2, X3)  or
SSR(X3 | X1, X2) = SSR (X1, X2, X3) - SSR (X1, X2)
SSR(X2, X3 | X1) = SSE (X1) - SSE (X1, X2, X3)  or
SSR(X2, X3 | X1) = SSR (X1, X2, X3) - SSR (X1)
```
(Neter, Wasserman, Kutner 1985.)

**Degrees of freedom (DF)**: A, B, 블록 변수가 있는 완전요인 설계의 각 SS 자유도 [수식 이미지]. 교호작용 DF = 구성 항 DF의 곱; 항 유형(예: 주효과)의 DF = 그 항들의 DF 합. **2-수준 설계의 Curvature DF = 1.** Notation: a, b, c = 블록 수, n = 총 관측치, ni = i번째 요인수준조합의 관측치 수, m = 요인수준조합 수, p = 계수 수.

**Adj MS – Term**: [수식 이미지] (MS = SS/DF 형태라는 문장은 없음).

**F**: 모형 항의 F 공식 [수식 이미지]. 분자 DF = 항의 DF, 분모 DF = 오차 DF. 균형 분할구: hard-to-change 요인의 F는 분모에 whole plot error MS; 비균형 분할구: WP Error와 SP Error의 선형결합(기대 평균제곱 기반).

**P-value – ANOVA**: F-분포, 분자 DF = 검정 항들의 DF 합, 분모 DF = 오차 DF. 원문 공식: `1 − P(F ≤ fj)`.

**Pure error lack-of-fit test**: (1) 각 반복 집합 내 평균으로부터의 편차 제곱합을 더해 SS PE; (2) 순수 오차 MS [이미지], n = 관측치 수, m = 서로 다른 x-수준 조합 수; (3) 적합성 결여 SS [이미지]; (4) 적합성 결여 MS [이미지]; (5) 검정 통계량 [이미지]. 큰 F·작은 p → 모형 부적절.

**P-value – Lack-of-fit**: 귀무가설 "데이터로 추정 가능하지만 모형에 없는 모든 항의 계수 = 0". 분자 DF = LOF DF, 분모 DF = 순수 오차 DF. `1 − P(F ≤ fj)`.

### 3.3 적합도 통계량 (`…methods-and-formulas__goodness-of-fit-statistics.txt`)
- **S**: [수식 이미지], Notation: MSE.
- **R-sq**(결정계수): [이미지], Notation: yi, ȳ, ŷi.
- **R-sq (adj)**: [이미지]. 음수면 0 표시. Notation: yi, ŷi, ȳ, n, **p = 모형의 항 수**.
- **R-sq (pred)**: [이미지]. 음수면 0 표시. Notation: yi, ȳ, n, ei, hi = X(X′X)⁻¹X′의 i번째 대각원소, X.
- **PRESS**: [이미지]. Notation: n, ei, hi.
- **R-sq (WP)**: [이미지]. SS(WPerror) = 전구 오차 항 SS; SS Total (WP) = 전구 오차 항과 hard-to-change 요인만 포함하는 모든 항의 Seq SS 합.
- **R-sq(SP)**: [이미지]. SS(SPerror); SS Total (SP) = SS Total − SS Total(WP).
- **Log-likelihood**: 비가중 [이미지], 가중 [이미지]. 가중치 0인 관측치는 분석에서 제외. Notation: n, **R = 모형의 오차 제곱합**, wi.
- **AICc**: [이미지]. "AICc is not calculated when [조건 이미지]". Notation: n, **p = 상수 포함 계수 수**.
- **BIC**: [이미지]. Notation: p(상수 포함), n.
- **Mallows' Cp**: [이미지]. Notation: SSEp = 고려 중인 모형의 SSE, MSEm = 모든 후보 항을 넣은 모형의 MSE, n, p = 상수 포함 항 수.

### 3.4 적합치·잔차·구간 (`…methods-and-formulas__fits-and-residuals.txt`)
- **Fit**: [이미지]. Notation: ŷ, xk = k번째 항(단일 예측변수·다항·교호작용), bk.
- **Residuals**: 관측값 − 적합치 [이미지]. Notation: yi, ŷi.
- **Standardized residual (Std Resid)** = 내적 스튜던트화 잔차: [이미지]. Notation: ei, hi = X(X′X)⁻¹X′의 i번째 대각, s² = MSE, X, X′.
- **Deleted (Studentized) residuals** = 외적 스튜던트화 잔차: 공식 [이미지], 다른 표현 [이미지]. i번째 관측치를 뺀 모형으로 추정. 각 삭제 잔차는 자유도 [이미지]인 t-분포. Notation: ei, s(i)² = i 제외 MSE, hi, n, p = 상수 포함 항 수, SSE.
- **Whole plot residuals**: [이미지]. ŷ(full, 전구 오차 항 포함) − ŷ(고정효과만).
- **SE Fit**: 예측변수 1개 [이미지], 여러 개 [이미지], 가중회귀(가중치 행렬 포함) [이미지]. 테스트 데이터/K-fold 시에도 동일 공식, s²·설계행렬·가중행렬은 훈련 데이터 기준. Notation: s², n, x0(새 값/벡터, 상수항 1로 시작), x̄, xi, x′0, X, W.
- **SE Fit (분할구)**: 계수 SE = 공분산 행렬 대각원소 제곱근 [이미지]; CI용 SE [이미지]; PI용 SE [이미지]. Notation: σ²_SP = MSE(SP); X = n×p(요인·공변량·블록·전구 오차 항); σ²_WP = 균형설계에서 [이미지]; m = 전구 내 하위구 수; Z = n×w 전구 지시행렬; n, p, w = 전구 수; x 행벡터; Cov(β); β.
- **Confidence interval**: [이미지]. Notation: (t 분위수 — 이미지), ŷ, α(제1종 오류율), n, p = 모형 모수 수, S²(b) = 계수 분산-공분산 행렬, s², X, X0(p×1), X′0.
- **Prediction interval**: [이미지]. Notation: s(Pred) = [이미지], ŷ, α, n, p, s², X, X0, X′0.

### 3.5 진단 측도 (`…methods-and-formulas__diagnostic-measures.txt`)
- **Leverages (Hi)**: 모자행렬 H(n×n 투영행렬) [이미지]의 i번째 대각원소. 예측변수 값이 평균 벡터에서 (Mahalanobis 거리로) 멀면 큼. 0~1. **3p/n 또는 .99 중 작은 값 초과 → X 표시.** Notation: X, hi, p = 상수 포함 항 수, n.
- **Cook's distance**: 레버리지·표준화 잔차로 계산, 관측치 제외 재적합 없이 계산 [이미지]. Notation: ei, hi, p(상수 포함 모수 수), s², b, b(i), X.
- **DFITS**: 레버리지 + 외적 스튜던트화 잔차 결합; 관측치 제거 시 적합치가 변하는 표준편차 수 [이미지]. Notation: ei, hi, X, ŷi, ŷ(i), MSE(i), n, p.

### 3.6 효과도 (`…methods-and-formulas__effects-plots.txt`) — 전부 텍스트로 존재
**Normal probability plot**
- 오차 DF ≥ 1: 정규점수/확률/백분율 vs **표준화 효과**. 선 = 표준편차 1인 정규분포. **p-값 < α** 인 효과에 유의 라벨. 제목 `Normal Plot of the Standardized Effects`.
- 오차 DF = 0: vs **비표준화 효과**. 선 = 표준편차가 Lenth PSE인 정규분포. |효과| > ME 이면 유의 라벨. 원문: `ME = t*PSE` — t는 **자유도 = (효과 수 / 3)** 인 t-분포의 (1 – α / 2) 분위수. 제목 `Normal Plot of the Effects`.

**Half normal plot**
- 오차 DF ≥ 1: 표준화 효과, 선 = SD 1 정규, p < α 라벨, 제목 `Half Normal Plot of the Standardized Effects`.
- 오차 DF = 0: 비표준화 효과, SD = PSE, |효과| > ME = t*PSE(df = 효과 수/3).
- 반정규 plot point는 표준정규 절대값 분포 기반, 누적분포함수 원문: `F(x) = 2Φ(x) – 1` (Φ = 표준정규 CDF).

**Pareto chart**
- 오차 DF ≥ 1: 빨간 기준선을 **t = 자유도가 오차 DF인 t-분포의 (1 – α / 2) 분위수** 위치에. 제목 `Pareto Chart of the Standardized Effects`.
- 오차 DF = 0: 기준선 = `ME = t*PSE`(df = 효과 수/3). 제목 `Pareto Chart of the Effects`.

**Lenth's pseudo standard error (PSE)** (원문 4단계):
1. 효과의 절대값 계산
2. S = 1.5 × (1단계 효과들의 중위수)
3. 2.5 × S 보다 작은 효과들의 중위수 계산
4. PSE = 1.5 × (3단계 중위수)

### 3.7 Stepwise 공식 (`…methods-and-formulas__stepwise.txt`)
- **Forward information criteria**: §1.6과 동일 기술(8단계 연속 개선 없음 / 완전 모형 / 오차 DF 1).
- **Forward selection**: stepwise와 같은 방법으로 추가, 한 번 추가되면 제거 없음. 후보 중 p < Alpha to enter 인 변수가 없으면 종료.
- **Stepwise method**: F-검정으로 추가/삭제. **초기 모형이 모든 자유도를 쓰면(포화) — Analyze Factorial Design·Analyze Variability에서는 분석을 멈추지 않고 항의 ¼을 제거**해 자유도를 확보(제거 수는 반올림 정수, **최대 9**). 포화 모형에서 **Adj SS가 가장 작은 항부터, 계층 유지하며** 제거; 제거된 항은 이후 단계에서 재고려하지 않고 model selection details 표에 나열.
  - 제거: 모형 내 각 변수의 F [이미지]. Notation: SSE(j – Xr) = xr 없는 모형 SSE, SSE j, MSE j. p > Alpha to remove 이면 p 최대 변수 제거.
  - 추가: 모형 밖 각 변수의 F [이미지]. Notation: SSE j(추가 전), SSE(j + Xa), DF(Xa) [이미지], MSE(j + Xa). p < Alpha to enter 이면 p 최소 변수 추가. 더 못 넣고 못 빼면 종료.
- **Backward elimination**: 전체 항에서 한 번에 하나씩 제거, 재진입 없음. 포화 모형 처리 규칙은 Stepwise와 동일(¼ 제거, 최대 9, Adj SS 최소·계층 유지).

### 3.8 오차 분할: 순수 오차·곡면성·적합성 결여 (`…how-error-is-partitioned.txt`)
- 잔차 오차 DF = 총 런 수 − 추정 모수 수(상수, 공변량, 블록 계수, 중앙점 계수, 주효과, 교호작용 포함). 잔차 오차 SS = 모든 런의 잔차 제곱합.
- **Pure error**: 반복(모형 항 수준이 완전히 같은 런)이 있으면 집합마다 r − 1 DF. 원문: `m*(r - 1) + (c - 1)` — m = 모형의 모서리점(corner point) 수, r = 반복 수, c = 중앙점 수. SS = 각 반복 집합 내 평균으로부터의 편차 제곱합. 비반복 설계라도 한 요인의 모든 항을 제거하면 요인이 하나 적은 반복 설계가 되어 오차 항이 생김(예: 3요인 비반복에서 ABC, AC, BC, C 제거 → A, B 2요인 반복 설계).
- **Curvature**: 중앙점이 있으면 중앙점 항을 모수로 넣거나 곡면성을 오차 성분으로 둠. 어느 쪽이든 **DF 1**. SS = 중앙점 항을 추가했을 때 잔차 오차 SS의 감소량.
- **Lack-of-fit**: 반복이 있고 모형이 비포화이면 존재. DF = 잔차 오차 DF − 순수 오차 DF − (해당 시) 곡면성 DF. SS = 잔차 오차 SS − 순수 오차 SS − (해당 시) 곡면성 SS. 모형에서 생략된 추정 가능한 모든 교호작용 항의 총효과를 나타냄.

### 3.9 주효과 계수 계산 (`…how-is-a-coefficient-for-a-main-effect-calculated.txt`)
- 일반식 [수식 이미지] — Notation: X 설계행렬, Y 반응 벡터.
- 균형·직교·공변량 없는 설계에서 (−1, 0, 1) 코딩이면 **계수 = 해당 수준 평균 − 전체 평균**. 예(Correction Time 평균, Rows: Experience, Columns: RoadType):

```
          Dirt   Gravel  Paved   All
Advanced  15.00  7.00    7.50    9.83
Beginner  20.00  18.00   10.00   16.00
All       17.50  12.50   8.75    12.92
```

| Factor/Level | Mean | Effect |
|---|---|---|
| Experience: Advanced | 16 | 16 – 12.92 = 3.08 |
| Experience: Beginner | 9.83 | 9.83 – 12.92 = -3.08 |
| RoadType: Dirt | 17.5 | 17.5 - 12.92 = 4.58 |
| RoadType: Gravel | 12.5 | 12.5 - 12.92 = -0.42 |
| RoadType: Paved | 8.75 | 8.75 - 12.92 = -4.17 |

(문서의 표에서 Advanced와 Beginner의 Mean이 뒤바뀌어 적혀 있음 — 원문 그대로 옮김.) 각 요인의 효과 합은 반올림 오차 외 0.

### 3.10 코드화 단위 vs 비코드화 단위 (`…coded-units-and-uncoded-units.txt`)
- low = −1, high = 1. 예: Pressure 310/380, Primer Type One/Two.

| Uncoded: Pressure | Primer Type | Adhesion | | Coded: Pressure | Primer Type | Adhesion |
|---|---|---|---|---|---|---|
| 310 | One | 4.52 | | -1 | -1 | 4.52 |
| 380 | One | 4.55 | | 1 | -1 | 4.55 |
| 310 | Two | 5.05 | | -1 | 1 | 5.05 |
| 380 | Two | 4.69 | | 1 | 1 | 4.69 |

- **기본적으로 코드화 단위로 분석.** 계수를 공통 척도로 비교 가능. 비코드화로 분석하면 직교성이 깨질 수 있음(직교 → 항을 제거해도 나머지 추정치 불변).

### 3.11 중앙점 처리와 포화 모형 처리 (여러 페이지 종합; 전용 문서 2개는 폴더에 없음)
- CenterPt 열: 요인점 = 1, 중앙점 = 0. 체크박스는 0이 있을 때만 활성. 분할구에는 없음. (Terms 페이지)
- 중앙점 항이 모형에 있으면 ANOVA의 Curvature 행이 Model 아래, 없으면 Error 아래(검정용 오차에 포함). DF 1. (ANOVA 페이지, 공식 페이지)
- SS Curvature 계산 Notation에 중앙점 평균 ȳC, 요인점 평균 ȳF, 요인점 수 nF 사용 — 공식 자체는 이미지. (ANOVA 공식)
- 회귀식에서 CenterPt 변수는 모든 연속 요인이 중점일 때 1, 아니면 0. (Regression equation 페이지)
- 유의하지 않으면 제거 권장; 남기면 등고선/표면/중첩 등고선 불가, Optimizer 보간 없음. (ANOVA 페이지)
- **포화 모형**: 2-수준 설계에서 항 수 = 런 수이면 표준화 효과 불가 → 비표준화 효과 + Lenth. 일반 완전요인이면 Pareto 생략. (Graphs/Effects plots 페이지) Stepwise/Backward 시작 시 ¼(최대 9) 제거. (Stepwise 공식) Backward elimination 대화상자 설명: "removes a few terms with small effect to obtain a minimal number of error degrees of freedom". "포화 모형의 항 수 결정" 규칙 자체는 **문서에 없음**.

---

## 4. 그래프 사양

### 4.1 Pareto / Normal / Half Normal (`…interpret-the-result_e6bb8b6d.txt`, `…methods-and-formulas__effects-plots.txt`, key-results)
- **Pareto chart of the standardized effects**: |표준화 효과| 를 **큰 순서로** 막대. 표준화 효과 = 효과 = 0 귀무가설의 t-통계량. 기준선(빨간 선)은 §3.6. 예시 문장: "factors C, B, and BC cross the reference line that is at 2.31" (α = 0.05). 막대 라벨은 요인 문자(A, B, …, AB, BD …) — 예제 해석에서 "injection pressure (B)", "BD" 사용. 방향(부호)은 알 수 없음.
- **Normal plot of the standardized effects**: x = 표준화 효과, y = 정규 점수/확률/백분율. 음 효과 왼쪽, 양 효과 오른쪽. 유의/비유의 점의 **색과 모양이 다름**, 유의 점에 라벨. 적합선 = 모든 효과가 0일 때 기대 위치.
- **Half normal plot**: |표준화 효과| 를 크기순, 유의 점은 오른쪽, 라벨 표시, 점 색·모양 구분.
- 세 그래프 모두: 오차 DF = 0이면 비표준화 효과 + Lenth(제목에서 "Standardized" 빠짐).
- `Display only model terms` / `Display all terms` 옵션(§1.7).

### 4.2 Residual plots (`…interpret-the-result_bd77adff.txt`, Graphs 페이지)
- Histogram of residuals(≈20개 이상일 때 유효; 정규성 판단엔 쓰지 말 것), Normal probability plot of residuals(잔차 vs 정규 기대값; S-curve 긴 꼬리, 역S 짧은 꼬리, 아래로 굽음 오른쪽 치우침), Residuals versus fits(y 잔차, x 적합치; 이항이면 logit of fits), Residuals versus order(수집 순서, x = 행 번호), Residuals versus the variables(지정 변수).
- Four in one = 위 4개를 한 그래프에. Analyze Variability에는 Three in one 선택지(구성은 문서에 없음).
- 잔차 종류 선택: Regular / Standardized / Deleted.
- 패턴 표(Residuals vs fits): Fanning/uneven spreading → Nonconstant variance; Curvilinear → missing higher-order term; far from zero → outlier; far in x-direction → influential point. (Normal plot) Not a straight line → Nonnormality; point far from line → outlier; changing slope → unidentified variable. (Histogram) long tail → skewness; isolated bar → outlier. 해결책: 비등분산 → Box-Cox 또는 가중치.

### 4.3 Factorial Plots — Main Effects / Interaction (`using-fitted-models__how-to__factorial-plots__*`)
- 메뉴 `Stat > DOE > Factorial > Factorial Plots`(ko: 요인 그림). 메인: `Response` 선택, `Variables to Include in Plots`(Available → Selected). 저장된 모형(…_model.MWX) 사용.
- Graphs: `Main effects plot`(변수마다), `Interaction plot` — 변수 2개 이상일 때 `Display lower left matrix`(쌍마다 1개) / `Display full matrix`(전치 포함 전체 행렬: 각 변수가 x축과 범례에 모두 나타남).
- **적합 평균(fitted means)** 표시(연속 반응 = 평균, Poisson = 평균, 이항 = 확률, Analyze Variability = 표준편차). **혼합물 설계는 데이터 평균만.** 혼합효과 모형은 조건부 평균.
- Main effects plot: 범주형 예측변수는 수준별 점 + 연결선, **연속·Poisson 반응에 전체 평균 기준선**; 연속 예측변수는 연속 관계 선. 수평선 = 주효과 없음.
- Interaction plot: x축 예측변수의 값에서 적합 평균; 두 번째 예측변수가 범주형이면 수준별 선, **연속이면 표본의 최저·최고값 두 선**. 평행선 = 교호작용 없음.
- Cube Plot 대화상자에는 `Type of means to use in plots`(예: `Fitted means`)가 있으나, Factorial Plots 메인에서 data means/fitted means 선택지가 있는지는 **문서에 없음**.
- 예제(InsulationProperties_model, Response = Insulation, 변수 Material·InjTemp·CoolTemp): 수치 없음. 해석: Material*CoolTemp, InjTemp*CoolTemp 유의; InjTemp 85에서는 두 CoolTemp 절연값 거의 같고 InjTemp 100에서는 크게 다름; InjTemp 100 + CoolTemp 45가 최고.

### 4.4 Cube Plot (`using-fitted-models__how-to__cube-plot__before-you-start__example-with-a-factorial-design.txt`)
- 메뉴 `Stat > DOE > Factorial > Cube Plot`(ko: 입방체도). 필드: `Type of means to use in plots`(`Fitted means` 선택지 확인; 다른 선택지 이름은 문서에 없음 — Data means로 추정하지 말 것), `Response`, `Variables to Include in Plots`.
- 4요인 → 큐브 2개(왼쪽 CoolTemp 25, 오른쪽 CoolTemp 45), 각 꼭짓점에 적합 평균. 예제 수치: **CoolTemp 45, Formula2, InjTemp 100, InjPress 150 조합의 적합 평균 = 28.3558**(최대).

### 4.5 Contour Plot (`using-fitted-models__how-to__contour-plot__*`)
- 메뉴(회귀) `Stat > Regression > Regression > Contour Plot`; (혼합물) `Stat > DOE > Mixture > Contour/Surface Plots` > `Contour plot` > `Setup`. 메인: `Response`; `Select a pair of variables for a single plot`(X Axis, Y Axis). 혼합물: `Select a triplet of components for a single plot`(X-Axis, Y-Axis, Z-Axis), `Plot all level combinations`.
- **Contours** 하위 대화상자: Contour Levels — `Use defaults`(Minitab이 **4~7개** 결정) / `Number`(정수 **2~11**) / `Values`(데이터 단위로 **2~11개** 값). Data Display — `Area`(음영), `Contour lines`, `Symbols at design points`(요인·반응표면 설계일 때).
- **Settings** 하위 대화상자(모형 유형별):
  - 일반 모형: `Hold continuous variables at`(Variable | Setting; 기본 = 평균), `Hold categorical variables at`(기본 = 최소 숫자값 또는 알파벳 첫 수준).
  - **요인/스크리닝 설계**: `Hold factors at`(범주형 요인은 반드시 한 수준에 고정; 연속 요인 기본 = 평균), `Hold covariates at`(기본 = 평균, 반드시 고정).
  - 혼합물: `Hold components at`(Lower bound setting / Middle setting / Upper bound setting; Component | Name | Setting), `Hold process variables at`(Low / Middle / High setting; 공정변수는 **코드화 단위**), `Hold mixture amount at`. 텍스트 공정변수는 텍스트 수준으로만 고정.
- 등고선도는 연속 변수 2개만. 예제(ThermalEnergyTest, Heat Flux, X=East, Y=South): North는 **약 16.7**(평균)로 고정. 혼합물 예제: 회색 실선 = 설계 공간, Temperature 80 vs 90 두 그림.

### 4.6 Surface Plot (`using-fitted-models__how-to__surface-plot__before-you-start__example-w_7e44223b.txt`)
- 메뉴 `Stat > Regression > Regression > Surface Plot`. 메인: `Response`, `Select a pair of variables for a single plot`(X Axis, Y Axis). 예제 동일(East, South; North ≈ 16.7 고정). 하위 대화상자 내용은 문서에 없음.

### 4.7 Overlaid Contour Plot (`using-fitted-models__how-to__overlaid-contour-plot__*`)
- 메뉴 `Stat > Regression > Regression > Overlaid Contour Plot` / `Stat > DOE > Mixture > Overlaid Contour Plot`. 메인: `Responses`(Available → Selected, 2개 이상), `Variables`(X Axis, Y Axis); 혼합물은 `Select components or process variables as axes` → `3 Components`(X/Y/Z-Axis).
- **Contours**: 표 `Response | Low | High` — 반응마다 Low/High 등고선 값. 지침: 최소화 목표면 Low = 수확체감점(없으면 달성 불가능한 아주 작은 수), High = 최대 허용값; 목표값이면 규격한계 안쪽; 최대화면 High = 수확체감점, Low = 최소 허용값. **이항 로지스틱 모형이면 0~1.**
- **Settings**: `Hold continuous variables at`(예제: East = 31 입력).
- 결과: **흰 영역** = 모든 반응이 Low~High 안에 드는 조합. 회색 실선 = 혼합물 설계 공간.
- 예제 수치(ThermalEnergyTest): Insolation Low 725 / High 775, Heat Flux Low 175 / High 225, East 고정 31. 혼합물 예제(FondueRecipe_model): Flavor 80/100, Quantity 1.5/3, Burned 0/1.5, Temperature 80 고정.

---

## 5. Response Optimizer

### 5.1 대화상자 (`…response-optimizer__perform-the-analysis__0d1405be.txt`, `_ed409c24.txt`, `_38561a0d.txt`, 예제)
- 메뉴 `Stat > Regression > Regression > Response Optimizer`(ko: 반응 최적화 도구). 메인: 반응별 행에서 **Goal** 선택(문서에서 확인되는 값: `Target`, `Maximize`, `Minimize`; 그 외 선택지는 문서에 없음), Target 열 입력(예: Insolation Target 750).
- **Desirability** 하위 대화상자(`Response Optimizer > Desirability`): 표 `Response | Goal | Lower | Target | Upper | Weight | Importance`.
  - Response, Goal: 표시 전용.
  - **Lower**: Goal이 Target 또는 Maximize인 반응에 입력. **기본 = 데이터 최소값**(이항: 최소 비율).
  - **Target**: Target 목표면 메인에서 입력한 값; **Minimize면 기본 = 데이터 최소값, Maximize면 기본 = 데이터 최대값.**
  - **Upper**: Goal이 Minimize 또는 Target인 반응에 입력. **기본 = 데이터 최대값**.
  - **Weight**: **0.1 ~ 10**, 만족도 함수의 형상.
  - **Importance**: **0.1 ~ 10**, 반응 간 상대적 중요도.
  - Note: 반응 열 중 결측이 있으면 "models use different methods to standardize the shared variables" 오류 가능 → 결측 행 제외 필요.
- **Options**(`Response Optimizer > Options`; Predictive Analytics 모듈은 Constraints):
  - `Consider missing values during optimization.`(MARS/Random Forests/TreeNet 전용) 및 `Hold at missing`.
  - **Constraints** 표: `Variable | Constraint | Hold Value | Lower | Upper`. Constraint = `No constraints` / `Hold at value` / `Constrain to region`(GLM 공변량은 `Hold at mean` 추가; 결측 허용 시 `Hold at missing`). **요인 설계의 공변량은 반드시 고정값 — 기본 = 공변량 평균.**
  - **Starting values**: `Variable | Starting Value` — 연속 변수마다 관측 최소~최대 사이 값, 제약 만족해야 하며 Hold 값이 있는 변수에는 입력 불가.
  - `Confidence level for all intervals`(보통 95), `Type of confidence interval`: Two-sided / Lower bound / Upper bound(CI와 PI 모두).
- **Optimizer**(`Response Optimizer > Optimizer`; Random Forests/MARS/TreeNet 전용):
  - Missing Value Strategy: `Dynamic`(권장) / `Heuristic`.
  - Stopping Rules: `Time in minutes exceeds`(0 이상; 웹앱 최대 29), `Iterations exceed`, `Composite desirability is greater than or equal to`(기본 1; 낮추면 조기 종료, 해제하면 시간/반복 한계까지).
- 혼합물 전용 옵션: **문서에 없음**(이 페이지들에는 mixture 설정 없음).

### 5.2 공식 (`…methods-and-formulas__767d6302.txt`, `_3318f8d9.txt`, `average-importance.txt`)
**Individual desirabilities** — 수식 본문은 전부 [수식 이미지]. 텍스트에 남은 구조:
- ŷ = 반응 예측값(연속이면 실수, 범주형이면 선택 클래스 확률의 합).
- Maximize: 3구간 — `di = 0` | `di = [식]` | `di = 1`.
- Minimize: 3구간 — `di = 0` | `di = [식]` | `di = 1`.
- Target: 4구간 — `di = [식]` | `di = [식]` | `di = 0` | `di = 0`.
- Notation: ŷi 예측값, **Ti 목표값, Li 최저 허용값, Ui 최고 허용값, di 개별 만족도, D 종합 만족도, ri = i번째 반응 만족도 함수의 weight, wi = i번째 반응의 importance, W = [이미지]**.
(구간 조건·지수 형태는 문서 텍스트에 없음 — 이미지 파일명은 부록 A.)

**Composite desirability**: "The weighted geometric mean of the individual desirabilities." 공식 [이미지]; importance가 모두 같으면 [이미지]. Notation: di, wi, W = [이미지], n = 반응 수.

**Average importance**(Predictive Analytics 모듈 전용): 모형별 상대 변수 중요도의 평균 [이미지]. 선형/이항 로지스틱 회귀에서는 모형 내 모든 변수의 상대 중요도 = 1. 예: 4개 모형 중 3개에서 75, 56, 44, 4번째 모형에 없음 → (75 + 56 + 44 + 0)/4 = 43.75. Notation: Vi, M.

### 5.3 출력 (`…response-optimizer__interpret-the-results_66569390.txt`, 예제)
- **Parameters** 표: `Response | Goal | Lower | Target | Upper | Weight | Importance`.
- **Solution** 표: `Solution | <각 변수> | <반응>Fit … | CompositeDesirability` (예: `Solution | East | South | North | InsolationFit | Heat FluxFit | CompositeDesirability`).
- **Multiple Response Prediction**: 표 1 `Variable | Setting`(공변량 포함, 예: MeasTemp 21.4875); 표 2 `Response | Fit | SE Fit | 95% CI | 95% PI`.
- **Optimization plot**: 변수마다 열(빨간 세로선 = 현재 설정, 열 상단에 현재값(빨강)과 데이터의 high/low), 반응마다 행(파란 가로선 = 현재 반응값; 왼쪽에 예측값 y와 개별 만족도 d), 좌상단에 **종합 만족도 D**와 라벨 `Optimal`(변경하면 `New`, 새 최적이면 `Optimal`), 도구모음(`Predict` 단추 등). Stat 메뉴 모형은 더블클릭으로 상호작용 모드. 회색 영역 = 해당 반응 만족도 0.
- 종합 만족도: 0~1, 1 = 이상적, 0 = 하나 이상의 반응이 허용 한계 밖. **Minitab은 종합 만족도를 최대화.**

### 5.4 예제 수치
**ThermalEnergyTest** (Insolation Target 750, Heat Flux Target 200; 그 외 기본값):

Parameters
| Response | Goal | Lower | Target | Upper | Weight | Importance |
|---|---|---|---|---|---|---|
| Insolation | Target | 568.55 | 750 | 909.45 | 1 | 1 |
| Heat Flux | Target | 181.50 | 200 | 278.70 | 1 | 1 |

Solution
| Solution | East | South | North | InsolationFit | Heat FluxFit | CompositeDesirability |
|---|---|---|---|---|---|---|
| 1 | 32.2129 | 34.9758 | 18.3831 | 750 | 200 | 1 |

Multiple Response Prediction
| Variable | Setting |
|---|---|
| East | 32.2129 |
| South | 34.9758 |
| North | 18.3831 |

| Response | Fit | SE Fit | 95% CI | 95% PI |
|---|---|---|---|---|
| Insolation | 750.0 | 34.3 | (679.3, 820.7) | (621.8, 878.2) |
| Heat Flux | 200.00 | 5.14 | (189.41, 210.59) | (179.37, 220.63) |

(ko: 파라미터 / 반응·목적·하한·목표값·상한·가중치·중요도 / 솔루션 / 일사량적합치·열량적합치·종합 만족도 / 다중 반응 예측 / 변수·설정 / 반응·적합치·SE 적합치.)

**Insulation 3반응 예제**(all-statistics 페이지; 목표: Strength Maximize(38.1821 excellent, < 19.2189 unacceptable), Density Minimize(0.4351 excellent, > 1.60314 unacceptable), Insulation Maximize(27.7156 excellent, < 13.2905 unacceptable), importance 동일):
- 종합 만족도 **0.7750**; 설정 Material = Formula2, InjPress = 98.4848, InjTemp = 100.0, CoolTemp = 45.0; 공변량 MeasTemp 21.49 고정; Insulation 예측 25.6075, 개별 만족도 0.85386.

| Variable | Setting |
|---|---|
| Material | Formula2 |
| InjPress | 98.4848 |
| InjTemp | 100 |
| CoolTemp | 45 |
| MeasTemp | 21.4875 |

| Response | Fit | SE Fit | 95% CI | 95% PI |
|---|---|---|---|---|
| Strength | 32.34 | 1.04 | (29.45, 35.22) | (27.25, 37.43) |
| Density | 0.6826 | 0.0597 | (0.5167, 0.8484) | (0.3899, 0.9753) |
| Insulation | 25.608 | 0.268 | (24.863, 26.352) | (24.294, 26.921) |

---

## 6. Predict

### 6.1 대화상자 (`using-fitted-models__how-to__predict__perform-the-analysis__enter-your-data.txt`)
- 메뉴: 모형을 적합한 메뉴에서 `Predict`(예: `Stat > Regression > Regression > Predict`; ko: 예측).
- `Response`: **최신 저장 모형이 있는 반응만** 목록에 나옴(없으면 재적합).
- `Include covariates in prediction`(Fit General Linear Model·Analyze Factorial Design 모형 전용): 체크 안 하면 **공변량에 대해 평균화한 예측**.
- 두 번째 드롭다운: `Enter individual values`(표에 변수마다 값 1개 이상, 열마다 같은 개수; 범주형은 드롭다운, 연속은 숫자/날짜) / `Enter columns of values`(변수마다 워크시트 열, 행 수 동일, 범주형은 적합에 쓴 값과 동일; 결과는 열에 저장되고 기본으로 표시 안 함 → Results에서 선택).
- 예시 워크시트: `Salary | Gender | Years | Quality | Gender_New | Years_New | Quality_New` (50 M 4 95 M 6 70 / 76 F 13 67 M 10 84 / 68 F 7 78 F 15 60 / 80 M 11 88 F 12 57).

### 6.2 출력 (`…predict__interpret-the-results__all-statistics.txt`, 예제)
- `Regression Equation`(한 행 식), `Settings`(`Variable | Setting`), `Prediction`(`Fit | SE Fit | 95% CI | 95% PI`). 설정이 데이터 범위에 비해 비정상이면 예측 아래 **경고 표시**. 적합치 종류는 반응 유형에 따라 평균/확률/표준편차.
- PI는 항상 CI보다 넓음.

### 6.3 공식 (`…predict__methods-and-formulas__methods-and-formulas.txt`)
- Confidence interval [수식 이미지] — Notation: (t 분위수 이미지), ŷ, α, n, p, S²(b), s², X, X0(p×1), X′0.
- Fit [이미지] — ŷ, xk, bk.
- SE Fit: 1 예측변수 [이미지], 다변수 [이미지], 가중 [이미지]; 테스트/K-fold에도 동일(훈련 데이터의 s², X, W).
- Regression equation 원문: `y = β0 + β1x1 + … + βkxk + ε`; 적합식 [이미지]; 단순회귀 `y=ß0+ ß1x1+ε`. 범주형 변수: 수준별 개별식 또는 지시변수 단일식 — 예: `Blue: C1 = 0.184 + 0.1964*C2`, `Red: C1 = 0.011 + 0.1964*C2`, 단일식 `C1 = 0.184 + 0.1964*C2 + 0.0*C3_Blue - 0.173*C3_Red`.
- Prediction interval [이미지] — Notation: s(Pred) [이미지], ŷ, α, n, p, s², X, X0, X′0.

### 6.4 예제 (ThermalEnergyTest, Heat Flux; East 35, South 34, North 16)
| Heat Flux | = | 389.2 + 2.12 East + 5.318 South - 24.13 North |
|---|---|---|

| Variable | Setting |
|---|---|
| East | 35 |
| South | 34 |
| North | 16 |

| Fit | SE Fit | 95% CI | 95% PI |
|---|---|---|---|
| 258.242 | 2.35414 | (253.393, 263.090) | (239.882, 276.601) |

(ko: 회귀 방정식 / 설정 / 변수·설정 / 예측 / 적합치·SE 적합치·95% CI·95% PI.)

---

## 7. 예제 출력표 — 테스트 정답용 (숫자 원문 그대로)

### 7.1 Analyze Factorial Design — InsulationProperties.MWX, Response = Strength, Terms 차수 2, Covariates = MeasTemp, Graphs = Four in one (`…before-you-start__example.txt`)

Coded Coefficients
| Term | Effect | Coef | SE Coef | T-Value | P-Value | VIF |
|---|---|---|---|---|---|---|
| Constant | | 56.0 | 21.0 | 2.66 | 0.056 | |
| MeasTemp | | -1.229 | 0.979 | -1.25 | 0.278 | 5.87 |
| Material | 5.316 | 2.658 | 0.678 | 3.92 | 0.017 | 3.23 |
| InjPress | 5.645 | 2.822 | 0.401 | 7.04 | 0.002 | 1.13 |
| InjTemp | 4.355 | 2.177 | 0.378 | 5.76 | 0.005 | 1.00 |
| CoolTemp | -3.457 | -1.729 | 0.420 | -4.12 | 0.015 | 1.24 |
| Material*InjPress | -0.723 | -0.361 | 0.415 | -0.87 | 0.433 | 1.21 |
| Material*InjTemp | -1.025 | -0.512 | 0.443 | -1.16 | 0.312 | 1.38 |
| Material*CoolTemp | -0.208 | -0.104 | 0.510 | -0.20 | 0.848 | 1.82 |
| InjPress*InjTemp | -0.837 | -0.419 | 0.510 | -0.82 | 0.458 | 1.82 |
| InjPress*CoolTemp | -0.055 | -0.027 | 0.382 | -0.07 | 0.947 | 1.03 |
| InjTemp*CoolTemp | 1.933 | 0.966 | 0.381 | 2.54 | 0.064 | 1.02 |

Model Summary
| S | R-sq | R-sq(adj) | R-sq(pred) |
|---|---|---|---|
| 1.51005 | 98.02% | 92.57% | 70.86% |

Analysis of Variance
| Source | DF | Adj SS | Adj MS | F-Value | P-Value |
|---|---|---|---|---|---|
| Model | 11 | 451.357 | 41.032 | 17.99 | 0.007 |
| Covariates | 1 | 3.591 | 3.591 | 1.58 | 0.278 |
| MeasTemp | 1 | 3.591 | 3.591 | 1.58 | 0.278 |
| Linear | 4 | 304.587 | 76.147 | 33.39 | 0.002 |
| Material | 1 | 35.053 | 35.053 | 15.37 | 0.017 |
| InjPress | 1 | 113.068 | 113.068 | 49.59 | 0.002 |
| InjTemp | 1 | 75.533 | 75.533 | 33.12 | 0.005 |
| CoolTemp | 1 | 38.666 | 38.666 | 16.96 | 0.015 |
| 2-Way Interactions | 6 | 20.309 | 3.385 | 1.48 | 0.366 |
| Material*InjPress | 1 | 1.732 | 1.732 | 0.76 | 0.433 |
| Material*InjTemp | 1 | 3.045 | 3.045 | 1.34 | 0.312 |
| Material*CoolTemp | 1 | 0.095 | 0.095 | 0.04 | 0.848 |
| InjPress*InjTemp | 1 | 1.538 | 1.538 | 0.67 | 0.458 |
| InjPress*CoolTemp | 1 | 0.012 | 0.012 | 0.01 | 0.947 |
| InjTemp*CoolTemp | 1 | 14.694 | 14.694 | 6.44 | 0.064 |
| Error | 4 | 9.121 | 2.280 | | |
| Total | 15 | 460.478 | | | |

Regression Equation in Uncoded Units
```
Strength = 52.7 - 1.229 MeasTemp + 10.43 Material + 0.216 InjPress + 0.007 InjTemp - 1.357 CoolTemp - 0.0096 Material*InjPress - 0.0683 Material*InjTemp - 0.0104 Material*CoolTemp - 0.00149 InjPress*InjTemp - 0.00007 InjPress*CoolTemp + 0.01288 InjTemp*CoolTemp
```

Alias Structure
| Factor | Name |
|---|---|
| A | Material |
| B | InjPress |
| C | InjTemp |
| D | CoolTemp |

Aliases
```
I - 5.42 ABC + 28.92 ABD - 9.04 ACD - 10.85 BCD + 45.19 ABCD
A + 0.15 ABC - 0.77 ABD + 0.24 ACD + 0.29 BCD - 1.21 ABCD
B - 0.03 ABC + 0.19 ABD - 0.06 ACD - 0.07 BCD + 0.29 ABCD
C - 0.01 ABC + 0.03 ABD - 0.01 ACD - 0.01 BCD + 0.05 ABCD
D - 0.05 ABC + 0.25 ABD - 0.08 ACD - 0.09 BCD + 0.39 ABCD
AB + 0.04 ABC - 0.24 ABD + 0.07 ACD + 0.09 BCD - 0.37 ABCD
AC + 0.06 ABC - 0.32 ABD + 0.10 ACD + 0.12 BCD - 0.50 ABCD
AD - 0.09 ABC + 0.47 ABD - 0.15 ACD - 0.18 BCD + 0.74 ABCD
BC + 0.09 ABC - 0.47 ABD + 0.15 ACD + 0.18 BCD - 0.74 ABCD
BD + 0.02 ABC - 0.08 ABD + 0.03 ACD + 0.03 BCD - 0.13 ABCD
CD - 0.01 ABC + 0.07 ABD - 0.02 ACD - 0.03 BCD + 0.11 ABCD
```
해석 문구: Pareto에서 가장 큰 효과 = injection pressure (B), 가장 작은 = BD; MeasTemp VIF 5.87; R² 98.02%.

### 7.2 같은 데이터, 공변량 없는 모형 2개 (ANOVA 해석 페이지 `…interpret-the-result_e8cb6bbc.txt`)

(a) 주효과 + 모든 2-way (10항)
| Source | DF | Adj SS | Adj MS | F-Value | P-Value |
|---|---|---|---|---|---|
| Model | 10 | 447.766 | 44.777 | 17.61 | 0.003 |
| Linear | 4 | 428.937 | 107.234 | 42.18 | 0.000 |
| Material | 1 | 181.151 | 181.151 | 71.25 | 0.000 |
| InjPress | 1 | 112.648 | 112.648 | 44.31 | 0.001 |
| InjTemp | 1 | 73.725 | 73.725 | 29.00 | 0.003 |
| CoolTemp | 1 | 61.412 | 61.412 | 24.15 | 0.004 |
| 2-Way Interactions | 6 | 18.828 | 3.138 | 1.23 | 0.418 |
| Material*InjPress | 1 | 0.342 | 0.342 | 0.13 | 0.729 |
| Material*InjTemp | 1 | 0.778 | 0.778 | 0.31 | 0.604 |
| Material*CoolTemp | 1 | 4.565 | 4.565 | 1.80 | 0.238 |
| InjPress*InjTemp | 1 | 0.002 | 0.002 | 0.00 | 0.978 |
| InjPress*CoolTemp | 1 | 0.039 | 0.039 | 0.02 | 0.906 |
| InjTemp*CoolTemp | 1 | 13.101 | 13.101 | 5.15 | 0.072 |
| Error | 5 | 12.712 | 2.542 | | |
| Total | 15 | 460.478 | | | |

(b) p-값이 가장 큰 2-way부터 하나씩 제거한 최종 모형(InjTemp*CoolTemp만 남음)
| Source | DF | Adj SS | Adj MS | F-Value | P-Value |
|---|---|---|---|---|---|
| Model | 5 | 442.04 | 88.408 | 47.95 | 0.000 |
| Linear | 4 | 428.94 | 107.234 | 58.16 | 0.000 |
| Material | 1 | 181.15 | 181.151 | 98.24 | 0.000 |
| InjPress | 1 | 112.65 | 112.648 | 61.09 | 0.000 |
| InjTemp | 1 | 73.73 | 73.725 | 39.98 | 0.000 |
| CoolTemp | 1 | 61.41 | 61.412 | 33.31 | 0.000 |
| 2-Way Interactions | 1 | 13.10 | 13.101 | 7.11 | 0.024 |
| InjTemp*CoolTemp | 1 | 13.10 | 13.101 | 7.11 | 0.024 |
| Error | 10 | 18.44 | 1.844 | | |
| Total | 15 | 460.48 | | | |

(이 (b) 모형의 Means 표가 §2.8. Adj SS 자릿수가 (a)와 다르게 표시됨에 주의 — 표시 자릿수는 열 단위로 유효숫자 맞춤.)

### 7.3 Analyze Definitive Screening Design — ultrasonic_cleaner.MWX, Response = Power, Terms = Linear (`doe__how-to__screening__analyze-screening-design__before-you-start__example.txt`)

Coded Coefficients
| Term | Coef | SE Coef | T-Value | P-Value | VIF |
|---|---|---|---|---|---|
| Constant | 657.8 | 12.4 | 53.22 | 0.000 | |
| Train | 52.4 | 13.6 | 3.85 | 0.004 | 1.00 |
| Degas | 0.9 | 13.6 | 0.07 | 0.949 | 1.00 |
| Burst | 8.6 | 13.6 | 0.63 | 0.542 | 1.00 |
| Quiet | -39.6 | 13.6 | -2.91 | 0.017 | 1.00 |
| Center | -2.4 | 13.6 | -0.17 | 0.866 | 1.00 |
| Bandwidth | 3.5 | 13.6 | 0.26 | 0.803 | 1.00 |
| Sweep | 2.8 | 13.6 | 0.21 | 0.839 | 1.00 |

Model Summary
| S | R-sq | R-sq(adj) | R-sq(pred) |
|---|---|---|---|
| 50.9634 | 72.56% | 51.21% | 4.50% |

Analysis of Variance
| Source | DF | Adj SS | Adj MS | F-Value | P-Value |
|---|---|---|---|---|---|
| Model | 7 | 61803.7 | 8829.1 | 3.40 | 0.046 |
| Linear | 7 | 61803.7 | 8829.1 | 3.40 | 0.046 |
| Train | 1 | 38451.1 | 38451.1 | 14.80 | 0.004 |
| Degas | 1 | 11.2 | 11.2 | 0.00 | 0.949 |
| Burst | 1 | 1040.6 | 1040.6 | 0.40 | 0.542 |
| Quiet | 1 | 21938.4 | 21938.4 | 8.45 | 0.017 |
| Center | 1 | 77.8 | 77.8 | 0.03 | 0.866 |
| Bandwidth | 1 | 171.5 | 171.5 | 0.07 | 0.803 |
| Sweep | 1 | 113.1 | 113.1 | 0.04 | 0.839 |
| Error | 9 | 23375.4 | 2597.3 | | |
| Total | 16 | 85179.2 | | | |

Regression Equation in Uncoded Units
```
Power = 626.5 + 116.5 Train + 2.0 Degas + 1.92 Burst - 8.80 Quiet - 0.47 Center + 0.70 Bandwidth + 0.57 Sweep
```

Alias Structure (up to order 2)
| Factor | Name |
|---|---|
| A | Train |
| B | Degas |
| C | Burst |
| D | Quiet |
| E | Center |
| F | Bandwidth |
| G | Sweep |

Aliases
```
I + 0.82 AA + 0.82 BB + 0.82 CC + 0.82 DD + 0.82 EE + 0.82 FF + 0.82 GG
A
B
C
D
E
F
G
```
해석: Pareto에서 Train (A), Quiet (D)가 가장 큼; 잔차 대 적합치에 U자형 → 제곱항/교호작용 누락 가능. (DF Total 16 → 17 런.)

### 7.4 Analyze Variability — InsulationStrength.MWX, Response (standard deviations) = Std, 차수 2, Pareto, Three in one (`doe__how-to__factorial__analyze-variability__before-you-start__example.txt`)

Method
| Estimation | Least squares |
|---|---|

Coded Coefficients for Ln(Std)
| Term | Effect | Ratio Effect | Coef | SE Coef | T-Value | P-Value | VIF |
|---|---|---|---|---|---|---|---|
| Constant | | | 0.3424 | 0.0481 | 7.12 | 0.001 | |
| Material | -0.9598 | 0.3830 | -0.4799 | 0.0481 | -9.99 | 0.000 | 1.00 |
| InjPress | -0.1845 | 0.8315 | -0.0922 | 0.0481 | -1.92 | 0.113 | 1.00 |
| InjTemp | 0.0555 | 1.0571 | 0.0278 | 0.0481 | 0.58 | 0.589 | 1.00 |
| CoolTemp | -0.1259 | 0.8817 | -0.0629 | 0.0481 | -1.31 | 0.247 | 1.00 |
| Material*InjPress | -0.9918 | 0.3709 | -0.4959 | 0.0481 | -10.32 | 0.000 | 1.00 |
| Material*InjTemp | 0.1875 | 1.2062 | 0.0937 | 0.0481 | 1.95 | 0.109 | 1.00 |
| Material*CoolTemp | 0.0056 | 1.0056 | 0.0028 | 0.0481 | 0.06 | 0.956 | 1.00 |
| InjPress*InjTemp | -0.0792 | 0.9239 | -0.0396 | 0.0481 | -0.82 | 0.448 | 1.00 |
| InjPress*CoolTemp | -0.0900 | 0.9139 | -0.0450 | 0.0481 | -0.94 | 0.392 | 1.00 |
| InjTemp*CoolTemp | 0.0066 | 1.0066 | 0.0033 | 0.0481 | 0.07 | 0.948 | 1.00 |

Model Summary for Ln(Std)
| S | R-sq | R-sq(adj) | R-sq(pred) |
|---|---|---|---|
| 0.549040 | 97.75% | 93.25% | 76.97% |

Analysis of Variance for Ln(Std)
| Source | DF | Adj SS | Adj MS | F-Value | P-Value |
|---|---|---|---|---|---|
| Model | 10 | 65.4970 | 6.5497 | 21.73 | 0.002 |
| Linear | 4 | 31.7838 | 7.9459 | 26.36 | 0.001 |
| Material | 1 | 30.0559 | 30.0559 | 99.71 | 0.000 |
| InjPress | 1 | 1.1104 | 1.1104 | 3.68 | 0.113 |
| InjTemp | 1 | 0.1005 | 0.1005 | 0.33 | 0.589 |
| CoolTemp | 1 | 0.5170 | 0.5170 | 1.71 | 0.247 |
| 2-Way Interactions | 6 | 33.7132 | 5.6189 | 18.64 | 0.003 |
| Material*InjPress | 1 | 32.0953 | 32.0953 | 106.47 | 0.000 |
| Material*InjTemp | 1 | 1.1466 | 1.1466 | 3.80 | 0.109 |
| Material*CoolTemp | 1 | 0.0010 | 0.0010 | 0.00 | 0.956 |
| InjPress*InjTemp | 1 | 0.2046 | 0.2046 | 0.68 | 0.448 |
| InjPress*CoolTemp | 1 | 0.2642 | 0.2642 | 0.88 | 0.392 |
| InjTemp*CoolTemp | 1 | 0.0014 | 0.0014 | 0.00 | 0.948 |
| Error | 5 | 1.5072 | 0.3014 | | |
| Total | 15 | 67.0043 | | | |

Regression Equation in Uncoded Units
```
Ln(Std) = -1.30 - 0.158 Material + 0.0148 InjPress + 0.0180 InjTemp + 0.0031 CoolTemp - 0.01322 Material*InjPress + 0.01250 Material*InjTemp + 0.00028 Material*CoolTemp - 0.000141 InjPress*InjTemp - 0.000120 InjPress*CoolTemp + 0.000044 InjTemp*CoolTemp
```
Alias Structure: Factor A Material, B InjPress, C InjTemp, D CoolTemp; Aliases = `I, A, B, C, D, AB, AC, AD, BC, BD, CD`(완전요인, 별칭 없음). 해석: 가장 큰 효과 Material*InjPress (AB), 가장 작은 Material*CoolTemp (AD); R² 97.75%. (Ratio Effect = exp(Effect)로 보이나 **문서에 정의 없음**.)

### 7.5 Response Optimizer / Predict / Cube / Contour / Overlaid 수치 → §5.4, §6.4, §4.4~4.7 참조.

### 7.6 Alias structure 해석 페이지 예제 (`…interpret-the-result_d9296586.txt`; 3요인 Surgeon/VAS/Ibuprofen)
- 분수 설계: `I + ABC`, `A + BC`, `B + AC`, `C + AB`.
- 블록 설계: `I`, `Block 1 - ABC`, `Block 2 + ABC`, `Block 3 - ABC`, `A`, `B`, `C`.
- 공변량(age) 포함 부분 별칭: `I + 0.91 AB - 0.23 AC - 1.37 BC + 0.27 ABC`, `A + 0.61 AB - 0.15 AC - 0.41 BC - 0.15 ABC`, `B + 0.04 AB + 0.49 AC - 0.07 BC - 0.01 ABC`, `C + AB`.

### 7.7 Effects plot 해석 페이지 예시 수치 (`…interpret-the-result_e6bb8b6d.txt`)
- Pareto 기준선 2.31(α = 0.05)에서 C, B, BC 유의(데이터셋 미제시). Normal plot 예: Process (A) 양의 효과, Pressure (B)·Speed (C) 음의 효과.

### 7.8 Model summary 해석 페이지 보조표 (`…interpret-the-result_3f8a664d.txt`)
| Model | % Potato | Cooling rate | Cooking temp | R2 | Adjusted R2 |
|---|---|---|---|---|---|
| 1 | X | | | 52% | 51% |
| 2 | X | X | | 63% | 62% |
| 3 | X | X | X | 65% | 62% |

---

## 8. 구현 시 주의할 점

1. **계수는 항상 코드화 단위(−1/+1), Effect = 2 × Coef.** Effect는 요인·요인 교호작용에만 있고 Constant·공변량·블록·CenterPt는 비움. DSD(Analyze Screening Design) 출력엔 Effect 열 자체가 없다.
2. **설계행렬 열 순서 Constant → Covariates → Blocks → Factors → Interactions**가 Coefficients 행 순서·ANOVA 그룹 순서·"별칭 충돌 시 뒤에 오는 항 제거" 규칙의 기준이다. 블록은 (−1,0,+1), CenterPt는 (0,1; 요인점=1, 중앙점=0) 코딩.
3. **ANOVA p-값은 Adj SS 기준**(Seq SS는 표시 옵션). Model·그룹 행(Covariates, Linear, 2-Way Interactions…)은 구성 항 Seq SS의 합. Curvature 행은 중앙점 항 포함 여부에 따라 Model/Error 소속이 바뀌고 DF는 항상 1. Lack-of-Fit/Pure Error 행은 "적합 가능한 미포함 항 존재 + 반복 존재" 두 조건이 모두 맞을 때만 생성(순수 오차 DF = m(r−1)+(c−1)).
4. **회귀식 단위**: 계층 모형이면 Uncoded(블록 평균화되어 블록 계수 없음, 범주형은 ±1), 비계층이면 Coded. Hierarchy 프롬프트(권장 = 항 추가)를 재현해야 한다.
5. **포화 모형(오차 DF 0)** 분기: 효과도는 비표준화 효과 + Lenth PSE(1.5·median → 2.5S 절단 → 1.5·median), ME = t(1−α/2, df = 효과 수/3)·PSE, 그래프 제목에서 "Standardized" 제거; 일반 완전요인이면 Pareto 생략; Stepwise/Backward는 Adj SS 최소 항 ¼(최대 9) 선제 제거 후 시작.
6. **효과도 α**는 기본 1 − 신뢰수준이지만 Stepwise 방법을 쓰면 Alpha to remove(Backward/Stepwise) 또는 Alpha to enter(Forward)로 바뀐다. Pareto 기준선 = t(1−α/2, 오차 DF).
7. **이상 관측치 플래그**: R = |Std Resid| > 2, X = Hi > min(3p/n, 0.99), p는 상수 포함 계수 수. R-sq(adj)·R-sq(pred)가 음수면 0으로 표시.
8. **그래프 가용성 제약**: 중앙점 항이 모형에 남아 있으면 Contour/Surface/Overlaid Contour 비활성, Optimizer는 수준 사이 보간 안 함. Contour 등고선 기본 4~7개, 사용자 지정 2~11개. Factorial/Cube Plot은 적합 평균(혼합물은 데이터 평균), 연속 2차 변수의 interaction plot은 최소·최대값 두 선, 주효과도에 전체 평균 기준선.
9. **Response Optimizer 기본값**: Lower = 데이터 최소, Upper = 데이터 최대, Target(Min/Max 목표) = 데이터 최소/최대, Weight·Importance 0.1~10, 요인 설계의 공변량은 평균에 고정(Multiple Response Prediction의 Setting 표에 공변량 행 포함). 종합 만족도 = 개별 만족도의 **가중 기하평균**(개별 만족도 구간식은 이미지라 텍스트 근거 없음 — 부록 A 이미지 확인 필요).
10. **Predict**: 저장 모형이 최신인 반응만 선택 가능, `Include covariates in prediction` 미선택 시 공변량 평균화, 설정이 비정상이면 경고. 출력은 Regression Equation / Settings / Prediction(Fit, SE Fit, 95% CI, 95% PI) 세 표.
11. **Box-Cox**: 모든 반응 > 0 필수, 최적 λ 탐색 −2~2, 기본은 0.5 단위 반올림, λ < 0이면 −1 곱해 순서 유지; 출력 제목에 "for Ln(Std)" 같은 변환 반응명 부착, Method 표에 Rounded λ / Estimated λ / 95% CI for λ.
12. **분할구 설계 제약**: 중앙점·가중치·Stepwise 불가, AICc/BIC 미표시, Model Summary에 S(WP)/R-sq(WP)/R-sq(SP) 추가, hard-to-change 요인 F의 분모 = WP Error MS.
13. **수식 복원 작업 필요**: S, R-sq 계열, PRESS, AICc/BIC/Cp, 표준화·삭제 잔차, SE Fit, CI/PI, Cook's D, DFITS, 만족도 함수는 모두 PNG(부록 A)라 별도 소스로 검증해야 한다. 이 요약은 이를 추정해 채우지 않았다.

---

## 부록 A. 수식 이미지 파일명 (HTML `<img src="/en-us/minitab/png/…">`)

| 페이지 | 이미지 파일(접두 `/en-us/minitab/png/`) |
|---|---|
| model-information | `Coefficients_Factorial_Design_mf.dita_IDD77FB8372E5447C59711F1B57FCC4D53_methodformula_0.png` ~ `_7.png`(계수·SE 공식 및 표기 기호), `box_cox_transformation_SS_FRM_mf.dita_dctm_Chron09000457802afcc4_0.png`, `_1.png`, `Weighted_regression_GLM_Balanced_Anova_FRM_mf.dita_IDC22529CF4F9D44F498BD872FA5A95834_methodformula_0.png` ~ `_2.png` |
| analysis-of-variance | `Sum_of_squares_Factorial_Design_mf.dita_IDDE6936BED1A9466280AA25DD1D4D86B9_methodformula_0.png` ~ `_17.png`, `Degrees_of_freedom_Factorial_Design_mf.dita_IDF59AD6A240744696B97B54538EB345D9_methodformula_0.png` ~ `_8.png`, `ms_term_afd_mf.dita_dctm_Chron0900045780575bf3_0.png`, `f_ffac_mixr_mf.dita_ID23DD0015FD794AB3BB581697C1E533B7_methodformula_0.png`, `pure_error_lack_of_fit_fixed_batch_SS_regr_glm_mf.dita_dctm_Chron0900045780316fa6_0.png` ~ `_4.png` |
| goodness-of-fit | `s_SR_MR_2W_glm_mf.dita_ID89DAF14EEC854D78A71CA2C5CE318456_mtbreference_0.png`(S), `r2_SR_MR_2W_SS_glm_mf.dita_ID858FF15D28FC4FDFB1B577270B2E591E_mtbreference_0.png` ~ `_2.png`(R-sq), `r2adj_SR_MR_SS_glm_mf.dita_IDBD4FD33B65584671A6292FD45889FD95_methodformula_0.png` ~ `_3.png`, `R2predicted_SR_MR_1W_2W_glm_mf.dita_IDDC54176D95F64B11AF5C6C8DF106DBEA_mtbreference_0.png`, `_1.png`, `press_FRM_fixed_batch_SS_mf.dita_dctm_Chron0900045780316fa6_0.png`, `r_sq_wp_afd_mf.dita_dctm_Chron0900045780575bf4_0.png`, `r_sq_sp_afd_mf.dita_dctm_Chron0900045780575bf5_0.png`, `log_likelihood_linear_models_mf.dita_dctm_Chron09000457806e9474_0.png`, `_1.png`, `aicc_linear_models_mf.dita_dctm_Chron09000457806e7db2_0.png`, `_1.png`, `bic_linear_models_mf.dita_dctm_Chron09000457806e7db7_0.png`, `mallows_cp_breg_step_glm_mf.dita_dctm_Chron090004578001ba18_0.png` |
| fits-and-residuals | `Fitted_value_SR_MR_PR_glm_FRM_mf.dita_ID313F2B10560647B4B5C92A72C46F9ABB_mtbreference_0.png`, `_1.png`, `residuals_mf.dita_dctm_Chron090004578043b533_0.png`, `_1.png`, `standardized_resid_SR_MR_2W_glm_FRM_mf.dita_ID1B1C3D89FED24607B492FF16545CB3AA_mtbreference_0.png`, `Deleted_studentized_residual_GLM_BA_FRM_mf.dita_ID54EA76F4FBA04089909F13391657C629_methodformula_0.png` ~ `_2.png`, `whole_plot_residuals_afd_mf.dita_dctm_Chron0900045780575bf6_0.png` ~ `_2.png`, `SEFit_PR_glm_FRM_mf.dita_ID1F60FD567A624B259642E7AB6AD1FBDA_methodformula_0.png` ~ `_3.png`, `SE_Fit_split_plot_design.dita_dctm_Chron0900045780575bf7_0.png` ~ `_6.png`, `CI_PR_mf.dita_IDD7D7571B5B894635AD4DD2603DA11FD1_mtbreference_0.png` ~ `_3.png`, `prediction_int_PR_mf.dita_ID3918093AB4214007BF1241FA43416042_mtbreference_0.png` ~ `_2.png` |
| diagnostic-measures | `Leverages_GLM_Balanced_Anova_mf.dita_ID6EA75B46E066414B8052B289F92210C3_methodformula_0.png`, `_1.png`, `cooks_d_frm_glm_mf_mss.dita_ID3DB1530FA8574E7BB761C82D93DE2D70_mtbreference_0.png`, `_1.png`, `DFITS_greg_regr_mf.dita_ID2196CD4AC2CE4BDAA56509CD072CFB4E_mtbreference_0.png` ~ `_3.png` |
| effects-plots | (이미지 없음 — 전부 텍스트) |
| stepwise | `stepwise_method_stepwise_afd_mss.dita_dctm_Chron09000457808ed90d_0.png` ~ `_2.png` |
| Predict methods | `CI_PR_mf…_0~3.png`, `Fitted_value_SR_MR_PR_glm_FRM_mf…_0,1.png`, `SEFit_PR_glm_FRM_mf…_0~3.png`, `Regression_model_SR_MR_PR_mf.dita_IDA310F1B6C3F142F4BE4D3AC28B1D3DF4_methodformula_0.png` ~ `_2.png`, `prediction_int_PR_mf…_0~2.png` |
| Response Optimizer individual desirabilities | `mf_individual_desirabilities_response_optimizer.dita_dctm_Chron090004578069aebb_0.png` ~ `_18.png` |
| composite desirability | `mf_composite_desirability_response_optimizer.dita_dctm_Chron090004578069aebc_0.png` ~ `_2.png` |
| average importance | `mf_average_importance_response_optimizer.dita_mf_average_importance_response_optimizer_0.png` |
| how-is-a-coefficient… | `calculate_coefficients_for_main_effects.dita_dctm_Chron09000457801c6590_0.png` |
| how-error-is-partitioned | (이미지 없음) |
