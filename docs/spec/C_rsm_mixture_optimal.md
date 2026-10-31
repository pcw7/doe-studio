# C. 반응 표면(RSM) · 혼합물(Mixture) · 최적 설계(Optimal) · Taguchi — Minitab 문서 구조화 요약

- 소스 폴더: `...\scratchpad\minitab_pages\en-us\` (한국어판은 `...\minitab_pages\ko-kr\` 에 일부 존재)
- 작성 원칙: 문서에 있는 내용만 기록. 표의 숫자는 원문 그대로. UI 라벨·열 이름·설계 이름은 영어 원문 유지. 문서에 없는 항목은 **"문서에 없음"** 으로 명시.
- 각 절 끝 또는 항목 옆 괄호 안에 근거 파일명을 표기.

## 0. 범위·소스 상태·전제

### 0.1 읽은 파일 (en-us, 88개 중 87개 존재)
- Response surface how-to: `doe__how-to__response-surface__create-response-surface-design__create-_{096e9000,2b401544,34e2ebec,3c72e2af,814483e0,897f0ad4,b108c6d9,bb93f5e3,eb6a23ae,f0ea3592}.txt`, `...__select-_6982412c.txt`, `...__select-a-response-surface-design.txt`, `doe__how-to__response-surface__analyze-response-surface-design__{before-you-start__example, interp_2f7cc302, interp_ab6d6d41, interp_ce5a0525, method_18bb7972, method_484a873b, method_91d6a8aa, method_a6627ad5, method_a9d3dd88, method_e97f0d5f, perfor_40ad6d39, perfor_ad8d554f, perfor_b23b80b5, perfor_d6a65ef0}.txt`, `doe__how-to__response-surface__define-custom-response-surface-design___ea9fc237.txt`, `doe__how-to__response-surface__display-and-modify-design.txt`, `doe__how-to__response-surface__select-optimal-design.txt`
- Response surface supporting topics: `doe__supporting-topics__response-surface-designs__{blocks-in-a-box-behnken-design, blocks-in-a-central-composite-design, response-surface-cen_4229705b, response-surface-central-composite-and-box-behnken-designs(동일 내용 중복), summary-of-box-behnken-designs, summary-of-central-composite-designs, what-is-alpha-in-a-c_92088d54}.txt`
- Mixtures how-to: `doe__how-to__mixtures__create-mixture-design__*` (예제 3 + overview + display-available-designs + speci_* 7 + specify-the-components + all-statistics), `doe__how-to__mixtures__analyze-mixture-design__*` (example, interpret 2, methods 4, perform 3), `doe__how-to__mixtures__{contour-surface-plots, display-and-modify-design, factorial-plots, overlaid-contour-plot, response-optimizer, select-optimal-design}.txt`, `doe__how-to__mixtures__response-trace-plot__before-you-start__example.txt`, `doe__how-to__mixtures__simplex-design-plot__before-you-start__example.txt`
- Mixture supporting topics: `doe__supporting-topics__mixture-designs__{choose-a-mixture-design, how-minitab-augments-designs, models-terms-and-blending, perform-a-mixtures-experiment, scales-for-representing-the-data, what-is-a-mixture-design, what-is-a-pseudo-component, what-is-a-simplex-design, what-is-an-extreme-vertices-design, what-is-the-degree-of-a-lattice}.txt`
- Optimal: `doe__how-to__factorial__select-optimal-design__before-you-start__examp_{61fbc6b2,a837a12e,acb2f2eb}.txt`, `doe__how-to__factorial__select-optimal-design__methods-and-formulas__methods-and-formulas.txt`, `doe__supporting-topics__basics__optimality-criteria.txt`, `doe__supporting-topics__basics__what-points-can-i-use-in-a-designed-experiment.txt`
- Taguchi: `doe__how-to__taguchi__analyze-taguchi-design__before-you-start__exampl_076df8c3.txt`, `doe__how-to__taguchi__create-taguchi-design__before-you-start__example_2dc12631.txt`, `doe__how-to__taguchi__create-taguchi-design__create-the-design__display-available-designs.txt`, `doe__supporting-topics__taguchi-designs__catalogue-of-taguchi-designs.txt`

### 0.2 소스 상태에 대한 중요 메모
1. **`doe__supporting-topics__basics__what-is-an-optimal-design.txt` 는 en-us 폴더에 존재하지 않음** (`ls`/`cat` 모두 No such file). 해당 내용은 "문서에 없음"으로 처리.
2. **Methods-and-formulas 페이지의 수식은 거의 전부 이미지**(`<img src=".../png/...mtbreference_N.png">`, alt 텍스트 없음)이므로 텍스트 추출본에 수식 본문이 없음. 수식 제목·표기(Notation) 표·텍스트로 적힌 일부 식(예: `b = (X'X)-1X'y`, `Proportion = Amount / Total`, DF 규칙, `1 − P(F ≤ fj)`)만 원문 그대로 수록. 나머지는 "공식 본문은 이미지라 문서 텍스트에 없음"으로 표기.
3. "Display available designs" 대화상자 페이지(RS·Mixture·Taguchi 모두)는 **"This dialog box does not take any input"** 이라는 설명만 있고 표 자체는 문서에 없음. RS 의 가용 설계 숫자는 "Summary of central composite designs" / "Summary of Box-Behnken designs" 표에서, Mixture 의 가용 범위는 analyze-mixture methods 의 "Simplex lattice designs" 표에서 가져옴.
4. ko-kr 폴더에 존재하는 대응 파일(txt): mixture analyze example, mixture create 예제 3개 + overview, RS analyze example, CCD 예제, Box-Behnken 예제, select-a-response-surface-design, perform-a-mixtures-experiment, what-is-a-mixture-design, response-surface-central-composite-and-box-behnken-designs. 이 파일들에서 뽑은 한국어 UI 라벨 매핑을 각 절 끝에 수록.

---

## 1. Create Response Surface Design — Central Composite (CCD)

메뉴 경로: `Stat > DOE > Response Surface > Create Response Surface Design` (select-a-response-surface-design.txt, create-_096e9000.txt)

### 1.1 설계 유형 선택 (select-a-response-surface-design.txt / select-_6982412c.txt)
- **Create Response Surface Design (Central Composite)**: 중앙점을 포함한 요인/부분요인 설계에 축점(axial/star points) 그룹을 추가하여 곡면성 추정.
- **Create Response Surface Design (Box-Behnken)**: 실험 공간 모서리(edge)의 중간점에 처리 조합이 있고 연속 요인이 3개 이상 필요. 내장된 요인/부분요인 설계가 없음.

### 1.2 메인 대화상자 필드 (예제 파일 create-_34e2ebec.txt, create-_f0ea3592.txt 의 단계 서술에서 추출)
| 필드 (영문 원문) | 내용 |
|---|---|
| Type of Design | `Central composite` / `Box-Behnken` 라디오 |
| Number of continuous factors | 드롭다운. CCD 는 Summary 표 기준 2~10, Box-Behnken 은 3,4,5,6,7,9,10 (표 §1.5, §2.2) |
| Number of categorical factors | 문서에 명시적 필드 설명은 없으나, all-statistics (create-_2b401544.txt) 에 범주형 요인 1개(C) 포함 CCD 예가 있고, Factors 하위 대화상자에 `Categorical Factors` 입력이 있음 |
| `Display Available Designs` 버튼 | 입력 없음. 설계 유형(블록 유무)·연속 요인 수별 런 수 표시 (create-_3c72e2af.txt, create-_eb6a23ae.txt). **표 내용 자체는 문서에 없음** |
| `Designs` 버튼 | §1.3 |
| `Factors` 버튼 | §1.4 |
| `Options` 버튼 | §1.6 |
| `Results` 버튼 | 예제에서 `Summary table and design table` 선택 (create-_34e2ebec.txt). 다른 선택지는 문서에 없음 |

### 1.3 Designs 하위 대화상자 — CCD (create-_096e9000.txt)
경로: `... > Create Response Surface Design > Designs`

- **Designs table**: 기본 설계의 실험 런 수와 블록 수를 선택. 실제 총 런 수는 중앙점 수·반복 수·범주형 요인 수준 수에 따라 달라짐. 예제에서는 "Select the second design (full design with 20 runs and 2 blocks) in the white box" (3요인) (create-_34e2ebec.txt).
- **Number of center points**
  - `Default`: Minitab 이 직교 블록을 만드는 중앙점 수를 결정. 블록이 없으면 default 는 회전 가능(rotatable) 설계를 만듦.
  - `Custom`: 중앙점 수를 직접 지정. 축 블록이 있는 설계면 블록 유형별로 지정:
    - `Cube block`: 고·저 수준 런이 있는 각 블록에 추가할 중앙점 수. 큐브 블록이 여러 개면 가능한 한 균등 분배.
    - `Axial block`: 축 수준 런이 있는 블록에 추가할 중앙점 수.
- **Value of Alpha** (축점의 중심으로부터 코드화 거리)
  - `Default`: 직교 블록이 되도록 α 결정. 블록이 없으면 회전 가능 설계.
  - `Face Centered`: 축점에 요인의 고·저 수준 사용 (α = 1).
  - `Custom`: α 직접 지정. 1 미만이면 축점이 큐브 내부, 1 초과면 큐브 외부.
  - Note (원문): "A value of F0.25 guarantees rotatability. F is the number of factorial points in the design." (F^0.25 = 요인점 수의 1/4 제곱)
- **Number of replicates**: 기본 설계의 각 런을 수행할 횟수. 나중에 `Stat > DOE > Modify Design` 으로 추가 가능.
  - `Block on replicates`: 각 반복을 별도 블록에 배치. 기본 설계에 블록이 있으면 총 블록 수 = 기본 블록 수 × 반복 수.

### 1.4 Factors 하위 대화상자 — CCD (create-_bb93f5e3.txt)
- **Levels Define**: 입력한 요인 수준이 `Cube points` 인지 `Axial points` 인지 선택.
- **Name**: 요인 이름. 기본값은 알파벳 순(I 는 건너뜀).
- **Continuous Factors**: 각 요인의 이름, Low, High. 기본값 Low = −1, High = +1. (예: 150 / 250)
- **Categorical Factors**: 이름, 수준 수, 수준 값.

### 1.5 "Summary of central composite designs" 표 — 숫자 그대로 (summary-of-central-composite-designs.txt)
원문 서두: "The table summarizes the designs generated by the central composite design commands. If the design has blocks, then the blocks are orthogonal."

| Factors | Design | Runs | Blocks | Cube blocks | Cube runs | Center points | Cube center points | Axial center points | Default alpha | Rotatable |
|---|---|---|---|---|---|---|---|---|---|---|
| 2 | Full | 13 | 1 | --- | 4 | 5 | --- | 0 | 1.414 | y |
| 2 | Full | 14 | 2 | 1 | 4 | 6 | 3 | 3 | 1.414 | y |
| 3 | Full | 14 | 1 | --- | 8 | 6 | --- | 0 | 1.682 | y |
| 3 | Full | 20 | 2 | 1 | 8 | 6 | 4 | 2 | 1.633 | n |
| 3 | Full | 20 | 3 | 2 | 8 | 6 | 4 | 2 | 1.633 | n |
| 4 | Full | 31 | 1 | --- | 16 | 7 | --- | 0 | 2 | y |
| 4 | Full | 30 | 2 | 1 | 16 | 6 | 4 | 2 | 2 | y |
| 4 | Full | 30 | 3 | 2 | 16 | 6 | 4 | 2 | 2 | y |
| 5 | Full | 52 | 1 | --- | 32 | 10 | --- | 0 | 2.378 | y |
| 5 | Full | 54 | 2 | 1 | 32 | 12 | 8 | 4 | 2.366 | n |
| 5 | Full | 54 | 3 | 2 | 32 | 12 | 8 | 4 | 2.366 | n |
| 5 | Half | 32 | 1 | (빈칸) | 16 | 6 | --- | 0 | 2 | y |
| 5 | Half | 33 | 2 | 1 | 16 | 7 | 6 | 1 | 2 | y |
| 6 | Full | 90 | 1 | --- | 64 | 14 | --- | 0 | 2.828 | y |
| 6 | Full | 90 | 2 | 1 | 64 | 14 | 8 | 6 | 2.828 | y |
| 6 | Full | 90 | 3 | 2 | 64 | 14 | 8 | 6 | 2.828 | y |
| 6 | Full | 90 | 5 | 4 | 64 | 14 | 8 | 6 | 2.828 | y |
| 6 | Half | 53 | 1 | --- | 32 | 9 | --- | 0 | 2.378 | y |
| 6 | Half | 54 | 2 | 1 | 32 | 10 | 8 | 2 | 2.366 | n |
| 6 | Half | 54 | 3 | 2 | 32 | 10 | 8 | 2 | 2.366 | n |
| 7 | Full | 152 | 1 | --- | 128 | 10 | --- | 0 | 3.364 | y |
| 7 | Full | 160 | 2 | 1 | 128 | 18 | 8 | 10 | 3.364 | y |
| 7 | Full | 160 | 3 | 2 | 128 | 18 | 8 | 10 | 3.364 | y |
| 7 | Full | 160 | 5 | 4 | 128 | 18 | 8 | 10 | 3.364 | y |
| 7 | Half | 88 | 1 | --- | 64 | 10 | --- | 0 | 2.828 | y |
| 7 | Half | 90 | 2 | 1 | 64 | 12 | 8 | 4 | 2.828 | y |
| 7 | Half | 90 | 3 | 2 | 64 | 12 | 8 | 4 | 2.828 | y |
| 7 | Half | 90 | 5 | 4 | 64 | 12 | 8 | 4 | 2.828 | y |
| 8 | Half | 154 | 1 | --- | 128 | 10 | --- | 0 | 3.364 | y |
| 8 | Half | 160 | 2 | 1 | 128 | 16 | 8 | 8 | 3.364 | y |
| 8 | Half | 160 | 3 | 2 | 128 | 16 | 8 | 8 | 3.364 | y |
| 8 | Half | 160 | 5 | 4 | 128 | 16 | 8 | 8 | 3.364 | y |
| 8 | Quarter | 90 | 1 | --- | 64 | 10 | --- | 0 | 2.828 | y |
| 8 | Quarter | 90 | 2 | 1 | 64 | 10 | 8 | 2 | 2.828 | y |
| 8 | Quarter | 90 | 3 | 2 | 64 | 10 | 8 | 2 | 2.828 | y |
| 8 | Quarter | 90 | 5 | 4 | 64 | 10 | 8 | 2 | 2.828 | y |
| 9 | Quarter | 156 | 1 | --- | 128 | 10 | --- | 0 | 3.364 | y |
| 9 | Quarter | 160 | 2 | 1 | 128 | 14 | 8 | 6 | 3.364 | y |
| 9 | Quarter | 160 | 3 | 2 | 128 | 14 | 8 | 6 | 3.364 | y |
| 9 | Quarter | 160 | 5 | 4 | 128 | 14 | 8 | 6 | 3.364 | y |
| 10 | Eighth | 158 | 1 | --- | 128 | 10 | --- | 0 | 3.364 | y |
| 10 | Eighth | 160 | 2 | 1 | 128 | 12 | 8 | 4 | 3.364 | y |
| 10 | Eighth | 160 | 3 | 2 | 128 | 12 | 8 | 4 | 3.364 | y |
| 10 | Eighth | 160 | 5 | 4 | 128 | 12 | 8 | 4 | 3.364 | y |

메모:
- 원문에서 "5 | Half | 32 | 1" 행의 Cube blocks 셀은 `---` 가 아닌 빈칸.
- 검산(문서에 산식은 없음, 분석가 검산): `Runs = Cube runs + 2K(축점) + Center points` 가 **44행 중 43행에서 성립**. 유일한 예외는 "3 | Full | 14 | 1 | --- | 8 | 6 | --- | 0 | 1.682 | y" 행으로 8 + 6 + 6 = 20 ≠ 14. 원문 숫자(14)를 그대로 옮겼으나 원문 오타 가능성이 높음(α = 1.682 는 3요인 회전 가능 CCD 의 표준값이며 그 설계는 20런). 구현 시 이 행만 별도 검토 필요.
- 또한 Center points = Cube center points + Axial center points 가 블록 설계 모든 행에서 성립(예: 2 Full 2블록 6 = 3 + 3; 7 Full 2블록 18 = 8 + 10).
- 구현 시 이 표를 **그대로 룩업 테이블**로 쓰는 것을 권장.

### 1.6 Options 하위 대화상자 (create-_814483e0.txt)
- **Randomize runs**: 블록 내에서 런 순서를 랜덤화할지, 표준 순서로 둘지 선택.
  - **Base for random data generator**: 같은 base 를 넣으면 같은 런 순서 재현.
  - 워크시트 저장 후에는 `Display Response Surface Design` 으로 표준/랜덤 순서 보기, `Modify Design` 으로 재랜덤화.
- **Store design in worksheet**: 해제하면 워크시트에 저장하지 않고 런 수·속성만 확인. 분석하려면 반드시 저장해야 함.

### 1.7 Blocks in a central composite design 규칙 (blocks-in-a-central-composite-design.txt)
- 직교 블록 수는 요인 수·런 수·선택한 fraction 에 따라 다름.
- CCD 는 **항상 요인(factorial) 블록과 축점(axial) 블록으로 분리 가능**. 요인이 3개 이상이면 요인 블록을 2개 이상으로 더 나눌 수 있음. 설계 생성 시 Minitab 이 적절한 선택지를 표시.
- 반복 추가 시 "block on replicates" 동작:
  - 기존 블록이 없으면: 각 반복 세트를 별도 블록에 배치.
  - 기존 블록이 있으면: 기존 블록 체계를 복제. 블록 수 = 원래 블록 수 × 반복 수, 블록당 런 수는 동일.
  - 기존 블록이 있지만 반복에 블록을 만들지 않으면: 각 블록 내 점을 반복. 블록당 런 수 = 원래 런 수 × 반복 수, 블록 수는 그대로.
- Note: α 와 중앙점 수의 조합이 회전성·직교 블록 여부를 결정. 둘 다 가능하면 둘 다 만족하는 default, 블록이 있어 둘 다 불가능하면 직교 블록 우선.

### 1.8 Alpha (what-is-alpha-in-a-c_92088d54.txt, all-statistics create-_2b401544.txt)
- α = 축점(star point)의 중심으로부터 거리. α<1 큐브 내부, α=1 큐브 면 위(face-centered), α>1 큐브 외부.
- 블록 있고 둘 다 불가능 → 직교 블록이 되도록 α 선택; 블록 없음 → 회전 가능하도록 α 선택.
- "Minitab's alpha values agree with those listed in Montgomery" (D. C. Montgomery (2004). Design and Analysis of Experiments, 6th ed.).
- Face-centered 설계: α = 1, 요인당 3수준 필요, 기존 요인/해상도 V 설계에 축점을 추가해서도 생성 가능 (response-surface-cen_4229705b.txt).

### 1.9 생성 출력 형식 (all-statistics create-_2b401544.txt, 예제 create-_34e2ebec.txt)
출력 항목(순서대로):
1. **Design Summary** 표: `Factors:`, `Replicates:`, `Base runs:`, `Total runs:`, `Base blocks:`, `Total blocks:` (2열×3행 레이아웃)
2. `α = <값>` 한 줄
3. `Two-level factorial: Full factorial` (또는 fraction 명) 한 줄
4. **Point Types** 표: `Cube points:`, `Center points in cube:`, `Axial points:`, `Center points in axial:`
5. **Design Table (randomized)**: 열 `Run | Blk | A | B | C ...`
   - 연속 요인은 코드화 단위: −1 = 저수준, 1 = 고수준, 0 = 중간점, ±α 값 = 축 수준(예: −1.414 / 1.414 혹은 1.41421).
   - 범주형 요인은 범주에 대응하는 숫자로 표시.
   - 요인 문자는 생성 시 순서대로 알파벳(I 건너뜀).
- 정의: Base runs = 기본 설계의 요인 수준 조합 수; Total runs = Base runs × replicates. Base blocks = 반복 추가 전 블록 수; Total blocks 는 반복으로 생긴 블록 포함.
- CCD 구성: "cube" 부분(2^K 또는 2^(k−p) 요인점) + 2K 축점 + 중앙점.
- Center points in axial: 모든 요인이 중앙 수준이면서 축 블록에 있는 점.
- 각 반복은 같은 수의 중앙점을 추가하고, 범주형 요인의 각 수준도 같은 수의 중앙점을 추가함 (create-_096e9000.txt).

### 1.10 CCD 예제 — 3요인 2블록 20런 (create-_34e2ebec.txt) — 숫자 그대로
시나리오: 결정 성장 최대화(촉매 노출 시간, 촉매 비율, 온도). 단계: Type of Design = Central composite → Number of continuous factors = 3 → Designs 에서 두 번째 설계(full, 20 runs, 2 blocks) 선택 → Results 에서 Summary table and design table.

Design Summary
| | | | |
|---|---|---|---|
| Factors: | 3 | Replicates: | 1 |
| Base runs: | 20 | Total runs: | 20 |
| Base blocks: | 2 | Total blocks: | 2 |

α = 1.633
Two-level factorial: Full factorial

Point Types
| | |
|---|---|
| Cube points: | 8 |
| Center points in cube: | 4 |
| Axial points: | 6 |
| Center points in axial: | 2 |

Design Table (randomized)
| Run | Blk | A | B | C |
|---|---|---|---|---|
| 1 | 1 | 1.000 | -1.000 | 1.000 |
| 2 | 1 | -1.000 | -1.000 | -1.000 |
| 3 | 1 | 1.000 | -1.000 | -1.000 |
| 4 | 1 | -1.000 | -1.000 | 1.000 |
| 5 | 1 | 1.000 | 1.000 | 1.000 |
| 6 | 1 | -1.000 | 1.000 | 1.000 |
| 7 | 1 | -1.000 | 1.000 | -1.000 |
| 8 | 1 | 0.000 | 0.000 | 0.000 |
| 9 | 1 | 1.000 | 1.000 | -1.000 |
| 10 | 1 | 0.000 | 0.000 | 0.000 |
| 11 | 1 | 0.000 | 0.000 | 0.000 |
| 12 | 1 | 0.000 | 0.000 | 0.000 |
| 13 | 2 | 0.000 | 0.000 | 0.000 |
| 14 | 2 | 1.633 | 0.000 | 0.000 |
| 15 | 2 | 0.000 | 0.000 | 0.000 |
| 16 | 2 | 0.000 | -1.633 | 0.000 |
| 17 | 2 | 0.000 | 0.000 | -1.633 |
| 18 | 2 | -1.633 | 0.000 | 0.000 |
| 19 | 2 | 0.000 | 1.633 | 0.000 |
| 20 | 2 | 0.000 | 0.000 | 1.633 |

해석 원문 요지: 첫 런에서 A, C 는 수준 1, B 는 −1. 워크시트에는 요인 이름과 비코드화 수준 표시. 기본 랜덤화되므로 재생성 시 런 순서는 예제와 다름.

### 1.11 CCD all-statistics 예제 — 연속 2 + 범주형 1, 2블록 28런 (create-_2b401544.txt) — 숫자 그대로
문맥: "the design table shows 14 runs in each of two blocks, for a total of 28 runs. The runs are randomized within each block. −1.414 and 1.414 indicate the low and high axial levels. In the first run, the continuous factors A and B are at the middle point ... and the categorical factor C is at level 1."

Design Table (randomized)
| Run | Blk | A | B | C |
|---|---|---|---|---|
| 1 | 1 | 0.00000 | 0.00000 | 1 |
| 2 | 1 | -1.00000 | -1.00000 | 1 |
| 3 | 1 | 1.00000 | -1.00000 | 1 |
| 4 | 1 | 0.00000 | 0.00000 | 1 |
| 5 | 1 | -1.00000 | -1.00000 | 2 |
| 6 | 1 | 0.00000 | 0.00000 | 1 |
| 7 | 1 | -1.00000 | 1.00000 | 1 |
| 8 | 1 | 1.00000 | 1.00000 | 2 |
| 9 | 1 | 1.00000 | 1.00000 | 1 |
| 10 | 1 | -1.00000 | 1.00000 | 2 |
| 11 | 1 | 0.00000 | 0.00000 | 2 |
| 12 | 1 | 0.00000 | 0.00000 | 2 |
| 13 | 1 | 0.00000 | 0.00000 | 2 |
| 14 | 1 | 1.00000 | -1.00000 | 2 |
| 15 | 2 | 0.00000 | 0.00000 | 2 |
| 16 | 2 | 0.00000 | 0.00000 | 1 |
| 17 | 2 | 0.00000 | 1.41421 | 2 |
| 18 | 2 | -1.41421 | 0.00000 | 1 |
| 19 | 2 | -1.41421 | 0.00000 | 2 |
| 20 | 2 | 0.00000 | 0.00000 | 2 |
| 21 | 2 | 0.00000 | -1.41421 | 2 |
| 22 | 2 | 0.00000 | 0.00000 | 1 |
| 23 | 2 | 0.00000 | -1.41421 | 1 |
| 24 | 2 | 1.41421 | 0.00000 | 2 |
| 25 | 2 | 0.00000 | 0.00000 | 2 |
| 26 | 2 | 0.00000 | 0.00000 | 1 |
| 27 | 2 | 0.00000 | 1.41421 | 1 |
| 28 | 2 | 1.41421 | 0.00000 | 1 |

(이 예는 2요인 Full 14런 2블록 설계(Summary 표의 2행: cube 4, center 6 = cube 3 + axial 3, α 1.414)가 범주형 요인 2수준으로 **2배**가 된 것: 14 × 2 = 28. 이 "범주형 수준마다 설계 복제" 규칙은 all-statistics 의 "Each level of a categorical factor also adds the same number of center points" 서술과 일치.)

### 1.12 Define Custom / Display·Modify / Select Optimal (RS 영역) 
- **Define Custom Response Surface Design** (define-custom-...ea9fc237.txt): 필드 `Continuous Factors`(연속 요인 열), `Categorical Factors`(범주형 요인 열) 입력. 그 외 필드는 문서에 없음.
- **Display and Modify Design** (response-surface__display-and-modify-design.txt): Display Design 은 워크시트 표시 방식 변경, Modify Design 은 분석 가능한 형식을 유지하며 설계 변경. 상세는 factorial 영역 참조(본 담당 범위 밖).
- **Select Optimal Design** (response-surface__select-optimal-design.txt): "select, add, exchange, or evaluate runs from a candidate set". 상세는 §6.

### 1.13 ko-kr UI 라벨 매핑 — CCD (ko-kr create-_34e2ebec.txt, select-_6982412c.txt, response-surface-cen_4229705b.txt)
| 영문 | 한국어판 |
|---|---|
| Stat > DOE > Response Surface > Create Response Surface Design | 통계분석 > 실험계획법 > 반응 표면 설계 > 반응 표면 설계 생성 |
| Type of Design | 설계 유형 |
| Central composite | 중심 합성 계획법 |
| Box-Behnken | Box-Behnken |
| Number of continuous factors | 연속 요인 수 |
| Designs | 설계 |
| Results | 결과 |
| Summary table and design table | 요약 표 및 설계 표 |
| Design Summary | 설계 요약 |
| Factors: / Replicates: | 요인: / 반복실험: |
| Base runs: / Total runs: | 기본 런: / 전체 런 수: |
| Base blocks: / Total blocks: | 기본 블럭: / 전체 블럭 수: |
| Two-level factorial: Full factorial | 2-수준 요인 설계: 완전 요인 설계 |
| Point Types | 점 유형 |
| Cube points: | 꼭지점: |
| Center points in cube: | 입방체의 중앙점: |
| Axial points: | 축 점: |
| Center points in axial: | 축의 중앙점: |
| Design Table (randomized) | 설계 표(랜덤화) |
| Run / Blk | 런 / 블록 |
| axial point (star point) | 축 점(별 점) |
| orthogonal blocks / rotatability | 직교 블럭 / 회전성 |
| face-centered design | 내접 설계 |
| curvature | 곡면성 |
| continuous factors | 계량형 요인 (select-_6982412c ko) / 연속 요인 (예제 ko) |

---

## 2. Create Response Surface Design — Box-Behnken

### 2.1 Designs 하위 대화상자 — Box-Behnken (create-_b108c6d9.txt)
- **Number of center points**: `Default`(연속 요인 수에 따라 Minitab 이 결정) / `Custom`(직접 지정). 각 반복과 범주형 요인의 각 수준이 같은 수의 중앙점을 추가.
- **Number of blocks**: 기본 설계의 블록 수. 반복을 별도 블록에 두면 총 블록 = 기본 블록 × 반복 수.
- **Number of replicates** + **Block on replicates**: CCD 와 동일.
- (CCD 와 달리 Alpha 선택·Cube/Axial 중앙점 구분 없음.)

### 2.2 Options (create-_897f0ad4.txt): CCD 와 동일 — Randomize runs, Base for random data generator, Store design in worksheet.

### 2.3 "Summary of Box-Behnken designs" 표 — 숫자 그대로 (summary-of-box-behnken-designs.txt)
| Number of factors | Number of runs | Optional number of blocks | Default number of center points |
|---|---|---|---|
| 3 | 15 | 1 | 3 |
| 4 | 27 | 3 | 3 |
| 5 | 46 | 2 | 3 |
| 6 | 54 | 2 | 6 |
| 7 | 62 | 2 | 6 |
| 9 | 130 | 5 or 10 | 10 |
| 10 | 170 | 2 | 10 |

(요인 수 8 은 표에 없음 → Box-Behnken 8요인은 제공되지 않는 것으로 해석. 단 문서에 명시 문장은 없음.)

### 2.4 Blocks in a Box-Behnken design 규칙 (blocks-in-a-box-behnken-design.txt)
- 블록 추가 방법 수는 요인 수에 따라 다르며 **모든 블록 설계는 직교 블록**.
  - 3요인: 블록 불가
  - 4요인: 3블록
  - 5, 6, 7, 10요인: 2블록
  - 9요인: 5블록 또는 10블록
- 반복에 대한 블록 규칙은 CCD 와 동일(기존 블록 없음 → 반복마다 블록; 기존 블록 있음 + block on replicates → 블록 체계 복제; 기존 블록 있음 + 미선택 → 블록 내 반복).

### 2.5 특성 (response-surface-cen_4229705b.txt)
- 항상 요인당 3수준(−1, 0, 1). 모든 요인이 극단 설정인 런(예: 모두 저수준)을 포함하지 않음. 축점 없음 → 안전 운전 영역 내. 내장 요인 설계가 없어 순차 실험에 부적합.

### 2.6 Box-Behnken 예제 — 3요인 15런 (create-_f0ea3592.txt) — 숫자 그대로
단계: Type of Design = Box-Behnken → Number of continuous factors = 3 → Designs → OK → Results: Summary table and design table.

Design Summary
| | | | |
|---|---|---|---|
| Factors: | 3 | Replicates: | 1 |
| Base runs: | 15 | Total runs: | 15 |
| Base blocks: | 1 | Total blocks: | 1 |

Center points: 3

Design Table (randomized)
| Run | Blk | A | B | C |
|---|---|---|---|---|
| 1 | 1 | -1 | 0 | -1 |
| 2 | 1 | -1 | 0 | 1 |
| 3 | 1 | -1 | -1 | 0 |
| 4 | 1 | 1 | -1 | 0 |
| 5 | 1 | 1 | 0 | -1 |
| 6 | 1 | 0 | -1 | -1 |
| 7 | 1 | 1 | 0 | 1 |
| 8 | 1 | -1 | 1 | 0 |
| 9 | 1 | 0 | 1 | 1 |
| 10 | 1 | 1 | 1 | 0 |
| 11 | 1 | 0 | -1 | 1 |
| 12 | 1 | 0 | 0 | 0 |
| 13 | 1 | 0 | 0 | 0 |
| 14 | 1 | 0 | 0 | 0 |
| 15 | 1 | 0 | 1 | -1 |

출력 형식 차이: CCD 와 달리 `α = ...`, `Two-level factorial`, `Point Types` 표가 없고 `Center points: 3` 한 줄만 표시. 설계표 값은 정수(−1/0/1)로 표시.

### 2.7 ko-kr 매핑 — Box-Behnken (ko-kr create-_f0ea3592.txt)
| 영문 | 한국어판 |
|---|---|
| Center points: | 중앙점: |
| (나머지는 §1.13 과 동일) | |

---

## 3. Analyze Response Surface Design

메뉴: `Stat > DOE > Response Surface > Analyze Response Surface Design` (before-you-start__example.txt)

### 3.1 메인 대화상자
- **Responses**: 반응 열 입력(예제: `Strength`). 다른 메인 필드는 문서에 없음(stepwise 선택은 Graphs 문서에서 언급 — "Unless you use a stepwise selection method ... backwards selection or stepwise selection ... forward selection ... Alpha to remove / Alpha to enter", 관련 상세 페이지 "Perform stepwise regression for Analyze Response Surface Design" 은 담당 파일에 없음) (perfor_ad8d554f.txt).
- 버튼: `Terms`, `Options`, `Graphs`, `Results`(문서로 확인). `Stepwise`, `Storage`, `Prediction` 등은 문서에 없음.

### 3.2 Terms 하위 대화상자 (perfor_d6a65ef0.txt)
- **Include the following terms**: 모형 차수 선택 드롭다운. 선택에 따라 Selected Terms 가 바뀜. 원문 예: "if you choose Linear + squares, ... Selected Terms: All main effects and their quadratic effects. Available Terms: All 2-way interactions."
  - 문서에 등장하는 선택지 이름: `Linear + squares` (perfor_d6a65ef0.txt), `Linear` (optimal 예제 examp_61fbc6b2.txt: "From the Include the following terms drop-down list, select Linear"), full quadratic 이 기본값(optimal 예제 a837a12e: "the full quadratic terms that are default in the Terms sub-dialog box"). `Linear + interactions`, `Full quadratic` 이라는 정확한 라벨 문자열은 **문서에 없음**(추정하지 말 것).
- **Available Terms** / **Selected Terms** 리스트, 화살표 버튼(단일/더블), 더블클릭 이동.
- **Include blocks in the model** 체크박스: 블록 열에 값이 여러 개면 활성화.

### 3.3 Options 하위 대화상자 (perfor_40ad6d39.txt)
- **Weights**: 가중 회귀용 숫자 열(≥0, 반응과 같은 행 수).
- **Confidence level for all intervals**: 계수·적합치 CI 신뢰수준(보통 95%). CI 표시는 Results 에서 `Expanded tables` 선택 필요.
- **Type of confidence interval**: `Two-sided` / `Lower bound` / `Upper bound`.
- **Box-Cox Transformation**: `No Transformation` / `Optimal λ`(기본은 0.5 또는 정수로 반올림; 반올림 안 하려면 File > Options > Linear Models > Display of Results) / `λ = 0 (natural log)` / `λ = 0.5 (square root)` / `λ`(직접 지정; 보통 −2~2). 모든 반응값 > 0 필요.

### 3.4 Graphs 하위 대화상자 (perfor_ad8d554f.txt)
- **Effects Plots**: `Pareto`, `Normal`, `Half Normal`. 오차 자유도 ≥ 1 일 때만 그림. 유의수준 = 1 − 신뢰수준(stepwise 미사용 시); backward/stepwise 면 Alpha to remove, forward 면 Alpha to enter.
- **Residuals for Plots**: `Regular` / `Standardized` / `Deleted`.
- **Residual Plots**: `Individual plots`(`Histogram`, `Normal plot`, `Residuals versus fits`, `Residuals versus order`) / `Four in one`.
- **Residuals versus variables**: 변수 지정.

### 3.5 Results 하위 대화상자 (perfor_b23b80b5.txt)
- **Display of results**: `Simple tables` / `Expanded tables`(ANOVA, Coefficients, Model Summary, Fits and Diagnostics 확장판).
- **Method**: 비기본 설정 요약 표.
- **Analysis of variance**
- **Model summary**: 확장판은 PRESS, AICc, BIC 포함.
- **Coefficients**: `Default coefficients` / `Full set of coefficients`(범주형의 마지막 종속 수준 포함).
- **Regression equation**: `Separate equation for each set of factor levels` / `Single equation`.
- **Fits and diagnostics**: `Only for unusual observations` / `For all observations`.

### 3.6 출력표 형식
1. **Coded Coefficients**: 열 `Term | Coef | SE Coef | T-Value | P-Value | VIF`. 첫 행 `Constant`(VIF 빈칸). 계수는 모두 **코드화 단위** (interp_2f7cc302.txt). Expanded 에서 `95% CI` 추가.
   - 항 표기: 주효과 `HotBarT`, 제곱항 `HotBarT*HotBarT`, 교호작용 `HotBarT*DwelTime`.
   - VIF 해석 표: VIF = 1 Not correlated / 1 < VIF < 5 Moderately correlated / VIF > 5 Highly correlated.
2. **Model Summary**: `S | R-sq | R-sq(adj) | R-sq(pred)` (expanded: + PRESS, AICc, BIC). R-sq(adj), R-sq(pred) 는 음수면 0 표시.
3. **Analysis of Variance**: 열 `Source | DF | Adj SS | Adj MS | F-Value | P-Value` (expanded 는 Seq SS, Contribution 추가 — interp_ab6d6d41.txt 의 "Seq SS", "Contribution" 항목).
   - **Source 행 종류·순서(문서 예제 기준)**: `Model` → (`Blocks` — 블록 포함 시; 문서에 "P-value – Blocks", "F-value for blocks" 항목 있음, 예제 표에는 블록 없음) → `Linear` → 각 주효과 → `Square` → 각 제곱항 → `2-Way Interaction` → 각 교호작용 → `Error` → `Lack-of-Fit` → `Pure Error` → `Total`.
   - 그룹 라벨 표기: SealStrength 예제는 `2-Way Interaction`(단수), interp_ab6d6d41.txt 의 다른 예제(Material/InjPress/InjTemp/CoolTemp)는 `2-Way Interactions`(복수). 두 표기가 모두 문서에 존재.
   - Lack-of-Fit / Pure Error 는 두 조건(적합 가능하지만 모형에 없는 항 존재 + 반복 존재) 충족 시에만 분리.
4. **Regression Equation in Uncoded Units**: `<Response> | = | <식>` 형식 한 행. 범주형이 있으면 수준 조합별 식 또는 단일 식.
5. **Fits and Diagnostics for Unusual Observations**: 열 `Obs | <Response> | Fit | Resid | Std Resid | (flag)`; 플래그 `R` = Large residual, `X` = 큰 레버리지(leverage > 3p/n 또는 0.99 중 작은 값; method_a9d3dd88.txt). 표 아래 범례 `R  Large residual`.

### 3.7 Methods and formulas — 원문 텍스트 그대로 (이미지 수식은 "이미지" 표기)
**Design matrix** (method_18bb7972.txt): 첫 열은 상수항 1 열. k 블록이면 (k − 1) 블록 열(코딩은 Factorial Models 와 동일). 이어 주효과 열(범주형은 여러 열 가능), 제곱항 열(해당 요인 열의 자기 곱), 교호작용 열(두 열의 곱). 데이터가 지원 못해 제거된 항은 저장된 설계행렬에 없음.

**Coefficient (Coef)**: "In matrix terms, the formula that calculates the vector of coefficients in the model is:" — 수식 이미지(텍스트 없음). Notation: X = design matrix, Y = response vector. (혼합물 문서에는 동일 식이 텍스트로 `b = (X'X)-1X'y` 로 존재 — §5.4.)

**Box-Cox transformation**: λ ≠ 0 이면 Y^λ, λ = 0 이면 ln(Y). λ < 0 이면 변환값에 −1 을 곱해 순서 유지. 탐색 범위 −2 ~ 2. 표: λ = 2 → Y′ = Y 2; λ = 0.5 → (이미지); λ = 0 → Y′ = ln(Y); λ = −0.5 → (이미지); λ = −1 → Y′ = −1 / Y.

**Adjusted sum of squares** (method_91d6a8aa.txt), 원문:
```
SSR(X3 | X1, X2) = SSE (X1, X2) - SSE (X1, X2, X3) or
SSR(X3 | X1, X2) = SSR (X1, X2, X3) - SSR (X1, X2)
SSR(X2, X3 | X1) = SSE (X1) - SSE (X1, X2, X3) or
SSR(X2, X3 | X1) = SSR (X1, X2, X3) - SSR (X1)
```
**Sum of squares (SS)**: 행렬 수식 이미지. Notation: b = vector of coefficients, X = design matrix, Y = vector of response values, n = number of observations, J = n by n matrix of 1s.

**Sequential sum of squares**: 항 입력 순서에 의존, 이전 항이 주어졌을 때 각 항이 설명하는 고유 부분.

**Degrees of freedom (DF)** 원문:
```
DF for a numeric factor = 1
DF for a categorical factor = b − 1
DF for a quadratic term = 1
DF for blocks = c − 1
DF for error = n − p
DF for pure error = (이미지)
DF for lack of fit = m − p
DF total = n − 1
```
교호작용 DF = 구성 항 DF 의 곱. Notation: b = 요인 수준 수, c = 블록 수, n = 총 관측 수, ni = i번째 요인수준조합 관측 수, m = 요인수준조합 수, p = 계수 수.

**Adj MS – Model / Term / Error**: 수식 이미지. MS Error = s² (p = 상수 제외 계수 수).

**F**: F(Term), F(Lack-of-fit) 수식 이미지. Notation: Adj MS Term, MS Error, MS Lack-of-fit, MS Pure error.

**P-value – ANOVA**: Numerator DF = 검정 항(들)의 DF 합, Denominator DF = 오차 DF. Formula: `1 − P(F ≤ fj)`.
**P-value – Lack-of-fit**: Numerator DF = lack-of-fit DF, Denominator DF = pure error DF. Formula: `1 − P(F ≤ fj)`.

**Fits and residuals** (method_a6627ad5.txt): Fit, SE Fit(1 예측변수/다중/가중 W 포함), Residual, Standardized residual(= internally Studentized; e_i, h_i = X(X'X)⁻¹X' 의 i번째 대각, s²), Deleted (Studentized) residual(= externally Studentized; s(i)², t 분포), Confidence interval, Prediction interval — 모두 수식 이미지. 텍스트로 남은 조각: Prediction interval "The formula is: 0+ t(1 -α /2; n - p) s(pred)" (앞부분 ŷ0 기호 유실).

**Diagnostic measures** (method_a9d3dd88.txt): Leverage h_i (hat matrix H, 0~1, 기준 3p/n 또는 .99 중 작은 값이면 X 표시), Cook's distance D, DFITS — 수식 이미지.

**Goodness-of-fit** (method_e97f0d5f.txt): S(= √MSE 의미, 이미지), R-sq, R-sq(adj)(음수면 0), PRESS, R-sq(pred)(음수면 0), Log-likelihood(비가중/가중, 가중 0 관측 제외), AICc("AICc is not calculated when ." — 조건이 이미지), BIC, Mallows' Cp — 수식 전부 이미지. Notation: p = 상수 포함 계수 수(AICc/BIC/Cp), p = 모형 항 수(R-sq adj).

**Effects plots** (method_484a873b.txt): Pareto 기준선은 오차 DF 를 갖는 t 분포의 (1 – α / 2) 분위수 t 에 그림. 제목 "Pareto Chart of the standardized effects". Normal plot: 표준화 효과 vs 정규 점수, 기준선은 SD 1 정규분포, p < α 효과 라벨. Half normal: |표준화 효과|. 오차 DF 0 이면 그리지 않음.

### 3.8 예제 — SealStrength, 반응 Strength (before-you-start__example.txt) — 숫자 그대로
단계: Open SealStrength.MWX → Responses = Strength → Graphs: Residual Plots `Four in one`.

Coded Coefficients
| Term | Coef | SE Coef | T-Value | P-Value | VIF |
|---|---|---|---|---|---|
| Constant | 28.44 | 1.66 | 17.09 | 0.000 | |
| HotBarT | 1.685 | 0.899 | 1.87 | 0.079 | 1.00 |
| DwelTime | -1.719 | 0.899 | -1.91 | 0.074 | 1.00 |
| HotBarP | 1.481 | 0.899 | 1.65 | 0.119 | 1.00 |
| MatTemp | 1.060 | 0.899 | 1.18 | 0.255 | 1.00 |
| HotBarT*HotBarT | -2.662 | 0.823 | -3.23 | 0.005 | 1.03 |
| DwelTime*DwelTime | -2.476 | 0.823 | -3.01 | 0.008 | 1.03 |
| HotBarP*HotBarP | -1.329 | 0.823 | -1.61 | 0.126 | 1.03 |
| MatTemp*MatTemp | -1.151 | 0.823 | -1.40 | 0.181 | 1.03 |
| HotBarT*DwelTime | -5.81 | 1.10 | -5.28 | 0.000 | 1.00 |
| HotBarT*HotBarP | -0.09 | 1.10 | -0.08 | 0.938 | 1.00 |
| HotBarT*MatTemp | -0.14 | 1.10 | -0.13 | 0.902 | 1.00 |
| DwelTime*HotBarP | 0.55 | 1.10 | 0.50 | 0.624 | 1.00 |
| DwelTime*MatTemp | 0.24 | 1.10 | 0.22 | 0.832 | 1.00 |
| HotBarP*MatTemp | -0.10 | 1.10 | -0.09 | 0.929 | 1.00 |

Model Summary
| S | R-sq | R-sq(adj) | R-sq(pred) |
|---|---|---|---|
| 4.40228 | 78.58% | 59.84% | 0.00% |

Analysis of Variance
| Source | DF | Adj SS | Adj MS | F-Value | P-Value |
|---|---|---|---|---|---|
| Model | 14 | 1137.51 | 81.251 | 4.19 | 0.004 |
| Linear | 4 | 218.65 | 54.662 | 2.82 | 0.060 |
| HotBarT | 1 | 68.13 | 68.129 | 3.52 | 0.079 |
| DwelTime | 1 | 70.94 | 70.939 | 3.66 | 0.074 |
| HotBarP | 1 | 52.62 | 52.616 | 2.71 | 0.119 |
| MatTemp | 1 | 26.96 | 26.963 | 1.39 | 0.255 |
| Square | 4 | 372.07 | 93.018 | 4.80 | 0.010 |
| HotBarT*HotBarT | 1 | 202.61 | 202.611 | 10.45 | 0.005 |
| DwelTime*DwelTime | 1 | 175.32 | 175.318 | 9.05 | 0.008 |
| HotBarP*HotBarP | 1 | 50.52 | 50.522 | 2.61 | 0.126 |
| MatTemp*MatTemp | 1 | 37.87 | 37.866 | 1.95 | 0.181 |
| 2-Way Interaction | 6 | 546.79 | 91.132 | 4.70 | 0.006 |
| HotBarT*DwelTime | 1 | 540.47 | 540.470 | 27.89 | 0.000 |
| HotBarT*HotBarP | 1 | 0.12 | 0.121 | 0.01 | 0.938 |
| HotBarT*MatTemp | 1 | 0.30 | 0.305 | 0.02 | 0.902 |
| DwelTime*HotBarP | 1 | 4.84 | 4.840 | 0.25 | 0.624 |
| DwelTime*MatTemp | 1 | 0.90 | 0.899 | 0.05 | 0.832 |
| HotBarP*MatTemp | 1 | 0.16 | 0.160 | 0.01 | 0.929 |
| Error | 16 | 310.08 | 19.380 | | |
| Lack-of-Fit | 10 | 308.20 | 30.820 | 98.51 | 0.000 |
| Pure Error | 6 | 1.88 | 0.313 | | |
| Total | 30 | 1447.60 | | | |

Regression Equation in Uncoded Units
```
Strength = -289.3 + 2.287 HotBarT + 206.6 DwelTime + 0.124 HotBarP + 0.594 MatTemp
           - 0.00426 HotBarT*HotBarT - 39.6 DwelTime*DwelTime - 0.000532 HotBarP*HotBarP
           - 0.00288 MatTemp*MatTemp - 0.930 HotBarT*DwelTime - 0.000070 HotBarT*HotBarP
           - 0.00028 HotBarT*MatTemp + 0.0440 DwelTime*HotBarP + 0.047 DwelTime*MatTemp
           - 0.00010 HotBarP*MatTemp
```

Fits and Diagnostics for Unusual Observations
| Obs | Strength | Fit | Resid | Std Resid | |
|---|---|---|---|---|---|
| 3 | 20.69 | 14.43 | 6.26 | 2.20 | R |
| 5 | 27.43 | 21.72 | 5.71 | 2.01 | R |
| 9 | 25.99 | 20.16 | 5.83 | 2.05 | R |
| 19 | 21.38 | 15.10 | 6.28 | 2.21 | R |

R  Large residual

해석 원문 요지: HotBarT*HotBarT, DwelTime*DwelTime, HotBarT*DwelTime 유의. R² 78.58%, R²(pred) 0 → 과적합 → 모형 축소 권장. Pareto 에서 가장 큰 효과 AB(HotBarT*DwelTime), 가장 작은 효과 AC(HotBarT*HotBarP). 정규확률도 점들이 직선에서 벗어남.

### 3.9 문서 내 추가 ANOVA 예제 (interp_ab6d6d41.txt) — 숫자 그대로 (2수준 요인형 데이터, 그룹 라벨 `2-Way Interactions` 표기 예)
Analysis of Variance (full)
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

Analysis of Variance (reduced)
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

(이 표들에는 Lack-of-Fit/Pure Error 분리 없음 — 반복이 없거나 조건 미충족 사례.)

### 3.10 해석 단계 요약 (interp_ce5a0525.txt)
Step 1 Pareto(기본 α 0.05 기준선) → Step 2 p-값 → Step 3 Model Summary(S, R-sq, R-sq(adj), R-sq(pred), AICc/BIC) → Step 4 잔차도(Residuals vs fits 패턴 표: Fanning → Nonconstant variance, Curvilinear → missing higher-order term, far from zero → outlier, far in x → influential; Normal plot: Not straight → Nonnormality, far from line → outlier, changing slope → unidentified variable; vs order: Trend/Shift/Cycle).

### 3.11 ko-kr 매핑 — Analyze RS (ko-kr analyze-response-surface-design__before-you-start__example.txt)
| 영문 | 한국어판 |
|---|---|
| Stat > DOE > Response Surface > Analyze Response Surface Design | 통계분석 > 실험계획법 > 반응 표면 설계 > 반응 표면 설계 분석 |
| Responses | 반응 |
| Graphs / Residual Plots / Four in one | 그래프 / 잔차 그림 / 네 개 모두 |
| Coded Coefficients | 코드화된 계수 |
| Term / Coef / SE Coef / T-Value / P-Value / VIF | 항 / 계수 / SE 계수 / T-값 / P-값 / VIF |
| Constant | 상수 |
| Model Summary | 모형 요약 |
| S / R-sq / R-sq(adj) / R-sq(pred) | S / R-제곱 / R-제곱(수정) / R-제곱(예측) |
| Analysis of Variance | 분산 분석 |
| Source / DF / Adj SS / Adj MS / F-Value / P-Value | 출처 / DF / Adj SS / Adj MS / F-값 / P-값 |
| Model / Linear / Square / 2-Way Interaction | 모형 / 선형 / 제곱 / 2차 교호작용 |
| Error / Lack-of-Fit / Pure Error / Total | 오차 / 적합성 결여 / 순수 오차 / 총계 |
| Regression Equation in Uncoded Units | 코드화되지 않은 단위의 회귀 방정식 |
| Fits and Diagnostics for Unusual Observations | 비정상적 관측치에 대한 적합치 및 진단 |
| Obs / Fit / Resid / Std Resid | 관측 / 적합치 / 잔차 / 표준화 잔차 |
| R  Large residual | R  큰 잔차 |
| Model reduction | 모형 축소 |
| (예제 요인명) HotBarT / DwelTime / HotBarP / MatTemp | 열 봉의 온도 / 정지 시간 / 열 봉의 압력 / 재료 온도 (ko 판은 요인명도 번역; 해석 문단에는 영문명 그대로 남아 있음) |

---

## 4. Create Mixture Design

메뉴: `Stat > DOE > Mixture > Create Mixture Design` (create-mixture-design__before-you-start__overview.txt)

### 4.1 개요·실험 유형 (overview.txt, what-is-a-mixture-design.txt)
- 세 가지 설계 유형: **simplex centroid**, **simplex lattice**, **extreme vertices**. 공정 변수(process variables) 또는 양 변수(amount variable)를 포함 가능.
- 세 가지 실험 유형(분석 관점): `Mixture`(성분 비율에만 의존) / `Mixture-process variable`(성분 + 공정 변수) / `Mixture-amount`(성분 비율 + 혼합물 총량).
- 워크시트에 이미 성분 열이 있으면 `Define Custom Mixture Design` 사용.

### 4.2 메인 대화상자 (speci_68f765bc.txt)
| 필드 | 내용 |
|---|---|
| Type of Design | `Simplex centroid` / `Simplex lattice` / `Extreme vertices` |
| Number of components | 성분 수 선택 |
| `Display Available Designs` 버튼 | simplex centroid·simplex lattice 의 런 수를 설계 유형·격자 차수·성분 수별로 표시. 입력 없음. **표 자체는 문서에 없음** (display-available-designs.txt) |
| `Designs` 버튼 | 설계 생성 전에 반드시 클릭해야 함 ("Before Minitab creates the design, you must click Designs") |
| `Components` / `Process Vars` / `Options` / `Results` 버튼 | §4.3~§4.7 |
- 선택 지침(원문 요지): simplex lattice 는 격자 차수 선택 가능, simplex centroid 보다 복잡한 모형 적합 가능. 성분에 선형 제약을 두려면 extreme vertices.

### 4.3 Designs 하위 대화상자 — 유형별
공통 경로: `Stat > DOE > Mixture > Create Mixture Design > Designs`

**(a) Simplex Centroid** (speci_ce09c108.txt)
- **Augment the design with axial points**: 성분당 축점 1개를 기본 설계에 추가. 축점 = 중앙점과 꼭지점의 평균 블렌드.
- **Replicate Design Points**:
  - `Number of replicates for the whole design`
  - `Number of replicates for the selected types of points`: 점 유형별 반복 수를 `Point Type` 열 값 기준으로 `Number` 열에 입력. 유형: `vertex`(한 성분이 상한, 나머지 하한), `blends`(두 개 이상 성분이 하한이 아님; double blend, triple blend ...), `center point`(모든 성분 비율 동일; 기본 설계에 1개), `axial point`(중앙점과 꼭지점 비율의 평균; 기본 설계에서 축점 수 = 꼭지점 수; 축점 증강을 선택했을 때만 반복이 런을 추가).
  - Note: "For simplex lattice designs and extreme vertices designs, replication of blend points adds experimental runs only if the degree of the design includes the blend in the base design."
- (Degree 선택·center point 증강 옵션 없음 — centroid 는 중심점을 기본 포함.)

**(b) Simplex Lattice** (speci_2d093a0b.txt)
- **Degree of lattice**: 차수가 높을수록 복잡한 모형 적합 가능. 원문 표(4성분 기준):

| Degree | Number of blends |
|---|---|
| 1 | Contains only vertex points. |
| 2 | Contains double blends where the components are mixed equally. |
| 3 | Two double blends for each pair of components and triple blends that are mixed equally. |
| 4 | Three double blends for each pair of components and two triple blends for each trio of components. |

- **Augment the design with center point**
- **Augment the design with axial points**
- **Replicate Design Points**: (a) 와 동일.

**(c) Extreme Vertices** (speci_8b3a7cb5.txt)
- **Degree of design**: (b) 와 같은 표.
- **Augment the design with center point** / **Augment the design with axial points**
- **Replicate Design Points**: 점 유형 정의가 약간 다름 — `vertex`: 각 성분이 경계나 제약 중 하나에 있는 점. 선형 제약이 없는 기본 설계에서는 꼭지점 수 = 성분 수. `blends`: 두 개 이상 꼭지점이 정의하는 모서리/면 위의 점(성분 비율 중 적어도 하나가 0). `center point`: 설계 공간 중앙(기본 1개). `axial point`: 중앙점과 꼭지점 비율의 평균, 0 인 성분 없음.

### 4.4 Components 하위 대화상자 (specify-the-components.txt)
경로: `... > Create Mixture Design > Components`
- **Total Mixture Amount**
  - `Single total`: 양수 입력. 비율이면 합 = 1. **기본값 1**.
  - `Multiple totals (up to 5)`: 최대 5개 양수 → mixture-amounts 실험.
- **Component Bounds Specified in Amount (lower and upper are for the first total, if you specified more than one)**: 열 `Name`, `Lower`, `Upper`.
- Extreme vertices 에서는 `Linear Constraints` 버튼으로 선형 제약 지정.

### 4.5 Linear Constraints (speci_87473e65.txt)
경로: `... > Components > Linear Constraints`
- Extreme vertices 설계에서 **최대 10개**의 선형 제약.
- 입력: `Lower`, 성분별 계수 행(`A, B, C, ...` — 성분마다 한 행), `Upper`. 하나 이상의 성분에 계수, Lower 및/또는 Upper 값 지정.
- 원문 예(4성분):

| Condition | Lower | Coefficient A | Coefficient B | Coefficient C | Coefficient D | Upper |
|---|---|---|---|---|---|---|
| A + B > 10 and A + B < 20 | 10 | 1 | 1 | | | 20 |
| 5A + 3B + 8D < 0.1 | | 5 | 3 | | 8 | 0.1 |
| 0.5B + 0.8D > 0.9 | 0.9 | | 0.5 | 0.8 | | |

- 예: 젖은 재료(eggs, milk, oil) 합이 40%~60% → lower 0.4, upper 0.6, 계수 모두 1.

### 4.6 Process Vars 하위 대화상자 (speci_42d3ea87.txt)
경로: `... > Create Mixture Design > Process Vars`
- 최대 **7개의 2수준 공정 변수**. 공정 변수의 full 또는 fractional factorial 조합마다 혼합물 설계가 생성됨.
- **Process Variables**: `None` / `Number`(개수 선택 → 표의 해당 행 활성화)
- **Type of design**: full / fractional factorial (가용 설계는 변수 수에 따라 다름)
- **Fraction number**: fractional 선택 시 fraction 선택. 기본은 principal fraction.
- 표 열: `Name`(기본 X1, ..., Xn), `Type`(numeric / text), `Low`(기본 −1), `High`(기본 +1).

### 4.7 Options (speci_72977d66.txt)
- **Randomize runs** (+ `Base for random data generator`), **Store design in worksheet** — RS 와 동일. 저장 후 Display Design / Modify Design 사용.

### 4.8 Results 하위 대화상자
- 예제에서 `Detailed description and design table` 선택 (3개 예제 공통). 다른 선택지는 문서에 없음.

### 4.9 가용 설계 범위 (methods design-information.txt, choose-a-mixture-design.txt)
- **Simplex centroid**: q 성분이면 **2^q − 1** 점. 점: 한 성분 = 1(꼭지점), 두 성분 = 1/2, 세 성분 = 1/3, ... 모든 성분 = 1/q(중심/centroid).
- **Simplex lattice**: 차수 m 은 1~10. 생성 가능 조합(원문 표 그대로):

| Lattice of degree (m) | Number of components (q) |
|---|---|
| 1 | 2 to 20 |
| 2 | 2 to 20 |
| 3 | 2 to 17 |
| 4 | 2 to 11 |
| 5 | 2 to 8 |
| 6 | 2 to 7 |
| 7 | 2 to 6 |
| 8 | 2 to 5 |
| 9 | 2 to 5 |
| 10 | 2 to 5 |

- **Extreme vertices**: XVERT 알고리즘으로 제약 공간의 극꼭지점 생성 후 Piepel 의 CONAEV 알고리즘으로 지정 차수까지의 중심점(centroids) 계산. 참고문헌 Cornell (1990), St. John (1984).
- "Display available designs" 표(런 수 매트릭스)는 **문서에 없음**.

### 4.10 설계 선택 가이드 표 (choose-a-mixture-design.txt, what-is-the-degree-of-a-lattice.txt) — 원문 그대로
| | Unaugmented | Augmented |
|---|---|---|
| Simplex Centroid | You can fit up to a special cubic model. | You can partially fit up to a special cubic model. |
| Simplex Lattice Degree 1 | You can fit a linear model. | You can partially fit up to a quadratic model. |
| Simplex Lattice Degree 2 | You can fit up to a quadratic model. | You can partially fit up to a special cubic model. |
| Simplex Lattice Degree 3 | You can fit up to a full cubic model. | You can fit up to a full cubic model. |

Note(원문 요지): 혼합물 실험은 처음 계획보다 높은 차수 모형이 필요한 경우가 잦으므로 가능하면 최소 요구보다 많은 런을 수행.

### 4.11 증강(augment) 규칙 (how-minitab-augments-designs.txt)
- 기본적으로 내부점을 추가하여 증강: **축점과 (기본 설계에 없으면) 중앙점** 추가. 추가되는 점은 모두 완전 혼합(complete mixture).
- 각 축점은 꼭지점과 설계 중심의 **중간(halfway)**.
- 주 용도: lack-of-fit 검토, 내부 반응 표면 정보.
- 끄려면 Designs 에서 `Augment the design with a center point` / `Augment the design with axial points` 해제.
- 공정 변수나 반복이 있으면 최종 설계의 중앙점 수가 늘어남 (speci_2d093a0b.txt).

### 4.12 단위 변환 — 원문 그대로 (methods design-information.txt, scales-for-representing-the-data.txt, what-is-a-pseudo-component.txt)
```
Proportion = Amount / Total
If the total = 1, then the proportion units = amount units.
Pseudo = (proportion - low) / (1 - sum of the lower bounds)
Proportion = pseudo * (1 - sum of the lower bounds) + lower bound
If all lower bounds = 0, then pseudo units = proportion units
```
척도 동치 표:
| Total Mixture | Lower bounds | Equivalent scales |
|---|---|---|
| equal to 1 | 0 | amounts proportions pseudo-components |
| equal to 1 | greater than 0 | amounts proportions |
| not equal to 1 | 0 | proportions pseudo-components |
| not equal to 1 | greater than 0 | none |

Pseudo-component 예(총량 50 ml, X1 하한 20 → X2 상한 30):
| Amounts X1 | X2 | Proportions X1 | X2 | Pseudo-components X1 | X2 |
|---|---|---|---|---|---|
| 50 | 0 | 1.0 | 0.0 | 1.0 | 0.0 |
| 20 | 30 | 0.4 | 0.6 | 0.0 | 1.0 |
| 35 | 15 | 0.7 | 0.3 | 0.5 | 0.5 |

### 4.13 생성 출력 형식 (all-statistics.txt + 예제 3개)
출력 항목 순서:
1. **Design Summary**: `Components:`, `Design points:`, `Process variables:`, `Design degree:` (simplex lattice 는 `Lattice degree:`)
2. `Mixture total: <값>` 한 줄 (예: `Mixture total: 1.00000`)
3. **Number of Boundaries for Each Dimension**: 행 `Point Type | Dimension | Number`, 열은 점 유형 1(차원 0, 꼭지점), 2(차원 1, 모서리), 0(차원 2, 평면) ... 
4. **Number of Design Points for Each Type**: 열 `Point Type | 1 | 2 | 3 | 0 | -1`, 행 `Distinct`, `Replicates`, `Total number`
5. **Bounds of Mixture Components**: 상단 헤더 `Amount | Proportion | Pseudocomponent`, 2단 헤더 `Comp | Lower | Upper | Lower | Upper | Lower | Upper`
6. **Linear Constraints of Mixture Components** (extreme vertices 에 제약이 있을 때): `Constraint | Lower | A | B | C | Upper`
7. **Design Table (randomized)**: `Run | Type | A | B | C | X1 ...` (+ 총량이 여러 개면 `Amount` 열)
   - 성분 문자는 알파벳 순, **T 는 건너뜀**("skipping the letter T"). 공정 변수는 X1, ..., Xn, 코드화 −1/1.
   - 각 행 합이 1 이면 비율(proportions), 아니면 양(amounts)으로 표시.
- Design degree 의미: simplex centroid → 어느 차원까지의 centroid 포함; simplex lattice → 각 경계에서 점 생성 방식; extreme vertices → 어느 차원까지 centroid 포함(1: 꼭지점만, 2: + 모서리 중심, 3: + 면 중심).
- 워크시트 열 (overview.txt 표): `StdOrder | RunOrder | PtType | Blocks | <성분1> | <성분2> | <성분3>` (C1~C7). 예:

| C1 StdOrder | C2 RunOrder | C3 PtType | C4 Blocks | C5 Neroli | C6 Rose | C7 Tangerine |
|---|---|---|---|---|---|---|
| 10 | 1 | -1 | 1 | 0.16667 | 0.16667 | 0.66667 |
| 5 | 2 | 2 | 1 | 0.50000 | 0.00000 | 0.50000 |
| 3 | 3 | 1 | 1 | 0.00000 | 0.00000 | 1.00000 |
| 7 | 4 | 0 | 1 | 0.33333 | 0.33333 | 0.33333 |
| 6 | 5 | 2 | 1 | 0.00000 | 0.50000 | 0.50000 |
| 4 | 6 | 2 | 1 | 0.50000 | 0.50000 | 0,00000 (원문 오타: 쉼표) |
| 8 | 7 | -1 | 1 | 0.66667 | 0.16667 | 0.16667 |

### 4.14 PtType 코드 의미 (all-statistics.txt, what-points-can-i-use-in-a-designed-experiment.txt)
- **비제약(unconstrained) 설계**(모든 성분 0~1): 점 유형 값 = 블렌드에 포함된 성분 수. 예외 두 가지: `0` = 중앙점(모든 성분 동일 비율), `-1` = 축점(중앙점과 꼭지점의 정확히 중간인 완전 혼합).
- **제약(constrained) 설계**: `1` = 꼭지점(vertex), `2` = 모서리 중간점(두 꼭지점 비율 평균), `0` = 중앙점(꼭지점 비율들의 평균), `-1` = 축점(중앙점 비율과 꼭지점 비율의 평균).
- 설계 유형 공통 점 유형 표(원문):

| Point | Screening Designs | Factorial Designs | Response Surface Designs | Mixture Designs |
|---|---|---|---|---|
| 0 | center point | center point | center point | centroid |
| 1 | corner point | corner point (cube point) | cube point (corner point) | vertex |
| -1 | - | - | axial point | axial point |
| 2 | edge midpoint* | - | edge midpoint** | edge midpoint (double blend) |
| 3 | - | - | - | triple blend*** |

\* definitive screening designs 만. \*\* Box-Behnken 만. \*\*\* 혼합물에서는 고차 블렌드일수록 점 유형 값이 자연히 증가.

### 4.15 예제 1 — Simplex Centroid, 3성분 10런 (exampl_c6d183f1.txt) — 숫자 그대로
단계: Type of Design = Simplex centroid → Number of components = 3 → Designs → OK → Components: Name A~C = Neroli, Rose, Tangerine → Results: Detailed description and design table.

Design Summary
| | | | |
|---|---|---|---|
| Components: | 3 | Design points: | 10 |
| Process variables: | 0 | Design degree: | 3 |

Mixture total: 1.00000

Number of Boundaries for Each Dimension
| Point Type | 1 | 2 | 0 |
|---|---|---|---|
| Dimension | 0 | 1 | 2 |
| Number | 3 | 3 | 1 |

Number of Design Points for Each Type
| Point Type | 1 | 2 | 3 | 0 | -1 |
|---|---|---|---|---|---|
| Distinct | 3 | 3 | 0 | 1 | 3 |
| Replicates | 1 | 1 | 0 | 1 | 1 |
| Total number | 3 | 3 | 0 | 1 | 3 |

Bounds of Mixture Components
| Comp | Amount Lower | Amount Upper | Proportion Lower | Proportion Upper | Pseudocomponent Lower | Pseudocomponent Upper |
|---|---|---|---|---|---|---|
| A | 0.0000 | 1.0000 | 0.0000 | 1.0000 | 0.0000 | 1.0000 |
| B | 0.0000 | 1.0000 | 0.0000 | 1.0000 | 0.0000 | 1.0000 |
| C | 0.0000 | 1.0000 | 0.0000 | 1.0000 | 0.0000 | 1.0000 |

Design Table (randomized)
| Run | Type | A | B | C |
|---|---|---|---|---|
| 1 | 1 | 0.0000 | 0.0000 | 1.0000 |
| 2 | 2 | 0.0000 | 0.5000 | 0.5000 |
| 3 | 0 | 0.3333 | 0.3333 | 0.3333 |
| 4 | 2 | 0.5000 | 0.0000 | 0.5000 |
| 5 | 1 | 1.0000 | 0.0000 | 0.0000 |
| 6 | 2 | 0.5000 | 0.5000 | 0.0000 |
| 7 | -1 | 0.1667 | 0.1667 | 0.6667 |
| 8 | -1 | 0.1667 | 0.6667 | 0.1667 |
| 9 | -1 | 0.6667 | 0.1667 | 0.1667 |
| 10 | 1 | 0.0000 | 1.0000 | 0.0000 |

(해석: 7개 경계 = 0차원 꼭지점 3 + 1차원 모서리 3 + 2차원 평면 1. 중앙점 1, 축점 3. 2^3 − 1 = 7 기본점 + 축점 3 = 10.)

### 4.16 예제 2 — Simplex Lattice, 3성분 degree 1, 7런 (exampl_851cd3a7.txt) — 숫자 그대로
단계: Type of Design = Simplex lattice → Number of components = 3 → Designs → OK(기본 degree 1, 증강 기본 ON) → Components 이름 Neroli, Rose, Tangerine → Results: Detailed description and design table.

Design Summary
| | | | |
|---|---|---|---|
| Components: | 3 | Design points: | 7 |
| Process variables: | 0 | Lattice degree: | 1 |

Mixture total: 1.00000

Number of Boundaries for Each Dimension
| Point Type | 1 | 2 | 0 |
|---|---|---|---|
| Dimension | 0 | 1 | 2 |
| Number | 3 | 3 | 1 |

Number of Design Points for Each Type
| Point Type | 1 | 2 | 3 | 0 | -1 |
|---|---|---|---|---|---|
| Distinct | 3 | 0 | 0 | 1 | 3 |
| Replicates | 1 | 0 | 0 | 1 | 1 |
| Total number | 3 | 0 | 0 | 1 | 3 |

Bounds of Mixture Components: 예제 1 과 동일(모두 0.0000 / 1.0000).

Design Table (randomized)
| Run | Type | A | B | C |
|---|---|---|---|---|
| 1 | 1 | 0.0000 | 1.0000 | 0.0000 |
| 2 | -1 | 0.6667 | 0.1667 | 0.1667 |
| 3 | -1 | 0.1667 | 0.6667 | 0.1667 |
| 4 | 0 | 0.3333 | 0.3333 | 0.3333 |
| 5 | 1 | 1.0000 | 0.0000 | 0.0000 |
| 6 | 1 | 0.0000 | 0.0000 | 1.0000 |
| 7 | -1 | 0.1667 | 0.1667 | 0.6667 |

(degree 1 격자 = 꼭지점 3 + 증강 중앙점 1 + 축점 3 = 7. Summary 라벨이 `Lattice degree:` 임에 유의.)

### 4.17 예제 3 — Extreme Vertices, 3성분 + 공정변수 1, 18런 (exampl_71baccdd.txt, all-statistics.txt) — 숫자 그대로
단계: Type of Design = Extreme vertices → Number of components = 3 → Designs → OK → Components 표:

| Component | Name | Lower | Upper |
|---|---|---|---|
| A | Emmenthaler | 0.2 | 0.6 |
| B | Gruyere | 0 | 0.3 |
| C | Broth | 0.4 | 0.6 |

→ Linear Constraints 표(열 1개 입력): Lower = 0, A = 1, B = −1, C = 0, Upper = (빈칸) → OK 두 번 → Process Vars: `Number` = 1, Name = Temperature, Low = 80, High = 90 → Results: Detailed description and design table.

Design Summary
| | | | |
|---|---|---|---|
| Components: | 3 | Design points: | 18 |
| Process variables: | 1 | Design degree: | 1 |

Mixture total: 1.00000

Number of Boundaries for Each Dimension
| Point Type | 1 | 2 | 0 |
|---|---|---|---|
| Dimension | 0 | 1 | 2 |
| Number | 5 | 5 | 1 |

Number of Design Points for Each Type
| Point Type | 1 | 2 | 3 | 0 | -1 |
|---|---|---|---|---|---|
| Distinct | 8 | 0 | 0 | 2 | 8 |
| Replicates | 1 | 0 | 0 | 1 | 1 |
| Total number | 8 | 0 | 0 | 2 | 8 |

Bounds of Mixture Components
| Comp | Amount Lower | Amount Upper | Proportion Lower | Proportion Upper | Pseudocomponent Lower | Pseudocomponent Upper |
|---|---|---|---|---|---|---|
| A | 0.20000 | 0.60000 | 0.20000 | 0.60000 | 0.00000 | 1.00000 |
| B | 0.00000 | 0.30000 | 0.00000 | 0.30000 | 0.00000 | 0.75000 |
| C | 0.40000 | 0.60000 | 0.40000 | 0.60000 | 0.00000 | 0.50000 |

Linear Constraints of Mixture Components
| Constraint | Lower | A | B | C | Upper |
|---|---|---|---|---|---|
| 1 | 0.00000 | 1.00000 | -1.00000 | 0.00000 | |

Design Table (randomized)
| Run | Type | A | B | C | X1 |
|---|---|---|---|---|---|
| 1 | 1 | 0.20000 | 0.20000 | 0.60000 | -1 |
| 2 | 1 | 0.20000 | 0.20000 | 0.60000 | 1 |
| 3 | 0 | 0.37500 | 0.12500 | 0.50000 | 1 |
| 4 | 1 | 0.30000 | 0.30000 | 0.40000 | 1 |
| 5 | 1 | 0.40000 | 0.00000 | 0.60000 | -1 |
| 6 | -1 | 0.33750 | 0.21250 | 0.45000 | -1 |
| 7 | -1 | 0.28750 | 0.16250 | 0.55000 | 1 |
| 8 | -1 | 0.38750 | 0.06250 | 0.55000 | 1 |
| 9 | -1 | 0.48750 | 0.06250 | 0.45000 | 1 |
| 10 | 1 | 0.30000 | 0.30000 | 0.40000 | -1 |
| 11 | -1 | 0.33750 | 0.21250 | 0.45000 | 1 |
| 12 | -1 | 0.28750 | 0.16250 | 0.55000 | -1 |
| 13 | -1 | 0.48750 | 0.06250 | 0.45000 | -1 |
| 14 | 1 | 0.40000 | 0.00000 | 0.60000 | 1 |
| 15 | 0 | 0.37500 | 0.12500 | 0.50000 | -1 |
| 16 | 1 | 0.60000 | 0.00000 | 0.40000 | 1 |
| 17 | -1 | 0.38750 | 0.06250 | 0.55000 | -1 |
| 18 | 1 | 0.60000 | 0.00000 | 0.40000 | -1 |

해석(원문 요지):
- 제약 설계. 꼭지점 8(공정변수 수준당 4), 모서리점 0, 중앙점 2(수준당 1), 축점 8(수준당 4). 각 점 유형 반복 1 → Total = Distinct.
- Pseudocomponent 상한 검산: 하한 합 = 0.2 + 0 + 0.4 = 0.6 → B 상한 (0.3 − 0)/(1 − 0.6) = 0.75, C 상한 (0.6 − 0.4)/0.4 = 0.5, A 상한 (0.6 − 0.2)/0.4 = 1.0 (§4.12 공식과 일치).
- 선형 제약 1·A − 1·B ≥ 0 → "Gruyere 양이 Emmenthaler 양을 초과하지 않음".
- 첫 런: A 0.20000, B 0.20000, C 0.60000, X1 = −1(80도).
- 유의: 꼭지점 4개 중 (0.2, 0.2, 0.6) 과 (0.3, 0.3, 0.4) 는 제약 A − B ≥ 0 의 경계(A = B)에 놓인 꼭지점.

### 4.18 Simplex Design Plot (simplex-design-plot__before-you-start__example.txt)
- 메뉴 `Stat > DOE > Mixture > Simplex Design Plot`.
- 대화상자: **Components**: `Select a triplet of components for a single plot` → `X-Axis` / `Y-Axis` / `Z-Axis` 성분 선택(예: Emmenthaler / Gruyere / Broth). 체크 `Plot all level combinations`(공정 변수 수준 조합마다 그림).
- 해석: 삼각 좌표에 설계점 표시. 회색 영역 = 제약 설계 공간(그림이 설계 공간 밖으로 확장될 수 있음). 18점 = 온도 수준 2 × 9점(꼭지점 4, 중앙점 1, 축점 4; 축점은 중앙점과 꼭지점의 정확히 중간).

### 4.19 ko-kr 매핑 — Create Mixture (ko-kr exampl_71baccdd / 851cd3a7 / c6d183f1 / overview / perform-a-mixtures-experiment / what-is-a-mixture-design)
| 영문 | 한국어판 |
|---|---|
| Stat > DOE > Mixture > Create Mixture Design | 통계분석 > 실험계획법 > 혼합 > 혼합물 설계 생성 (perform-a-mixtures-experiment ko 는 "혼합물 설계 > 혼합물 설계 생성") |
| Type of Design | 설계 유형 |
| Simplex centroid / Simplex lattice / Extreme vertices | 심플렉스 중심 / 심플렉스 격자 / 꼭지점 |
| Number of components | 성분 수 |
| Designs / Components / Process Vars / Options / Results | 설계 / 성분 / 공정 변수 / (문서에 없음) / 결과 |
| Linear Constraints | 선형 제약 조건 |
| Component / Name / Lower / Upper | 성분 / 이름 / 하한 / 상한 |
| Process Variables: Number | 공정 변수: 개수 |
| Low / High | 낮음 / 많음 (ko 원문 그대로; "높음" 이 아님에 유의) |
| Detailed description and design table | 자세한 설명 및 설계 표 |
| Design Summary | 설계 요약 |
| Components: / Process variables: / Design points: / Design degree: / Lattice degree: | 성분: / 공정 변수: / 설계점: / 설계 차수: / 격자도: |
| Mixture total | 혼합물 총량 |
| Number of Boundaries for Each Dimension | 각 차원에서의 경계 수 |
| Point Type / Dimension / Number | 점 유형 / 차원 / 횟수 |
| Number of Design Points for Each Type | 각 유형에서의 설계점 수 |
| Distinct / Replicates / Total number | 구별되는 점 / 반복실험 / 전체 수 |
| Bounds of Mixture Components | 혼합물 성분의 한계 |
| Amount / Proportion / Pseudocomponent | 양 / 비율 / 유사 성분 |
| Comp | 성분 |
| Linear Constraints of Mixture Components | 혼합물 성분의 선형 제약 조건 |
| Constraint | 제약 조건 |
| Design Table (randomized) | 설계 표(랜덤화) |
| Run / Type | 실행 / 유형 (혼합물 설계표에서는 "실행"; RS 설계표에서는 "런") |
| StdOrder / RunOrder / PtType / Blocks | 표준 순서 / 런 순서 / 점 유형 / 블럭 |
| vertex / edge / plane / center point / axial point | 꼭지점 / 가장자리 / 평면 / 중앙점 / 축 점 |
| constrained / unconstrained design | 제약된 설계 / 제약이 없는 설계 |
| complete blend | 완전 혼합 |
| Simplex Design Plot | 심플렉스 설계도 |
| Define Custom Mixture Design | 사용자 혼합물 설계 정의 |
| Modify Design / Display Design | 설계 수정 / 설계 표시 |
| Response Trace Plot / Contour Plot / Surface Plot / Overlaid Contour Plot / Response Optimizer | 반응 궤적도 / 등고선도 / 표면도 / 중첩 등고선도 / 반응 최적화 도구 |
| Mixture / Mixture-process variable / Mixture-amount | 혼합물 설계 / 혼합물-공정 변수 / 혼합물-양 |
| (예제 성분명) Emmenthaler / Gruyere / Broth; Neroli / Rose / Tangerine | 에멘탈 / 그뤼에르 / 수프(생성 예제) 또는 국물(분석 예제); 등화유 / 장미 기름 / 탕헤르 오렌지 기름 |

---

## 5. Analyze Mixture Design

메뉴: `Stat > DOE > Mixture > Analyze Mixture Design` (analyze-mixture-design__before-you-start__example.txt)

### 5.1 메인 대화상자 (예제 단계에서 확인된 필드)
| 필드 | 문서에서 확인된 값 |
|---|---|
| Responses | 반응 열(예: Flavor) |
| Type of Model | 예제 선택값 `Mixture components and process variables`. 나머지 라디오의 정확한 라벨 문자열은 **문서에 없음**(실험 유형은 Mixture / Mixture-process variables / Mixture-amounts 세 가지 — methods design-information.txt) |
| Analyze Components in | 예제 선택값 `Proportions`. 분석 단위는 amount / proportion / pseudocomponent 세 가지(methods design-information.txt). 나머지 라디오 라벨 문자열은 문서에 없음 |
| Model Fitting Method | 예제 선택값 `Mixture regression`. stepwise 절차가 메인 대화상자에서 선택 가능하며 그 경우 Terms 의 항은 후보가 되고 `Options` 버튼에서 선택 기준 수정 (s_accbba58.txt). stepwise 라디오의 정확한 라벨은 문서에 없음 |
| 버튼 | `Terms`, `Graphs`, `Options`(stepwise 기준; 내용 페이지는 담당 파일에 없음), `Results` |

### 5.2 Terms 하위 대화상자 (s_accbba58.txt)
경로: `Stat > DOE > Mixture > Analyze Mixture Design > Terms`
- **Include component terms for model**: 성분 모형 차수 선택 → Selected Terms 갱신.
- **Include inverse component terms**: 어느 성분도 하한이 0 이 아니고(원문: "when no components have a lower bound of zero") 비율 단위로 분석할 때만 가능. 성분 비율이 하한에 접근할 때의 극단적 반응 변화 모형화(레모네이드 감미료 예). 역항 표기: 1/A, 1/B, 1/C ... (design-information.txt)
- **Include process variable terms up through order** 또는 **Include mixture amount terms up through order**: 설계에 공정 변수가 있는지 양 변수가 있는지에 따라 라벨이 바뀜. 차수 선택.
- **Available Terms** / **Selected Terms** + 화살표/더블클릭.
- **Include blocks in the model**: 블록 열 값이 여러 개면 활성화.
- 예제 Selected Terms: `Emmenthaler, Gruyere, Broth, AB, BC, A*X1, B*X1, C*X1` (성분 교호작용은 `AB` 식 약어, 성분×공정변수는 `A*X1` 식 표기).

### 5.3 모형 유형·항 표 — 원문 그대로 (design-information.txt, models-terms-and-blending.txt)
| Model | Terms |
|---|---|
| Linear | A B C |
| Quadratic | Linear + AB AC BC |
| Special cubic | Quadratic+ ABC |
| Full cubic | Special cubic + AB(A-B) AC(A-C) BC(B-C) |
| Special quartic | Quadratic + AABC ABBC ABCC |
| Full quartic | Special quartic + AB(A-B) AC(A-C) BC(B-C) AB(A-B)2 AC(A-C)2 BC(B-C)2 |

"Note that there is no constant term in mixture models. Inverse terms include 1/A, 1/B, 1/C, etc."

| Model type | Terms | Type of blending |
|---|---|---|
| linear (first-order) | linear | additive |
| quadratic (second-order) | linear and quadratic | additive nonlinear synergistic binary or additive nonlinear antagonistic binary |
| special cubic (third-order) | linear, quadratic, and special cubic | additive nonlinear synergistic binary nonlinear antagonistic binary |
| full cubic (third-order) | linear, quadratic, special cubic, and full cubic | additive nonlinear synergistic binary nonlinear antagonistic binary nonlinear synergistic ternary nonlinear antagonistic ternary |
| special quartic (fourth-order) | linear, quadratic, special cubic, full cubic, and special quartic | additive ... nonlinear synergistic quaternary nonlinear antagonistic quaternary |
| full quartic (fourth-order) | linear, quadratic, special cubic, full cubic, special quartic, and full quartic | (위와 동일 목록) |

- 상수항 없는 모형 예(원문): `Y = b1A + b2B + b3C + b12AB + b13AC + b23BC`
- 역항 조건(models-terms-and-blending.txt 표현): "if the lower bound for any component is not zero and you choose to analyze the design in proportions" — Terms 페이지 표현("no components have a lower bound of zero")과 뉘앙스가 다름. 두 문장이 모두 문서에 있음(구현 시 확인 필요).

### 5.4 Graphs (s_a746071a.txt)
- Residuals for Plots: `Regular` / `Standardized` / `Deleted`
- Residual Plots: Individual plots(`Histogram`, `Normal plot`, `Residuals versus fits`, `Residuals versus order` — x축은 **행 번호**(RS 는 런 순서)), `Four in one`
- Residuals versus variables
- (Effects plots 항목 없음 — RS 와 차이)

### 5.5 Results (s_ca087a3f.txt)
- `Do not display`
- `Model selection, coefficients, and ANOVA table` (model selection steps, 계수표, S, R-sq, R-sq(adj), ANOVA)
- `Unusual observations in addition to the above`
- `Full table of fits and residuals in addition to the above`

### 5.6 출력표 형식 (example.txt, interpret 39cd75cc / 20706399)
1. 제목 `Estimated Regression Coefficients for <Response> (component proportions)` — 괄호 안은 분석 단위.
   - 열 `Term | Coef | SE Coef | T-Value | P-Value | VIF`.
   - **상수항(Constant) 행 없음**. 성분 선형항은 `T-Value`, `P-Value` 가 `*` 로 표시(성분 종속성 때문에 p-값 미표시). 공정 변수 계수는 코드화 값 기준.
   - 표 아래 한 줄: `Coefficients are calculated for coded process variables.`
   - VIF 가이드 동일(1 / 1~5 / >5). 제약 혼합물 설계에서는 VIF 가 커지는 경향.
2. **Model Summary**: `S | R-sq | R-sq(adj) | PRESS | R-sq(pred)` — **PRESS 포함**이 기본 표시(RS 와 차이).
3. 제목 `Analysis of Variance for <Response> (component proportions)`:
   - 열 `Source | DF | Seq SS | Adj SS | Adj MS | F-Value | P-Value` — **Seq SS 와 Adj SS 모두 표시**.
   - Source 행 구조(예제): `Regression` → `Component Only`(그룹 제목 행, 값 없음) → `Linear` → `Quadratic` → 각 성분 교호작용 항 → `Component * <공정변수명>`(그룹 제목 행, 값 없음; 예 `Component * Temperature`) → `Linear` → 각 성분×공정변수 항 → `Residual Error` → (`Lack-of-Fit`, `Pure Error` — 반복이 있으면; 예제에는 없음) → `Total`.
   - interpret 문서의 항목명: "P-value – Regression", "Seq SS Residual Error", "Seq SS Pure Error", "F-value for the lack-of-fit test". 그룹 F 예: linear effects, quadratic effects.
   - 선형 그룹의 Seq SS 와 Adj SS 가 다름(예: 3557.10 vs 741.33) — 성분 선형항은 절편 역할을 겸하므로 순차 SS 가 매우 큼.
4. Unusual observations / Full table of fits and residuals (Results 선택 시) — 형식은 문서에 없음.

### 5.7 Methods and formulas — 원문 텍스트 그대로 (coefficients.txt, analysis-of-variance.txt, g_27150a5f.txt)
**Coefficient**: "Minitab uses least squares estimation to calculate the coefficients. In matrix terms, the least squares estimates of the coefficients are:"
```
b = (X'X)-1X'y
```
Notation: X = design matrix, y = response column. 고차 모형 계수는 Cornell (1990) 참조.

**SE Coef**: 단순회귀 식(이미지). 다중회귀: "The standard errors of the coefficients for multiple regression are the square roots of the diagonal elements of this matrix:" (이미지; Notation 에 s² = mean square error, X, X').

**T-value**: 이미지(Notation: 검정통계량 = 추정 계수 / 계수 표준오차).

**P-value – Coefficients table**: "The two-sided p-value for the null hypothesis that a regression coefficient equals 0 is:" (이미지). 자유도 = 오차 자유도 `n – p`. Notation: tj = j번째 계수의 t 통계량, n = 관측 수, p = 항들의 자유도 합.

**VIF**: "For predictor xj, the VIF is:" (이미지). Notation: R2(xj) = xj 를 반응으로 하고 나머지 항을 예측변수로 한 결정계수. (즉 1/(1 − R²(xj)) 형태로 추정되나 본문에 식 텍스트는 없음.)

**Sum of squares**: 행렬식 이미지. Notation: b, X, Y, n, J(n×n 1 행렬). "Minitab breaks down the SS Regression or SS Treatments component into the amount of variation explained by each term using both the sequential sum of squares and adjusted sum of squares."

**Adjusted SS**: RS 와 동일한 SSR(X3 | X1, X2) 식 텍스트(§3.7).

**DF** 원문:
```
DF Regression = p - 1
DF Error      = n - p
Total         = n - 1
where n = number of observations and p = number of terms in the model.
```
(예제 검산: 항 8개 → Regression 7, Error 18 − 8 = 10, Total 17 ✓.)

**Adj MS – Regression / Error**: 이미지. **F**: F(Term), F(Lack-of-fit) 이미지; 랜덤 요인이 있으면 기대평균제곱 사용. **P-value**: `1 − P(F ≤ fj)`, 분자 DF = 항 DF 합, 분모 DF = 오차 DF.

**Goodness-of-fit**: S, R-sq, R-sq(adj)(음수→0), R-sq(pred)(음수→0), PRESS — 모두 이미지. Notation 에 hi = X(X'X)–1X' 의 i번째 대각 원소, ei = i번째 잔차.

### 5.8 예제 — FondueRecipe, 반응 Flavor (example.txt) — 숫자 그대로
단계: Open FondueRecipe.MWX → Responses = Flavor → Type of Model = Mixture components and process variables → Analyze Components in = Proportions → Model Fitting Method = Mixture regression → Terms: Emmenthaler, Gruyere, Broth, AB, BC, A*X1, B*X1, C*X1 → Graphs: Four in one.

Estimated Regression Coefficients for Flavor (component proportions)
| Term | Coef | SE Coef | T-Value | P-Value | VIF |
|---|---|---|---|---|---|
| Emmenthaler | 104.874 | 0.667 | * | * | 15.94 |
| Gruyere | 175.08 | 5.89 | * | * | 203.46 |
| Broth | -8.810 | 0.659 | * | * | 26.04 |
| Emmenthaler*Gruyere | 59.2 | 10.3 | 5.75 | 0.000 | 57.33 |
| Gruyere*Broth | 30.04 | 9.00 | 3.34 | 0.008 | 109.44 |
| Emmenthaler*Temperature | 4.500 | 0.475 | 9.48 | 0.000 | 8.09 |
| Gruyere*Temperature | 4.500 | 0.679 | 6.62 | 0.000 | 2.71 |
| Broth*Temperature | 4.500 | 0.443 | 10.16 | 0.000 | 11.76 |

Coefficients are calculated for coded process variables.

Model Summary
| S | R-sq | R-sq(adj) | PRESS | R-sq(pred) |
|---|---|---|---|---|
| 0.276960 | 99.98% | 99.97% | 2.65322 | 99.93% |

Analysis of Variance for Flavor (component proportions)
| Source | DF | Seq SS | Adj SS | Adj MS | F-Value | P-Value |
|---|---|---|---|---|---|---|
| Regression | 7 | 3924.18 | 3924.18 | 560.597 | 7308.30 | 0.000 |
| Component Only | | | | | | |
| Linear | 2 | 3557.10 | 741.33 | 370.664 | 4832.22 | 0.000 |
| Quadratic | 2 | 2.58 | 2.58 | 1.289 | 16.80 | 0.001 |
| Emmenthaler*Gruyere | 1 | 1.72 | 2.53 | 2.532 | 33.01 | 0.000 |
| Gruyere*Broth | 1 | 0.85 | 0.85 | 0.855 | 11.14 | 0.008 |
| Component * Temperature | | | | | | |
| Linear | 3 | 364.50 | 364.50 | 121.500 | 1583.95 | 0.000 |
| Emmenthaler*Temperature | 1 | 335.51 | 6.89 | 6.887 | 89.79 | 0.000 |
| Gruyere*Temperature | 1 | 21.07 | 3.37 | 3.365 | 43.87 | 0.000 |
| Broth*Temperature | 1 | 7.92 | 7.92 | 7.924 | 103.30 | 0.000 |
| Residual Error | 10 | 0.77 | 0.77 | 0.077 | | |
| Total | 17 | 3924.94 | | | | |

해석 원문 요지: 교호작용 p < 0.05 유의. 성분 2개 교호작용 계수 양수 → 상승(synergistic) 작용. 성분×Temperature 교호작용 → 맛 점수가 온도에 따라 달라짐. R² 99.98%.
(참고: 성분 선형항 DF 가 3 이 아니라 2 인 것은 성분 합 제약으로 절편 역할 1 자유도가 흡수되기 때문 — 문서에 명시 설명은 없고 DF Regression = p − 1 규칙과 일치.)

### 5.9 Response Trace Plot (response-trace-plot__before-you-start__example.txt)
- 메뉴 `Stat > DOE > Mixture > Response Trace Plot`. 저장된 모형 필요(예제 파일 FondueRecipe_model.MWX).
- 대화상자 필드(문서에서 확인): **Response**(Flavor), **Trace Direction**: `Cox (proportion)` 선택 — 다른 선택지(Piepel 등)의 라벨 문자열은 **문서에 없음**; **Model Fitted in**: `Proportions`; **Reference Blend**: `Centroid of vertices`(다른 선택지는 문서에 없음).
- 해석: 공정 변수 온도는 80 도로 고정. 기준 블렌드에서 출발하여 각 성분 비율을 증감시킬 때 반응 변화를 추적 — Emmenthaler↑ → Flavor↑; Gruyere↑ → 더 급하게 ↑; Broth↑ → ↓. 결론: Emmenthaler·Gruyere 비율 증가, Broth 감소 권장.

### 5.10 기타 Mixture 메뉴 (각 한 줄 문서)
- **Contour/Surface Plots** (contour-surface-plots.txt): 저장 모형 + 두 연속 변수. Using fitted models 영역 참조.
- **Overlaid Contour Plot** (overlaid-contour-plot.txt): 여러 반응의 허용 영역 시각화.
- **Response Optimizer** (response-optimizer.txt): 단일/다중 반응 최적 설정과 interactive optimization plot.
- **Factorial Plots** (factorial-plots.txt): main effects plot, interaction plot. **Cube Plot** 은 2수준 요인 설계 또는 **혼합물 설계**에서 사용 가능: 큐브당 3요인, 2요인이면 square plot, 최대 8요인, 중앙점은 5요인 이하에서만 표시. 혼합물에서는 (요인 설정 조합 + 데이터 평균) 또는 (조합만) 표시.
- **Display and Modify Design** (mixtures__display-and-modify-design.txt): factorial 영역 참조. Modify Design 작업 목록(perform-a-mixtures-experiment.txt): 성분 이름 변경, 반복, 랜덤화, 번호 재지정, 공정 변수 이름 변경, 공정 변수 수준 값 변경. Display Design: 런 표시 순서, 성분/공정 변수 표시 단위 변경.
- **Select Optimal Design** (mixtures__select-optimal-design.txt): §6 참조.

### 5.11 ko-kr 매핑 — Analyze Mixture (ko-kr analyze-mixture-design__before-you-start__example.txt)
| 영문 | 한국어판 |
|---|---|
| Stat > DOE > Mixture > Analyze Mixture Design | 통계분석 > 실험계획법 > 혼합 > 혼합물 설계 분석 |
| Responses | 반응 |
| Type of Model | 모형 유형 |
| Mixture components and process variables | 혼합물 성분 및 공정 변수 |
| Analyze Components in | 성분 분석 |
| Proportions | 비율 |
| Model Fitting Method | 모형 적합 방법 |
| Mixture regression | 혼합물 회귀 |
| Terms / Selected Terms | 항 / 선택 항 |
| Estimated Regression Coefficients for Flavor (component proportions) | 맛(성분 비율)에 대한 추정된 회귀 계수 |
| Coefficients are calculated for coded process variables. | 코드화된 공정 변수에 대한 계수가 계산됩니다. |
| Model Summary / PRESS | 모형 요약 / PRESS |
| Analysis of Variance for Flavor (component proportions) | 맛에 대한 분산 분석(성분 비율) |
| Regression | 회귀 분석 |
| Component Only | 성분만 |
| Linear / Quadratic | 선형 / 2차 |
| Component * Temperature | 성분 * 온도 |
| Residual Error / Total | 잔차 오차 / 총계 |
| Seq SS / Adj SS / Adj MS | Seq SS / Adj SS / Adj MS (번역 안 함) |
| synergistic | 상승 작용 |
| (예제 성분·변수명) Emmenthaler / Gruyere / Broth / Temperature | 에멘탈 / 그뤼에르 / 국물 / 온도 |

---

## 6. Select Optimal Design

메뉴(문서에서 확인된 경로): `Stat > DOE > Response Surface > Select Optimal Design` (examp_a837a12e.txt 등). Factorial·Mixture 영역에도 동일 명령이 있고 상세는 factorial 영역 문서를 가리킴 (response-surface__select-optimal-design.txt, mixtures__select-optimal-design.txt: "select, add, exchange, or evaluate runs from a candidate set of experimental runs").

### 6.1 최적화 기준 (optimality-criteria.txt, methods-and-formulas.txt)
- **D-optimality**: "minimizes the determinant of the variance-covariance matrix of the regression coefficients." 모형을 지정하면 후보점 집합에서 D-최적 기준을 만족하는 설계점 선택. 워크시트의 설계 열 행들이 후보점 집합.
- **Distance-based optimality**: 설계 공간에 점을 균일하게 분포. 모형을 미리 정할 수 없거나 원치 않을 때 사용. **General full factorial 설계에서는 사용 불가**. 교환(exchange) 방법을 쓰지 않으며 점을 반복(replicate)하지 않음.
- `what-is-an-optimal-design.txt` 는 소스 폴더에 **파일 없음**.

### 6.2 작업(Task) — 문서에서 확인된 UI 문자열
| 작업 | 문서 상 조작 |
|---|---|
| 선택(select) | `In Number of points in optimal design, type 20.` → Terms → OK (examp_a837a12e.txt). 작업 라디오의 정확한 라벨은 문서에 없음(기본 작업으로 추정하지 않음) |
| 증강/개선 | `Under Task, choose Augment/improve design, then enter 'Keep runs with −1' in the box.` + `Number of points in optimal design` = 25 (examp_acb2f2eb.txt) |
| 평가 | `Choose Evaluate design, then enter OptPoint in the box.` → Terms 에서 `Linear` 선택 (examp_61fbc6b2.txt) |
- **지시자 열(indicator column) 의미** (examp_acb2f2eb.txt, methods): 선택 결과로 원본 워크시트에 `OptPoint` 열 생성 — 1 = 최적 설계에 포함, 0 = 미포함(더 일반적으로는 "whether or not a point was selected and the number of replicates of that design point"). 증강 시 **음수 지시자**(예 −1)는 보호(제외 불가)할 점, 0 은 추가 후보. 예제에서는 `Calc > Calculator` 로 `−1 * 'OptPoint'` 를 `Keep runs with −1` 열에 저장.
- Terms 하위 대화상자: `Include the following terms` 드롭다운(기본 full quadratic; `Linear` 선택 가능). 블록이 있으면 `Block` 항 포함.

### 6.3 방법(Methods 하위 대화상자) (methods-and-formulas.txt, examp_a837a12e.txt)
D-optimal 선택은 두 단계:
1. **초기 설계 생성**: `sequential selection`(기본; 각 점을 D-optimality 최대 증가 순으로 추가, 후보 순서가 같으면 같은 해), `random selection`, 또는 두 방식의 조합("including some randomly selected runs").
2. **개선(improvement)**:
   - `Exchange method`: 후보에서 가장 좋은 점들을 먼저 추가한 뒤 가장 나쁜 점들을 제거, D-optimality 가 더 개선되지 않을 때까지. **교환할 점 수** 지정 가능(기본 1).
   - `Fedorov's method`: 한 점 추가 + 한 점 제거의 쌍을 동시에 교환하여 최대 개선. 개선 불가 시까지.
   - `None` / `Suppress improvement of the initial design`: 최종 = 초기.
- 증강 시 초기 설계: 워크시트의 모든 점 사용, 또는 지시자 열로 점과 반복 수 지정. 추가 점은 순차적으로 "best" 점 추가.
- 후보점은 **복원 추출**로 추가될 수 있어 최종 설계에 중복점 가능.
- Tip: 국소 최적 회피를 위해 다른 초기 설계에서 여러 번 시도(multiple trials). 순수 순차 선택 또는 지시자 열 지정 시에는 1회만 가능. (시도 횟수 필드명은 문서에 없음.)
- 최고 D-optimality 설계에 대해: 원본 워크시트에 `OptPoint` 지시자 열 생성, 선택점을 **새 워크시트**로 복사.
- 선택 결과는 후보점의 **행 순서에 의존**(같은 후보 집합도 순서가 다르면 다른 D-최적 설계 가능).
- **Distance-based**: 시작점 = 원점에서 유클리드 거리가 가장 큰 후보(반응 표면) 또는 순수 성분에 가장 가까운 점(혼합물). 이후 이미 선택된 점들로부터 가장 먼 점을 단계적으로 추가. 증강 시 지시자 열 필수.

### 6.4 출력 형식
- 제목 줄: `Response surface design selected according to D-optimality` / `Response surface design augmented according to D-optimality` / `Evaluation of Specified Response Surface Design`
- `Number of candidate design points: 30`
- `Number of design points to augment/improve: 20` (증강 시)
- `Number of design points in optimal design: 20`
- `Model terms: Block, A, B, C, D, AA, BB, CC, DD, AB, AC, AD, BC, BD, CD`
- `Initial design generated by Sequential method` / `Initial design augmented by Sequential method`
- `Initial design improved by Exchange method`
- `Number of design points exchanged is 1`
- 소제목 `Optimal Design` / `Specified Design`
- `Row number of selected design points: ...` (선택된 순서대로의 원본 워크시트 행 번호)
- 통계 표(행 라벨 원문 그대로):
  - `Condition number:`
  - `D-optimality (determinant of XTX):`
  - `A-optimality (trace of inv(XTX)):`
  - `G-optimality (avg leverage/max leverage):`
  - `V-optimality (average leverage):`
  - `Maximum leverage:`
- 비교 지침: D-optimality 는 클수록, A-optimality 는 작을수록 좋음. 최적성은 고정 설계 크기·특정 모형에 대해서만 정의됨.
- 공식: 위 괄호 설명(determinant of XᵀX, trace of (XᵀX)⁻¹, average leverage / max leverage, average leverage) 외의 수식은 **문서에 없음**. Condition number 산식도 문서에 없음.

### 6.5 예제 1 — D-optimal 선택, 후보 30 → 20점 (examp_a837a12e.txt) — 숫자 그대로
데이터 CrystalGrowth_optimal_design.MWX(4요인 2블록 CCD, 30런). 단계: `Number of points in optimal design` = 20 → Terms → OK.
```
Response surface design selected according to D-optimality
Number of candidate design points: 30
Number of design points in optimal design: 20
Model terms: Block, A, B, C, D, AA, BB, CC, DD, AB, AC, AD, BC, BD, CD
Initial design generated by Sequential method
Initial design improved by Exchange method
Number of design points exchanged is 1
Optimal Design
Row number of selected design points: 22, 23, 25, 27, 4, 8, 19, 2, 14, 15, 13, 6, 9, 3, 16,
     24, 28, 30, 26, 1
```
| | |
|---|---|
| Condition number: | 10.2292 |
| D-optimality (determinant of XTX): | 2.73819E+18 |
| A-optimality (trace of inv(XTX)): | 2.50391 |
| G-optimality (avg leverage/max leverage): | 0.8 |
| V-optimality (average leverage): | 0.8 |
| Maximum leverage: | 1 |

### 6.6 예제 2 — 증강 20 → 25점 (examp_acb2f2eb.txt) — 숫자 그대로
워크시트 C1~C9: `StdOrder | RunOrder | PtType | Blocks | A | B | C | D | OptPoint` (예: 행1 `12 | 1 | 1 | 1 | 8.25 | 55 | 0.75 | 6.5 | 1`, 행2 `11 | 2 | 1 | 1 | 6.75 | 55 | 0.75 | 6.5 | 0`). C10 `Keep runs with −1` = −1 × OptPoint. 단계: Task = `Augment/improve design`, 열 = 'Keep runs with −1', `Number of points in optimal design` = 25.
```
Response surface design augmented according to D-optimality
Number of candidate design points: 30
Number of design points to augment/improve: 20
Number of design points in optimal design: 25
Model terms: Block, A, B, C, D, AA, BB, CC, DD, AB, AC, AD, BC, BD, CD
Initial design augmented by Sequential method
Initial design improved by Exchange method
Number of design points exchanged is 1
Optimal Design
Row number of selected design points: 1, 3, 4, 6, 8, 9, 10, 13, 15, 16, 17, 19, 22, 23, 24,
     25, 26, 27, 28, 30, 2, 5, 14, 18, 20
```
| | |
|---|---|
| Condition number: | 8.53018 |
| D-optimality (determinant of XTX): | 3.73547E+20 |
| A-optimality (trace of inv(XTX)): | 1.99479 |
| G-optimality (avg leverage/max leverage): | 0.64 |
| V-optimality (average leverage): | 0.64 |
| Maximum leverage: | 1 |

(보호된 20점이 먼저 나열되고 추가 5점 2, 5, 14, 18, 20 이 뒤에 붙음.)

### 6.7 예제 3 — 평가, Linear 모형 (examp_61fbc6b2.txt) — 숫자 그대로
단계: `Evaluate design`, 열 = OptPoint → Terms: `Linear`.
```
Evaluation of Specified Response Surface Design
Number of design points in optimal design: 20
Model terms: Block, A, B, C, D
Specified Design
Row number of selected design points: 1, 3, 4, 6, 8, 9, 10, 13, 15, 16, 17, 19, 22, 23, 24,
     25, 26, 27, 28, 30
```
| | |
|---|---|
| Condition number: | 1.43109 |
| D-optimality (determinant of XTX): | 47267840 |
| A-optimality (trace of inv(XTX)): | 0.320581 |
| G-optimality (avg leverage/max leverage): | 0.871492 |
| V-optimality (average leverage): | 0.3 |
| Maximum leverage: | 0.344237 |

(검산: V-optimality = 평균 레버리지 = p/n = 6/20 = 0.3 (Block + A~D + 상수 = 6개 열). 예제 1 은 p = 16, n = 20 → 0.8; 예제 2 는 16/25 = 0.64 — 모두 일치. 이는 분석가 검산이며 문서 설명은 아님.)

### 6.8 ko-kr 매핑 — Optimal: 해당 ko-kr 파일 없음.

---

## 7. Taguchi (참고용)

### 7.1 Create Taguchi Design — 대화상자·예제 (create-taguchi-design__before-you-start__example_2dc12631.txt, display-available-designs.txt)
- 메뉴 `Stat > DOE > Taguchi > Create Taguchi Design`.
- 필드: **Type of Design**(예: `2-Level Design`), **Number of factors**(예: 4), `Designs` 버튼(예: `Select the L8 design`), `Display Available Designs`(입력 없음; 탭을 넘겨 모든 가용 설계 확인; 표기 예 "an L4 design has 4 runs. 2^3 means 3 factors at 2 levels").
- 기본 수준 값: 1, 2 (실제 설정값 입력 가능).
- 출력(예제, 숫자 그대로):

Design Summary
| | |
|---|---|
| Taguchi Array | L8(2^4) |
| Factors: | 4 |
| Runs: | 8 |

`Columns of L8(2^7) array: 1 2 4 7`

| C1 A | C2 B | C3 C | C4 D |
|---|---|---|---|
| 1 | 1 | 1 | 1 |
| 1 | 1 | 2 | 2 |
| 1 | 2 | 1 | 2 |
| 1 | 2 | 2 | 1 |
| 2 | 1 | 1 | 2 |
| 2 | 1 | 2 | 1 |
| 2 | 2 | 1 | 1 |
| 2 | 2 | 2 | 2 |

(즉 4요인 L8 은 L8(2^7) 직교배열의 1, 2, 4, 7 열을 사용.)

### 7.2 Catalogue of Taguchi designs — 숫자 그대로 (catalogue-of-taguchi-designs.txt)
- 표기: `L(runs) (levels ^ factors)`. 혼합 수준 예: L18 (2^1 3^7) = 18런, 2수준 요인 1개, 3수준 요인 7개.
- 모든 배열의 열은 균형·직교(각 열 쌍에서 모든 수준 조합이 같은 횟수로 등장).
- 목록(원문 순서): L4 (2^3), L8 (2^7), L8 (2^4),(4^1), L9 (3^4), L12 (2^11), L16 (2^15), L16 (2^12),(4^1), L16 (2^9),(4^2), L16 (2^6),(4^3), L16 (2^3),(4^4), L16 (4^5), L16 (8^1),(2^8), L18 (2^1),(3^7), L18 (6^1),(3^6), L25 (5^6), L27 (3^13), L32 (2^31), L32 (2^1),(4^9), L36 (2^11),(3^12), L36 (2^3),(3^13), L54 (2^1),(3^25)
- 아래 표에서 첫 열은 런 번호, 나머지 열 머리글은 배열의 열 번호.

**L4 (2^3)**
| | 1 | 2 | 3 |
|---|---|---|---|
| 1 | 1 | 1 | 1 |
| 2 | 1 | 2 | 2 |
| 3 | 2 | 1 | 2 |
| 4 | 2 | 2 | 1 |

**L8 (2^7)**
| | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|---|
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 2 | 1 | 1 | 1 | 2 | 2 | 2 | 2 |
| 3 | 1 | 2 | 2 | 1 | 1 | 2 | 2 |
| 4 | 1 | 2 | 2 | 2 | 2 | 1 | 1 |
| 5 | 2 | 1 | 2 | 1 | 2 | 1 | 2 |
| 6 | 2 | 1 | 2 | 2 | 1 | 2 | 1 |
| 7 | 2 | 2 | 1 | 1 | 2 | 2 | 1 |
| 8 | 2 | 2 | 1 | 2 | 1 | 1 | 2 |

**L8 (2^4), (4^1)**
| | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| 1 | 1 | 1 | 1 | 1 | 1 |
| 2 | 1 | 2 | 2 | 2 | 2 |
| 3 | 2 | 1 | 1 | 2 | 2 |
| 4 | 2 | 2 | 2 | 1 | 1 |
| 5 | 3 | 1 | 2 | 1 | 2 |
| 6 | 3 | 2 | 1 | 2 | 1 |
| 7 | 4 | 1 | 2 | 2 | 1 |
| 8 | 4 | 2 | 1 | 1 | 2 |

**L9 (3^4)**
| | 1 | 2 | 3 | 4 |
|---|---|---|---|---|
| 1 | 1 | 1 | 1 | 1 |
| 2 | 1 | 2 | 2 | 2 |
| 3 | 1 | 3 | 3 | 3 |
| 4 | 2 | 1 | 2 | 3 |
| 5 | 2 | 2 | 3 | 1 |
| 6 | 2 | 3 | 1 | 2 |
| 7 | 3 | 1 | 3 | 2 |
| 8 | 3 | 2 | 1 | 3 |
| 9 | 3 | 3 | 2 | 1 |

**L12 (2^11)**
| | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 2 | 1 | 1 | 1 | 1 | 1 | 2 | 2 | 2 | 2 | 2 | 2 |
| 3 | 1 | 1 | 2 | 2 | 2 | 1 | 1 | 1 | 2 | 2 | 2 |
| 4 | 1 | 2 | 1 | 2 | 2 | 1 | 2 | 2 | 1 | 1 | 2 |
| 5 | 1 | 2 | 2 | 1 | 2 | 2 | 1 | 2 | 1 | 2 | 1 |
| 6 | 1 | 2 | 2 | 2 | 1 | 2 | 2 | 1 | 2 | 1 | 1 |
| 7 | 2 | 1 | 2 | 2 | 1 | 1 | 2 | 2 | 1 | 2 | 1 |
| 8 | 2 | 1 | 2 | 1 | 2 | 2 | 2 | 1 | 1 | 1 | 2 |
| 9 | 2 | 1 | 1 | 2 | 2 | 2 | 1 | 2 | 2 | 1 | 1 |
| 10 | 2 | 2 | 2 | 1 | 1 | 1 | 1 | 2 | 2 | 1 | 2 |
| 11 | 2 | 2 | 1 | 2 | 1 | 2 | 1 | 1 | 1 | 2 | 2 |
| 12 | 2 | 2 | 1 | 1 | 2 | 1 | 2 | 1 | 2 | 2 | 1 |

**L16 (2^15)**
| | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 2 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 |
| 3 | 1 | 1 | 1 | 2 | 2 | 2 | 2 | 1 | 1 | 1 | 1 | 2 | 2 | 2 | 2 |
| 4 | 1 | 1 | 1 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 1 | 1 | 1 | 1 |
| 5 | 1 | 2 | 2 | 1 | 1 | 2 | 2 | 1 | 1 | 2 | 2 | 1 | 1 | 2 | 2 |
| 6 | 1 | 2 | 2 | 1 | 1 | 2 | 2 | 2 | 2 | 1 | 1 | 2 | 2 | 1 | 1 |
| 7 | 1 | 2 | 2 | 2 | 2 | 1 | 1 | 1 | 1 | 2 | 2 | 2 | 2 | 1 | 1 |
| 8 | 1 | 2 | 2 | 2 | 2 | 1 | 1 | 2 | 2 | 1 | 1 | 1 | 1 | 2 | 2 |
| 9 | 2 | 1 | 2 | 1 | 2 | 1 | 2 | 1 | 2 | 1 | 2 | 1 | 2 | 1 | 2 |
| 10 | 2 | 1 | 2 | 1 | 2 | 1 | 2 | 2 | 1 | 2 | 1 | 2 | 1 | 2 | 1 |
| 11 | 2 | 1 | 2 | 2 | 1 | 2 | 1 | 1 | 2 | 1 | 2 | 2 | 1 | 2 | 1 |
| 12 | 2 | 1 | 2 | 2 | 1 | 2 | 1 | 2 | 1 | 2 | 1 | 1 | 2 | 1 | 2 |
| 13 | 2 | 2 | 1 | 1 | 2 | 2 | 1 | 1 | 2 | 2 | 1 | 1 | 2 | 1 | 2 |
| 14 | 2 | 2 | 1 | 1 | 2 | 2 | 1 | 2 | 1 | 1 | 2 | 2 | 1 | 1 | 2 |
| 15 | 2 | 2 | 1 | 2 | 1 | 1 | 2 | 1 | 2 | 2 | 1 | 2 | 1 | 1 | 2 |
| 16 | 2 | 2 | 1 | 2 | 1 | 1 | 2 | 2 | 1 | 1 | 2 | 1 | 2 | 2 | 1 |

**L16 (2^12), (4^1)**
| | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 2 | 1 | 1 | 1 | 1 | 1 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 |
| 3 | 1 | 2 | 2 | 2 | 2 | 1 | 1 | 1 | 1 | 2 | 2 | 2 | 2 |
| 4 | 1 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 1 | 1 | 1 | 1 |
| 5 | 2 | 1 | 1 | 2 | 2 | 1 | 1 | 2 | 2 | 1 | 1 | 2 | 2 |
| 6 | 2 | 1 | 1 | 2 | 2 | 2 | 2 | 1 | 1 | 2 | 2 | 1 | 1 |
| 7 | 2 | 2 | 2 | 1 | 1 | 1 | 1 | 2 | 2 | 2 | 2 | 1 | 1 |
| 8 | 2 | 2 | 2 | 1 | 1 | 2 | 2 | 1 | 1 | 1 | 1 | 2 | 2 |
| 9 | 3 | 1 | 2 | 1 | 2 | 1 | 2 | 1 | 2 | 1 | 2 | 1 | 2 |
| 10 | 3 | 1 | 2 | 1 | 2 | 2 | 1 | 2 | 1 | 2 | 1 | 2 | 1 |
| 11 | 3 | 2 | 1 | 2 | 1 | 1 | 2 | 1 | 2 | 2 | 1 | 2 | 1 |
| 12 | 3 | 2 | 1 | 2 | 1 | 2 | 1 | 2 | 1 | 1 | 2 | 1 | 2 |
| 13 | 4 | 1 | 2 | 2 | 1 | 1 | 2 | 2 | 1 | 1 | 2 | 2 | 1 |
| 14 | 4 | 1 | 2 | 2 | 1 | 2 | 1 | 1 | 2 | 2 | 1 | 1 | 2 |
| 15 | 4 | 2 | 1 | 1 | 2 | 1 | 2 | 2 | 1 | 2 | 1 | 1 | 2 |
| 16 | 4 | 2 | 1 | 1 | 2 | 2 | 1 | 1 | 2 | 1 | 2 | 2 | 1 |

**L16 (2^9), (4^2)**
| | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 2 | 1 | 2 | 1 | 1 | 1 | 2 | 2 | 2 | 2 | 2 | 2 |
| 3 | 1 | 3 | 2 | 2 | 2 | 1 | 1 | 1 | 2 | 2 | 2 |
| 4 | 1 | 4 | 2 | 2 | 2 | 2 | 2 | 2 | 1 | 1 | 1 |
| 5 | 2 | 1 | 1 | 2 | 2 | 1 | 2 | 2 | 1 | 2 | 2 |
| 6 | 2 | 2 | 1 | 2 | 2 | 2 | 1 | 1 | 2 | 1 | 1 |
| 7 | 2 | 3 | 2 | 1 | 1 | 1 | 2 | 2 | 2 | 1 | 1 |
| 8 | 2 | 4 | 2 | 1 | 1 | 2 | 1 | 1 | 1 | 2 | 2 |
| 9 | 3 | 1 | 2 | 1 | 2 | 2 | 1 | 2 | 2 | 1 | 2 |
| 10 | 3 | 2 | 2 | 1 | 2 | 1 | 2 | 1 | 1 | 2 | 1 |
| 11 | 3 | 3 | 1 | 2 | 1 | 2 | 1 | 2 | 1 | 2 | 1 |
| 12 | 3 | 4 | 1 | 2 | 1 | 1 | 2 | 1 | 2 | 1 | 2 |
| 13 | 4 | 1 | 2 | 2 | 1 | 2 | 2 | 1 | 2 | 2 | 1 |
| 14 | 4 | 2 | 2 | 2 | 1 | 1 | 1 | 2 | 1 | 1 | 2 |
| 15 | 4 | 3 | 1 | 1 | 2 | 2 | 2 | 1 | 1 | 1 | 2 |
| 16 | 4 | 4 | 1 | 1 | 2 | 1 | 1 | 2 | 2 | 2 | 1 |

**L16 (2^6), (4^3)**
| | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 2 | 1 | 2 | 2 | 1 | 1 | 2 | 2 | 2 | 2 |
| 3 | 1 | 3 | 3 | 2 | 2 | 1 | 1 | 2 | 2 |
| 4 | 1 | 4 | 4 | 2 | 2 | 2 | 2 | 1 | 1 |
| 5 | 2 | 1 | 2 | 2 | 2 | 1 | 2 | 1 | 2 |
| 6 | 2 | 2 | 1 | 2 | 2 | 2 | 1 | 2 | 1 |
| 7 | 2 | 3 | 4 | 1 | 1 | 1 | 2 | 2 | 1 |
| 8 | 2 | 4 | 3 | 1 | 1 | 2 | 1 | 1 | 2 |
| 9 | 3 | 1 | 3 | 1 | 2 | 2 | 2 | 2 | 1 |
| 10 | 3 | 2 | 4 | 1 | 2 | 1 | 1 | 1 | 2 |
| 11 | 3 | 3 | 1 | 2 | 1 | 2 | 2 | 1 | 2 |
| 12 | 3 | 4 | 2 | 2 | 1 | 1 | 1 | 2 | 1 |
| 13 | 4 | 1 | 4 | 2 | 1 | 2 | 1 | 2 | 2 |
| 14 | 4 | 2 | 3 | 2 | 1 | 1 | 2 | 1 | 1 |
| 15 | 4 | 3 | 2 | 1 | 2 | 2 | 1 | 1 | 1 |
| 16 | 4 | 4 | 1 | 1 | 2 | 1 | 2 | 2 | 2 |

**L16 (2^3), (4^4)**
| | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|---|
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 2 | 1 | 2 | 2 | 1 | 2 | 2 | 2 |
| 3 | 1 | 3 | 3 | 2 | 3 | 1 | 2 |
| 4 | 1 | 4 | 4 | 2 | 4 | 2 | 1 |
| 5 | 2 | 1 | 2 | 2 | 1 | 2 | 1 |
| 6 | 2 | 2 | 1 | 2 | 2 | 1 | 2 |
| 7 | 2 | 3 | 4 | 1 | 3 | 2 | 2 |
| 8 | 2 | 4 | 3 | 1 | 4 | 1 | 1 |
| 9 | 3 | 1 | 3 | 1 | 4 | 2 | 2 |
| 10 | 3 | 2 | 4 | 1 | 3 | 1 | 1 |
| 11 | 3 | 3 | 1 | 2 | 2 | 2 | 1 |
| 12 | 3 | 4 | 2 | 2 | 1 | 1 | 2 |
| 13 | 4 | 1 | 4 | 2 | 2 | 1 | 2 |
| 14 | 4 | 2 | 3 | 2 | 1 | 2 | 1 |
| 15 | 4 | 3 | 2 | 1 | 4 | 1 | 1 |
| 16 | 4 | 4 | 1 | 1 | 3 | 2 | 2 |

**L16 (4^5)**
| | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| 1 | 1 | 1 | 1 | 1 | 1 |
| 2 | 1 | 2 | 2 | 2 | 2 |
| 3 | 1 | 3 | 3 | 3 | 3 |
| 4 | 1 | 4 | 4 | 4 | 4 |
| 5 | 2 | 1 | 2 | 3 | 4 |
| 6 | 2 | 2 | 1 | 4 | 3 |
| 7 | 2 | 3 | 4 | 1 | 2 |
| 8 | 2 | 4 | 3 | 2 | 1 |
| 9 | 3 | 1 | 3 | 4 | 2 |
| 10 | 3 | 2 | 4 | 3 | 1 |
| 11 | 3 | 3 | 1 | 2 | 4 |
| 12 | 3 | 4 | 2 | 1 | 3 |
| 13 | 4 | 1 | 4 | 2 | 3 |
| 14 | 4 | 2 | 3 | 1 | 4 |
| 15 | 4 | 3 | 2 | 4 | 1 |
| 16 | 4 | 4 | 1 | 3 | 2 |

**L16 (8^1), (2^8)**
| | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 2 | 1 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 |
| 3 | 2 | 1 | 1 | 1 | 1 | 2 | 2 | 2 | 2 |
| 4 | 2 | 2 | 2 | 2 | 2 | 1 | 1 | 1 | 1 |
| 5 | 3 | 1 | 1 | 2 | 2 | 1 | 1 | 2 | 2 |
| 6 | 3 | 2 | 2 | 1 | 1 | 2 | 2 | 1 | 1 |
| 7 | 4 | 1 | 1 | 2 | 2 | 2 | 2 | 1 | 1 |
| 8 | 4 | 2 | 2 | 1 | 1 | 1 | 1 | 2 | 2 |
| 9 | 5 | 1 | 2 | 1 | 2 | 1 | 2 | 1 | 2 |
| 10 | 5 | 2 | 1 | 2 | 1 | 2 | 1 | 2 | 1 |
| 11 | 6 | 1 | 2 | 1 | 2 | 2 | 1 | 2 | 1 |
| 12 | 6 | 2 | 1 | 2 | 1 | 1 | 2 | 1 | 2 |
| 13 | 7 | 1 | 2 | 2 | 1 | 1 | 2 | 2 | 1 |
| 14 | 7 | 2 | 1 | 1 | 2 | 2 | 1 | 1 | 2 |
| 15 | 8 | 1 | 2 | 2 | 1 | 2 | 1 | 1 | 2 |
| 16 | 8 | 2 | 1 | 1 | 2 | 1 | 2 | 2 | 1 |

**L18 (2^1), (3^7)** — 원문 열 머리글이 `1 2 3 4 5 6 7 9` (8 이 아니라 9 로 표기됨; 원문 그대로)
| | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 9 |
|---|---|---|---|---|---|---|---|---|
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 2 | 1 | 1 | 2 | 2 | 2 | 2 | 2 | 2 |
| 3 | 1 | 1 | 3 | 3 | 3 | 3 | 3 | 3 |
| 4 | 1 | 2 | 1 | 1 | 2 | 2 | 3 | 2 |
| 5 | 1 | 2 | 2 | 2 | 3 | 3 | 1 | 3 |
| 6 | 1 | 2 | 3 | 3 | 1 | 1 | 2 | 1 |
| 7 | 1 | 3 | 1 | 2 | 1 | 3 | 2 | 3 |
| 8 | 1 | 3 | 2 | 3 | 2 | 1 | 3 | 1 |
| 9 | 1 | 3 | 3 | 1 | 3 | 2 | 1 | 2 |
| 10 | 2 | 1 | 1 | 3 | 3 | 2 | 2 | 1 |
| 11 | 2 | 1 | 2 | 1 | 1 | 3 | 3 | 2 |
| 12 | 2 | 1 | 3 | 2 | 2 | 1 | 1 | 3 |
| 13 | 2 | 2 | 1 | 2 | 3 | 1 | 3 | 2 |
| 14 | 2 | 2 | 2 | 3 | 1 | 2 | 1 | 3 |
| 15 | 2 | 2 | 3 | 1 | 2 | 3 | 2 | 1 |
| 16 | 2 | 3 | 1 | 3 | 2 | 3 | 1 | 2 |
| 17 | 2 | 3 | 2 | 1 | 3 | 1 | 2 | 3 |
| 18 | 2 | 3 | 3 | 2 | 1 | 2 | 3 | 1 |

**L18 (6^1), (3^6)**
| | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|---|
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 2 | 1 | 2 | 2 | 2 | 2 | 2 | 2 |
| 3 | 1 | 3 | 3 | 3 | 3 | 3 | 3 |
| 4 | 2 | 1 | 1 | 2 | 2 | 3 | 3 |
| 5 | 2 | 2 | 2 | 3 | 3 | 1 | 1 |
| 6 | 2 | 3 | 3 | 1 | 1 | 2 | 2 |
| 7 | 3 | 1 | 2 | 1 | 3 | 2 | 3 |
| 8 | 3 | 2 | 3 | 2 | 1 | 3 | 1 |
| 9 | 3 | 3 | 1 | 3 | 2 | 1 | 2 |
| 10 | 4 | 1 | 3 | 3 | 2 | 2 | 1 |
| 11 | 4 | 2 | 1 | 1 | 3 | 3 | 2 |
| 12 | 4 | 3 | 2 | 2 | 1 | 1 | 3 |
| 13 | 5 | 1 | 2 | 3 | 1 | 3 | 2 |
| 14 | 5 | 2 | 3 | 1 | 2 | 1 | 3 |
| 15 | 5 | 3 | 1 | 2 | 3 | 2 | 1 |
| 16 | 6 | 1 | 3 | 2 | 3 | 1 | 2 |
| 17 | 6 | 2 | 1 | 3 | 1 | 2 | 3 |
| 18 | 6 | 3 | 2 | 1 | 2 | 3 | 1 |

**L25 (5^6)**
| | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 2 | 1 | 2 | 2 | 2 | 2 | 2 |
| 3 | 1 | 3 | 3 | 3 | 3 | 3 |
| 4 | 1 | 4 | 4 | 4 | 4 | 4 |
| 5 | 1 | 5 | 5 | 5 | 5 | 5 |
| 6 | 2 | 1 | 2 | 3 | 4 | 5 |
| 7 | 2 | 2 | 3 | 4 | 5 | 1 |
| 8 | 2 | 3 | 4 | 5 | 1 | 2 |
| 9 | 2 | 4 | 5 | 1 | 2 | 3 |
| 10 | 2 | 5 | 1 | 2 | 3 | 4 |
| 11 | 3 | 1 | 3 | 5 | 2 | 4 |
| 12 | 3 | 2 | 4 | 1 | 3 | 5 |
| 13 | 3 | 3 | 5 | 2 | 4 | 1 |
| 14 | 3 | 4 | 1 | 3 | 5 | 2 |
| 15 | 3 | 5 | 2 | 4 | 1 | 3 |
| 16 | 4 | 1 | 4 | 2 | 5 | 3 |
| 17 | 4 | 2 | 5 | 3 | 1 | 4 |
| 18 | 4 | 3 | 1 | 4 | 2 | 5 |
| 19 | 4 | 4 | 2 | 5 | 3 | 1 |
| 20 | 4 | 5 | 3 | 1 | 4 | 2 |
| 21 | 5 | 1 | 5 | 4 | 3 | 2 |
| 22 | 5 | 2 | 1 | 5 | 4 | 3 |
| 23 | 5 | 3 | 2 | 1 | 5 | 4 |
| 24 | 5 | 4 | 3 | 2 | 1 | 5 |
| 25 | 5 | 5 | 4 | 3 | 2 | 1 |

**L27 (3^13)**
| | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 2 | 1 | 1 | 1 | 1 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 |
| 3 | 1 | 1 | 1 | 1 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 |
| 4 | 1 | 2 | 2 | 2 | 1 | 1 | 1 | 2 | 2 | 2 | 3 | 3 | 3 |
| 5 | 1 | 2 | 2 | 2 | 2 | 2 | 2 | 3 | 3 | 3 | 1 | 1 | 1 |
| 6 | 1 | 2 | 2 | 2 | 3 | 3 | 3 | 1 | 1 | 1 | 2 | 2 | 2 |
| 7 | 1 | 3 | 3 | 3 | 1 | 1 | 1 | 3 | 3 | 3 | 2 | 2 | 2 |
| 8 | 1 | 3 | 3 | 3 | 2 | 2 | 2 | 1 | 1 | 1 | 3 | 3 | 3 |
| 9 | 1 | 3 | 3 | 3 | 3 | 3 | 3 | 2 | 2 | 2 | 1 | 1 | 1 |
| 10 | 2 | 1 | 2 | 3 | 1 | 2 | 3 | 1 | 2 | 3 | 1 | 2 | 3 |
| 11 | 2 | 1 | 2 | 3 | 2 | 3 | 1 | 2 | 3 | 1 | 2 | 3 | 1 |
| 12 | 2 | 1 | 2 | 3 | 3 | 1 | 2 | 3 | 1 | 2 | 3 | 1 | 2 |
| 13 | 2 | 2 | 3 | 1 | 1 | 2 | 3 | 2 | 3 | 1 | 3 | 1 | 2 |
| 14 | 2 | 2 | 3 | 1 | 2 | 3 | 1 | 3 | 1 | 2 | 1 | 2 | 3 |
| 15 | 2 | 2 | 3 | 1 | 3 | 1 | 2 | 1 | 2 | 3 | 2 | 3 | 1 |
| 16 | 2 | 3 | 1 | 2 | 1 | 2 | 3 | 3 | 1 | 2 | 2 | 3 | 1 |
| 17 | 2 | 3 | 1 | 2 | 2 | 3 | 1 | 1 | 2 | 3 | 3 | 1 | 2 |
| 18 | 2 | 3 | 1 | 2 | 3 | 1 | 2 | 2 | 3 | 1 | 1 | 2 | 3 |
| 19 | 3 | 1 | 3 | 2 | 1 | 3 | 2 | 1 | 3 | 2 | 1 | 3 | 2 |
| 20 | 3 | 1 | 3 | 2 | 2 | 1 | 3 | 2 | 1 | 3 | 2 | 1 | 3 |
| 21 | 3 | 1 | 3 | 2 | 3 | 2 | 1 | 3 | 2 | 1 | 3 | 2 | 1 |
| 22 | 3 | 2 | 1 | 3 | 1 | 3 | 2 | 2 | 1 | 3 | 3 | 2 | 1 |
| 23 | 3 | 2 | 1 | 3 | 2 | 1 | 3 | 3 | 2 | 1 | 1 | 3 | 2 |
| 24 | 3 | 2 | 1 | 3 | 3 | 2 | 1 | 1 | 3 | 2 | 2 | 1 | 3 |
| 25 | 3 | 3 | 2 | 1 | 1 | 3 | 2 | 3 | 2 | 1 | 2 | 1 | 3 |
| 26 | 3 | 3 | 2 | 1 | 2 | 1 | 3 | 1 | 3 | 2 | 3 | 2 | 1 |
| 27 | 3 | 3 | 2 | 1 | 3 | 2 | 1 | 2 | 1 | 3 | 1 | 3 | 2 |

**L32 (2^31)** — 원문은 열 1~16, 17~31 두 표로 분할. (두 번째 표의 4행 런 번호가 원문에 `42` 로 오기되어 있음 — 원문 그대로 표기)

열 1~16:
| | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 | 16 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 2 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 2 |
| 3 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 1 |
| 4 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 |
| 5 | 1 | 1 | 1 | 2 | 2 | 2 | 2 | 1 | 1 | 1 | 1 | 2 | 2 | 2 | 2 | 1 |
| 6 | 1 | 1 | 1 | 2 | 2 | 2 | 2 | 1 | 1 | 1 | 1 | 2 | 2 | 2 | 2 | 2 |
| 7 | 1 | 1 | 1 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 1 | 1 | 1 | 1 | 1 |
| 8 | 1 | 1 | 1 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 1 | 1 | 1 | 1 | 2 |
| 9 | 1 | 2 | 2 | 1 | 1 | 2 | 2 | 1 | 1 | 2 | 2 | 1 | 1 | 2 | 2 | 1 |
| 10 | 1 | 2 | 2 | 1 | 1 | 2 | 2 | 1 | 1 | 2 | 2 | 1 | 1 | 2 | 2 | 2 |
| 11 | 1 | 2 | 2 | 1 | 1 | 2 | 2 | 2 | 2 | 1 | 1 | 2 | 2 | 1 | 1 | 1 |
| 12 | 1 | 2 | 2 | 1 | 1 | 2 | 2 | 2 | 2 | 1 | 1 | 2 | 2 | 1 | 1 | 2 |
| 13 | 1 | 2 | 2 | 2 | 2 | 1 | 1 | 1 | 1 | 2 | 2 | 2 | 2 | 1 | 1 | 1 |
| 14 | 1 | 2 | 2 | 2 | 2 | 1 | 1 | 1 | 1 | 2 | 2 | 2 | 2 | 1 | 1 | 2 |
| 15 | 1 | 2 | 2 | 2 | 2 | 1 | 1 | 2 | 2 | 1 | 1 | 1 | 1 | 2 | 2 | 1 |
| 16 | 1 | 2 | 2 | 2 | 2 | 1 | 1 | 2 | 2 | 1 | 1 | 1 | 1 | 2 | 2 | 2 |
| 17 | 2 | 1 | 2 | 1 | 2 | 1 | 2 | 1 | 2 | 1 | 2 | 1 | 2 | 1 | 2 | 1 |
| 18 | 2 | 1 | 2 | 1 | 2 | 1 | 2 | 1 | 2 | 1 | 2 | 1 | 2 | 1 | 2 | 2 |
| 19 | 2 | 1 | 2 | 1 | 2 | 1 | 2 | 2 | 1 | 2 | 1 | 2 | 1 | 2 | 1 | 1 |
| 20 | 2 | 1 | 2 | 1 | 2 | 1 | 2 | 2 | 1 | 2 | 1 | 2 | 1 | 2 | 1 | 2 |
| 21 | 2 | 1 | 2 | 2 | 1 | 2 | 1 | 1 | 2 | 1 | 2 | 2 | 1 | 2 | 1 | 1 |
| 22 | 2 | 1 | 2 | 2 | 1 | 2 | 1 | 1 | 2 | 1 | 2 | 2 | 1 | 2 | 1 | 2 |
| 23 | 2 | 1 | 2 | 2 | 1 | 2 | 1 | 2 | 1 | 2 | 1 | 1 | 2 | 1 | 2 | 1 |
| 24 | 2 | 1 | 2 | 2 | 1 | 2 | 1 | 2 | 1 | 2 | 1 | 1 | 2 | 1 | 2 | 2 |
| 25 | 2 | 2 | 1 | 1 | 2 | 2 | 1 | 1 | 2 | 2 | 1 | 1 | 2 | 2 | 1 | 1 |
| 26 | 2 | 2 | 1 | 1 | 2 | 2 | 1 | 1 | 2 | 2 | 1 | 1 | 2 | 2 | 1 | 2 |
| 27 | 2 | 2 | 1 | 1 | 2 | 2 | 1 | 2 | 1 | 1 | 2 | 2 | 1 | 1 | 2 | 1 |
| 28 | 2 | 2 | 1 | 1 | 2 | 2 | 1 | 2 | 1 | 1 | 2 | 2 | 1 | 1 | 2 | 2 |
| 29 | 2 | 2 | 1 | 2 | 1 | 1 | 2 | 1 | 2 | 2 | 1 | 2 | 1 | 1 | 2 | 1 |
| 30 | 2 | 2 | 1 | 2 | 1 | 1 | 2 | 1 | 2 | 2 | 1 | 2 | 1 | 1 | 2 | 2 |
| 31 | 2 | 2 | 1 | 2 | 1 | 1 | 2 | 2 | 1 | 1 | 2 | 1 | 2 | 2 | 1 | 1 |
| 32 | 2 | 2 | 1 | 2 | 1 | 1 | 2 | 2 | 1 | 1 | 2 | 1 | 2 | 2 | 1 | 2 |

열 17~31:
| | 17 | 18 | 19 | 20 | 21 | 22 | 23 | 24 | 25 | 26 | 27 | 28 | 29 | 30 | 31 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 |
| 3 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 |
| 42 (원문) | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 5 | 1 | 1 | 1 | 2 | 2 | 2 | 2 | 1 | 1 | 1 | 1 | 2 | 2 | 2 | 2 |
| 6 | 2 | 2 | 2 | 1 | 1 | 1 | 1 | 2 | 2 | 2 | 2 | 1 | 1 | 1 | 1 |
| 7 | 1 | 1 | 1 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 1 | 1 | 1 | 1 |
| 8 | 2 | 2 | 2 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 2 | 2 | 2 | 2 |
| 9 | 1 | 2 | 2 | 1 | 1 | 2 | 2 | 1 | 1 | 2 | 2 | 1 | 1 | 2 | 2 |
| 10 | 2 | 1 | 1 | 2 | 2 | 1 | 1 | 2 | 2 | 1 | 1 | 2 | 2 | 1 | 1 |
| 11 | 1 | 2 | 2 | 1 | 1 | 2 | 2 | 2 | 2 | 1 | 1 | 2 | 2 | 1 | 1 |
| 12 | 2 | 1 | 1 | 2 | 2 | 1 | 1 | 1 | 1 | 2 | 2 | 1 | 1 | 2 | 2 |
| 13 | 1 | 2 | 2 | 2 | 2 | 1 | 1 | 1 | 1 | 2 | 2 | 2 | 2 | 1 | 1 |
| 14 | 2 | 1 | 1 | 1 | 1 | 2 | 2 | 2 | 2 | 1 | 1 | 1 | 1 | 2 | 2 |
| 15 | 1 | 2 | 2 | 2 | 2 | 1 | 1 | 2 | 2 | 1 | 1 | 1 | 1 | 2 | 2 |
| 16 | 2 | 1 | 1 | 1 | 1 | 2 | 2 | 1 | 1 | 2 | 2 | 2 | 2 | 1 | 1 |
| 17 | 2 | 1 | 2 | 1 | 2 | 1 | 2 | 1 | 2 | 1 | 2 | 1 | 2 | 1 | 2 |
| 18 | 1 | 2 | 1 | 2 | 1 | 2 | 1 | 2 | 1 | 2 | 1 | 2 | 1 | 2 | 1 |
| 19 | 2 | 1 | 2 | 1 | 2 | 1 | 2 | 2 | 1 | 2 | 1 | 2 | 1 | 2 | 1 |
| 20 | 1 | 2 | 1 | 2 | 1 | 2 | 1 | 1 | 2 | 1 | 2 | 1 | 2 | 1 | 2 |
| 21 | 2 | 1 | 2 | 2 | 1 | 2 | 1 | 1 | 2 | 1 | 2 | 2 | 1 | 2 | 1 |
| 22 | 1 | 2 | 1 | 1 | 2 | 1 | 2 | 2 | 1 | 2 | 1 | 1 | 2 | 1 | 2 |
| 23 | 2 | 1 | 2 | 2 | 1 | 2 | 1 | 2 | 1 | 2 | 1 | 1 | 2 | 1 | 2 |
| 24 | 1 | 2 | 1 | 1 | 2 | 1 | 2 | 1 | 2 | 1 | 2 | 2 | 1 | 2 | 1 |
| 25 | 2 | 2 | 1 | 1 | 2 | 2 | 1 | 1 | 2 | 2 | 1 | 1 | 2 | 2 | 1 |
| 26 | 1 | 1 | 2 | 2 | 1 | 1 | 2 | 2 | 1 | 1 | 2 | 2 | 1 | 1 | 2 |
| 27 | 2 | 2 | 1 | 1 | 2 | 2 | 1 | 2 | 1 | 1 | 2 | 2 | 1 | 1 | 2 |
| 28 | 1 | 1 | 2 | 2 | 1 | 1 | 2 | 1 | 2 | 2 | 1 | 1 | 2 | 2 | 1 |
| 29 | 2 | 2 | 1 | 2 | 1 | 1 | 2 | 1 | 2 | 2 | 1 | 2 | 1 | 1 | 2 |
| 30 | 1 | 1 | 2 | 1 | 2 | 2 | 1 | 2 | 1 | 1 | 2 | 1 | 2 | 2 | 1 |
| 31 | 2 | 2 | 1 | 2 | 1 | 1 | 2 | 2 | 1 | 1 | 2 | 1 | 2 | 2 | 1 |
| 32 | 1 | 1 | 2 | 1 | 2 | 2 | 1 | 1 | 2 | 2 | 1 | 2 | 1 | 1 | 2 |

**L32 (2^1), (4^9)**
| | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 2 | 1 | 1 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 |
| 3 | 1 | 1 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 |
| 4 | 1 | 1 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 |
| 5 | 1 | 2 | 1 | 1 | 2 | 2 | 3 | 3 | 4 | 4 |
| 6 | 1 | 2 | 2 | 2 | 1 | 1 | 4 | 4 | 3 | 3 |
| 7 | 1 | 2 | 3 | 3 | 4 | 4 | 1 | 1 | 2 | 2 |
| 8 | 1 | 2 | 4 | 4 | 3 | 3 | 2 | 2 | 1 | 1 |
| 9 | 1 | 3 | 1 | 2 | 3 | 4 | 1 | 2 | 3 | 4 |
| 10 | 1 | 3 | 2 | 1 | 4 | 3 | 2 | 1 | 4 | 3 |
| 11 | 1 | 3 | 3 | 4 | 1 | 2 | 3 | 4 | 1 | 2 |
| 12 | 1 | 3 | 4 | 3 | 2 | 1 | 4 | 3 | 2 | 1 |
| 13 | 1 | 4 | 1 | 2 | 4 | 3 | 3 | 4 | 2 | 1 |
| 14 | 1 | 4 | 2 | 1 | 3 | 4 | 4 | 3 | 1 | 2 |
| 15 | 1 | 4 | 3 | 4 | 2 | 1 | 1 | 2 | 4 | 3 |
| 16 | 1 | 4 | 4 | 3 | 1 | 2 | 2 | 1 | 3 | 4 |
| 17 | 2 | 1 | 1 | 4 | 1 | 4 | 2 | 3 | 2 | 3 |
| 18 | 2 | 1 | 2 | 3 | 2 | 3 | 1 | 4 | 1 | 4 |
| 19 | 2 | 1 | 3 | 2 | 3 | 2 | 4 | 1 | 4 | 1 |
| 20 | 2 | 1 | 4 | 1 | 4 | 1 | 3 | 2 | 3 | 2 |
| 21 | 2 | 2 | 1 | 4 | 2 | 3 | 4 | 1 | 3 | 2 |
| 22 | 2 | 2 | 2 | 3 | 1 | 4 | 3 | 2 | 4 | 1 |
| 23 | 2 | 2 | 3 | 2 | 4 | 1 | 2 | 3 | 1 | 4 |
| 24 | 2 | 2 | 4 | 1 | 3 | 2 | 1 | 4 | 2 | 3 |
| 25 | 2 | 3 | 1 | 3 | 3 | 1 | 2 | 4 | 4 | 2 |
| 26 | 2 | 3 | 2 | 4 | 4 | 2 | 1 | 3 | 3 | 1 |
| 27 | 2 | 3 | 3 | 1 | 1 | 3 | 4 | 2 | 2 | 4 |
| 28 | 2 | 3 | 4 | 2 | 2 | 4 | 3 | 1 | 1 | 3 |
| 29 | 2 | 4 | 1 | 3 | 4 | 2 | 4 | 2 | 1 | 3 |
| 30 | 2 | 4 | 2 | 4 | 3 | 1 | 3 | 1 | 2 | 4 |
| 31 | 2 | 4 | 3 | 1 | 2 | 4 | 2 | 4 | 3 | 1 |
| 32 | 2 | 4 | 4 | 2 | 1 | 3 | 1 | 3 | 4 | 2 |

**L36 (2^11), (3^12)** — 열 1~11 은 2수준, 12~23 은 3수준
| | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 | 20 | 21 | 22 | 23 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 2 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 |
| 3 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 |
| 4 | 1 | 1 | 1 | 1 | 1 | 2 | 2 | 2 | 2 | 2 | 2 | 1 | 1 | 1 | 1 | 2 | 2 | 2 | 2 | 3 | 3 | 3 | 3 |
| 5 | 1 | 1 | 1 | 1 | 1 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 3 | 3 | 3 | 3 | 1 | 1 | 1 | 1 |
| 6 | 1 | 1 | 1 | 1 | 1 | 2 | 2 | 2 | 2 | 2 | 2 | 3 | 3 | 3 | 3 | 1 | 1 | 1 | 1 | 2 | 2 | 2 | 2 |
| 7 | 1 | 1 | 2 | 2 | 2 | 1 | 1 | 1 | 2 | 2 | 2 | 1 | 1 | 2 | 3 | 1 | 2 | 3 | 3 | 1 | 2 | 2 | 3 |
| 8 | 1 | 1 | 2 | 2 | 2 | 1 | 1 | 1 | 2 | 2 | 2 | 2 | 2 | 3 | 1 | 2 | 3 | 1 | 1 | 2 | 3 | 3 | 1 |
| 9 | 1 | 1 | 2 | 2 | 2 | 1 | 1 | 1 | 2 | 2 | 2 | 3 | 3 | 1 | 2 | 3 | 1 | 2 | 2 | 3 | 1 | 1 | 2 |
| 10 | 1 | 2 | 1 | 2 | 2 | 1 | 2 | 2 | 1 | 1 | 2 | 1 | 1 | 3 | 2 | 1 | 3 | 2 | 3 | 2 | 1 | 3 | 2 |
| 11 | 1 | 2 | 1 | 2 | 2 | 1 | 2 | 2 | 1 | 1 | 2 | 2 | 2 | 1 | 3 | 2 | 1 | 3 | 1 | 3 | 2 | 1 | 3 |
| 12 | 1 | 2 | 1 | 2 | 2 | 1 | 2 | 2 | 1 | 1 | 2 | 3 | 3 | 2 | 1 | 3 | 2 | 1 | 2 | 1 | 3 | 2 | 1 |
| 13 | 1 | 2 | 2 | 1 | 2 | 2 | 1 | 2 | 1 | 2 | 1 | 1 | 2 | 3 | 1 | 3 | 2 | 1 | 3 | 3 | 2 | 1 | 2 |
| 14 | 1 | 2 | 2 | 1 | 2 | 2 | 1 | 2 | 1 | 2 | 1 | 2 | 3 | 1 | 2 | 1 | 3 | 2 | 1 | 1 | 3 | 2 | 3 |
| 15 | 1 | 2 | 2 | 1 | 2 | 2 | 1 | 2 | 1 | 2 | 1 | 3 | 1 | 2 | 3 | 2 | 1 | 3 | 2 | 2 | 1 | 3 | 1 |
| 16 | 1 | 2 | 2 | 2 | 1 | 2 | 2 | 1 | 2 | 1 | 1 | 1 | 2 | 3 | 2 | 1 | 1 | 3 | 2 | 3 | 3 | 2 | 1 |
| 17 | 1 | 2 | 2 | 2 | 1 | 2 | 2 | 1 | 2 | 1 | 1 | 2 | 3 | 1 | 3 | 2 | 2 | 1 | 3 | 1 | 1 | 3 | 2 |
| 18 | 1 | 2 | 2 | 2 | 1 | 2 | 2 | 1 | 2 | 1 | 1 | 3 | 1 | 2 | 1 | 3 | 3 | 2 | 1 | 2 | 2 | 1 | 3 |
| 19 | 2 | 1 | 2 | 2 | 1 | 1 | 2 | 2 | 1 | 2 | 1 | 1 | 2 | 1 | 3 | 3 | 3 | 1 | 2 | 2 | 1 | 2 | 3 |
| 20 | 2 | 1 | 2 | 2 | 1 | 1 | 2 | 2 | 1 | 2 | 1 | 2 | 3 | 2 | 1 | 1 | 1 | 2 | 3 | 3 | 2 | 3 | 1 |
| 21 | 2 | 1 | 2 | 2 | 1 | 1 | 2 | 2 | 1 | 2 | 1 | 3 | 1 | 3 | 2 | 2 | 2 | 3 | 1 | 1 | 3 | 1 | 2 |
| 22 | 2 | 1 | 2 | 1 | 2 | 2 | 2 | 1 | 1 | 1 | 2 | 1 | 2 | 2 | 3 | 3 | 1 | 2 | 1 | 1 | 3 | 3 | 2 |
| 23 | 2 | 1 | 2 | 1 | 2 | 2 | 2 | 1 | 1 | 1 | 2 | 2 | 3 | 3 | 1 | 1 | 2 | 3 | 2 | 2 | 1 | 1 | 3 |
| 24 | 2 | 1 | 2 | 1 | 2 | 2 | 2 | 1 | 1 | 1 | 2 | 3 | 1 | 1 | 2 | 2 | 3 | 1 | 3 | 3 | 2 | 2 | 1 |
| 25 | 2 | 1 | 1 | 2 | 2 | 2 | 1 | 2 | 2 | 1 | 1 | 1 | 3 | 2 | 1 | 2 | 3 | 3 | 1 | 3 | 1 | 2 | 2 |
| 26 | 2 | 1 | 1 | 2 | 2 | 2 | 1 | 2 | 2 | 1 | 1 | 2 | 1 | 3 | 2 | 3 | 1 | 1 | 2 | 1 | 2 | 3 | 3 |
| 27 | 2 | 1 | 1 | 2 | 2 | 2 | 1 | 2 | 2 | 1 | 1 | 3 | 2 | 1 | 3 | 1 | 2 | 2 | 3 | 2 | 3 | 1 | 1 |
| 28 | 2 | 2 | 2 | 1 | 1 | 1 | 1 | 2 | 2 | 1 | 2 | 1 | 3 | 2 | 2 | 2 | 1 | 1 | 3 | 2 | 3 | 1 | 3 |
| 29 | 2 | 2 | 2 | 1 | 1 | 1 | 1 | 2 | 2 | 1 | 2 | 2 | 1 | 3 | 3 | 3 | 2 | 2 | 1 | 3 | 1 | 2 | 1 |
| 30 | 2 | 2 | 2 | 1 | 1 | 1 | 1 | 2 | 2 | 1 | 2 | 3 | 2 | 1 | 1 | 1 | 3 | 3 | 2 | 1 | 2 | 3 | 2 |
| 31 | 2 | 2 | 1 | 2 | 1 | 2 | 1 | 1 | 1 | 2 | 2 | 1 | 3 | 3 | 3 | 2 | 3 | 2 | 2 | 1 | 2 | 1 | 1 |
| 32 | 2 | 2 | 1 | 2 | 1 | 2 | 1 | 1 | 1 | 2 | 2 | 2 | 1 | 1 | 1 | 3 | 1 | 3 | 3 | 2 | 3 | 2 | 2 |
| 33 | 2 | 2 | 1 | 2 | 1 | 2 | 1 | 1 | 1 | 2 | 2 | 3 | 2 | 2 | 2 | 1 | 2 | 1 | 1 | 3 | 1 | 3 | 3 |
| 34 | 2 | 2 | 1 | 1 | 2 | 1 | 2 | 1 | 2 | 2 | 1 | 1 | 3 | 1 | 2 | 3 | 2 | 3 | 1 | 2 | 2 | 3 | 1 |
| 35 | 2 | 2 | 1 | 1 | 2 | 1 | 2 | 1 | 2 | 2 | 1 | 2 | 1 | 2 | 3 | 1 | 3 | 1 | 2 | 3 | 3 | 1 | 2 |
| 36 | 2 | 2 | 1 | 1 | 2 | 1 | 2 | 1 | 2 | 2 | 1 | 3 | 2 | 3 | 1 | 2 | 1 | 2 | 3 | 1 | 1 | 2 | 3 |

**L36 (2^3), (3^13)** — 열 1~3 은 2수준, 4~16 은 3수준
| | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 | 16 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 2 | 1 | 1 | 1 | 1 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 |
| 3 | 1 | 1 | 1 | 1 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 |
| 4 | 1 | 2 | 2 | 1 | 1 | 1 | 1 | 1 | 2 | 2 | 2 | 2 | 3 | 3 | 3 | 3 |
| 5 | 1 | 2 | 2 | 1 | 2 | 2 | 2 | 2 | 3 | 3 | 3 | 3 | 1 | 1 | 1 | 1 |
| 6 | 1 | 2 | 2 | 1 | 3 | 3 | 3 | 3 | 1 | 1 | 1 | 1 | 2 | 2 | 2 | 2 |
| 7 | 2 | 1 | 2 | 1 | 1 | 1 | 2 | 3 | 1 | 2 | 3 | 3 | 1 | 2 | 2 | 3 |
| 8 | 2 | 1 | 2 | 1 | 2 | 2 | 3 | 1 | 2 | 3 | 1 | 1 | 2 | 3 | 3 | 1 |
| 9 | 2 | 1 | 2 | 1 | 3 | 3 | 1 | 2 | 3 | 1 | 2 | 2 | 3 | 1 | 1 | 2 |
| 10 | 2 | 2 | 1 | 1 | 1 | 1 | 3 | 2 | 1 | 3 | 2 | 3 | 2 | 1 | 3 | 2 |
| 11 | 2 | 2 | 1 | 1 | 2 | 2 | 1 | 3 | 2 | 1 | 3 | 1 | 3 | 2 | 1 | 3 |
| 12 | 2 | 2 | 1 | 1 | 3 | 3 | 2 | 1 | 3 | 2 | 1 | 2 | 1 | 3 | 2 | 1 |
| 13 | 1 | 1 | 1 | 2 | 1 | 2 | 3 | 1 | 3 | 2 | 1 | 3 | 3 | 2 | 1 | 2 |
| 14 | 1 | 1 | 1 | 2 | 2 | 3 | 1 | 2 | 1 | 3 | 2 | 1 | 1 | 3 | 2 | 3 |
| 15 | 1 | 1 | 1 | 2 | 3 | 1 | 2 | 3 | 2 | 1 | 3 | 2 | 2 | 1 | 3 | 1 |
| 16 | 1 | 2 | 2 | 2 | 1 | 2 | 3 | 2 | 1 | 1 | 3 | 2 | 3 | 3 | 2 | 1 |
| 17 | 1 | 2 | 2 | 2 | 2 | 3 | 1 | 3 | 2 | 2 | 1 | 3 | 1 | 1 | 3 | 2 |
| 18 | 1 | 2 | 2 | 2 | 3 | 1 | 2 | 1 | 3 | 3 | 2 | 1 | 2 | 2 | 1 | 3 |
| 19 | 2 | 1 | 2 | 2 | 1 | 2 | 1 | 3 | 3 | 3 | 1 | 2 | 2 | 1 | 2 | 3 |
| 20 | 2 | 1 | 2 | 2 | 2 | 3 | 2 | 1 | 1 | 1 | 2 | 3 | 3 | 2 | 3 | 1 |
| 21 | 2 | 1 | 2 | 2 | 3 | 1 | 3 | 2 | 2 | 2 | 3 | 1 | 1 | 3 | 1 | 2 |
| 22 | 2 | 2 | 1 | 2 | 1 | 2 | 2 | 3 | 3 | 1 | 2 | 1 | 1 | 3 | 3 | 2 |
| 23 | 2 | 2 | 1 | 2 | 2 | 3 | 3 | 1 | 1 | 2 | 3 | 2 | 2 | 1 | 1 | 3 |
| 24 | 2 | 2 | 1 | 2 | 3 | 1 | 1 | 2 | 2 | 3 | 1 | 3 | 3 | 2 | 2 | 1 |
| 25 | 1 | 1 | 1 | 3 | 1 | 3 | 2 | 1 | 2 | 3 | 3 | 1 | 3 | 1 | 2 | 2 |
| 26 | 1 | 1 | 1 | 3 | 2 | 1 | 3 | 2 | 3 | 1 | 1 | 2 | 1 | 2 | 3 | 3 |
| 27 | 1 | 1 | 1 | 3 | 3 | 2 | 1 | 3 | 1 | 2 | 2 | 3 | 2 | 3 | 1 | 1 |
| 28 | 1 | 2 | 2 | 3 | 1 | 3 | 2 | 2 | 2 | 1 | 1 | 3 | 2 | 3 | 1 | 3 |
| 29 | 1 | 2 | 2 | 3 | 2 | 1 | 3 | 3 | 3 | 2 | 2 | 1 | 3 | 1 | 2 | 1 |
| 30 | 1 | 2 | 2 | 3 | 3 | 2 | 1 | 1 | 1 | 3 | 3 | 2 | 1 | 2 | 3 | 2 |
| 31 | 2 | 1 | 2 | 3 | 1 | 3 | 3 | 3 | 2 | 3 | 2 | 2 | 1 | 2 | 1 | 1 |
| 32 | 2 | 1 | 2 | 3 | 2 | 1 | 1 | 1 | 3 | 1 | 3 | 3 | 2 | 3 | 2 | 2 |
| 33 | 2 | 1 | 2 | 3 | 3 | 2 | 2 | 2 | 1 | 2 | 1 | 1 | 3 | 1 | 3 | 3 |
| 34 | 2 | 2 | 1 | 3 | 1 | 3 | 1 | 2 | 3 | 2 | 3 | 1 | 2 | 2 | 3 | 1 |
| 35 | 2 | 2 | 1 | 3 | 2 | 1 | 2 | 3 | 1 | 3 | 1 | 2 | 3 | 3 | 1 | 2 |
| 36 | 2 | 2 | 1 | 3 | 3 | 2 | 3 | 1 | 2 | 1 | 2 | 3 | 1 | 1 | 2 | 3 |

**L54 (2^1), (3^25)** — 원문은 열 1~13, 14~26 두 표로 분할. (두 번째 표의 4행 런 번호가 원문에 `42` 로 오기 — 원문 그대로)

열 1~13:
| | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 2 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 2 | 2 | 2 | 2 | 2 |
| 3 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 3 | 3 | 3 | 3 | 3 |
| 4 | 1 | 1 | 2 | 2 | 2 | 2 | 2 | 2 | 1 | 1 | 1 | 1 | 1 |
| 5 | 1 | 1 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 |
| 6 | 1 | 1 | 2 | 2 | 2 | 2 | 2 | 2 | 3 | 3 | 3 | 3 | 3 |
| 7 | 1 | 1 | 3 | 3 | 3 | 3 | 3 | 3 | 1 | 1 | 1 | 1 | 1 |
| 8 | 1 | 1 | 3 | 3 | 3 | 3 | 3 | 3 | 2 | 2 | 2 | 2 | 2 |
| 9 | 1 | 1 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 |
| 10 | 1 | 2 | 1 | 1 | 2 | 2 | 3 | 3 | 1 | 1 | 2 | 2 | 3 |
| 11 | 1 | 2 | 1 | 1 | 2 | 2 | 3 | 3 | 2 | 2 | 3 | 3 | 1 |
| 12 | 1 | 2 | 1 | 1 | 2 | 2 | 3 | 3 | 3 | 3 | 1 | 1 | 2 |
| 13 | 1 | 2 | 2 | 2 | 3 | 3 | 1 | 1 | 1 | 1 | 2 | 2 | 3 |
| 14 | 1 | 2 | 2 | 2 | 3 | 3 | 1 | 1 | 2 | 2 | 3 | 3 | 1 |
| 15 | 1 | 2 | 2 | 2 | 3 | 3 | 1 | 1 | 3 | 3 | 1 | 1 | 2 |
| 16 | 1 | 2 | 3 | 3 | 1 | 1 | 2 | 2 | 1 | 1 | 2 | 2 | 3 |
| 17 | 1 | 2 | 3 | 3 | 1 | 1 | 2 | 2 | 2 | 2 | 3 | 3 | 1 |
| 18 | 1 | 2 | 3 | 3 | 1 | 1 | 2 | 2 | 3 | 3 | 1 | 1 | 2 |
| 19 | 1 | 3 | 1 | 2 | 1 | 3 | 2 | 3 | 1 | 2 | 1 | 3 | 2 |
| 20 | 1 | 3 | 1 | 2 | 1 | 3 | 2 | 3 | 2 | 3 | 2 | 1 | 3 |
| 21 | 1 | 3 | 1 | 2 | 1 | 3 | 2 | 3 | 3 | 1 | 3 | 2 | 1 |
| 22 | 1 | 3 | 2 | 3 | 2 | 1 | 3 | 1 | 1 | 2 | 1 | 3 | 2 |
| 23 | 1 | 3 | 2 | 3 | 2 | 1 | 3 | 1 | 2 | 3 | 2 | 1 | 3 |
| 24 | 1 | 3 | 2 | 3 | 2 | 1 | 3 | 1 | 3 | 1 | 3 | 2 | 1 |
| 25 | 1 | 3 | 3 | 1 | 3 | 2 | 1 | 2 | 1 | 2 | 1 | 3 | 2 |
| 26 | 1 | 3 | 3 | 1 | 3 | 2 | 1 | 2 | 2 | 3 | 2 | 1 | 3 |
| 27 | 1 | 3 | 3 | 1 | 3 | 2 | 1 | 2 | 3 | 1 | 3 | 2 | 1 |
| 28 | 2 | 1 | 1 | 3 | 3 | 2 | 2 | 1 | 1 | 3 | 3 | 2 | 2 |
| 29 | 2 | 1 | 1 | 3 | 3 | 2 | 2 | 1 | 2 | 1 | 1 | 3 | 3 |
| 30 | 2 | 1 | 1 | 3 | 3 | 2 | 2 | 1 | 3 | 2 | 2 | 1 | 1 |
| 31 | 2 | 1 | 2 | 1 | 1 | 3 | 3 | 2 | 1 | 3 | 3 | 2 | 2 |
| 32 | 2 | 1 | 2 | 1 | 1 | 3 | 3 | 2 | 2 | 1 | 1 | 3 | 3 |
| 33 | 2 | 1 | 2 | 1 | 1 | 3 | 3 | 2 | 3 | 2 | 2 | 1 | 1 |
| 34 | 2 | 1 | 3 | 2 | 2 | 1 | 1 | 3 | 1 | 3 | 3 | 2 | 2 |
| 35 | 2 | 1 | 3 | 2 | 2 | 1 | 1 | 3 | 2 | 1 | 1 | 3 | 3 |
| 36 | 2 | 1 | 3 | 2 | 2 | 1 | 1 | 3 | 3 | 2 | 2 | 1 | 1 |
| 37 | 2 | 2 | 1 | 2 | 3 | 1 | 3 | 2 | 1 | 2 | 3 | 1 | 3 |
| 38 | 2 | 2 | 1 | 2 | 3 | 1 | 3 | 2 | 2 | 3 | 1 | 2 | 1 |
| 39 | 2 | 2 | 1 | 2 | 3 | 1 | 3 | 2 | 3 | 1 | 2 | 3 | 2 |
| 40 | 2 | 2 | 2 | 3 | 1 | 2 | 1 | 3 | 1 | 2 | 3 | 1 | 3 |
| 41 | 2 | 2 | 2 | 3 | 1 | 2 | 1 | 3 | 2 | 3 | 1 | 2 | 1 |
| 42 | 2 | 2 | 2 | 3 | 1 | 2 | 1 | 3 | 3 | 1 | 2 | 3 | 2 |
| 43 | 2 | 2 | 3 | 1 | 2 | 3 | 2 | 1 | 1 | 2 | 3 | 1 | 3 |
| 44 | 2 | 2 | 3 | 1 | 2 | 3 | 2 | 1 | 2 | 3 | 1 | 2 | 1 |
| 45 | 2 | 2 | 3 | 1 | 2 | 3 | 2 | 1 | 3 | 1 | 2 | 3 | 2 |
| 46 | 2 | 3 | 1 | 3 | 2 | 3 | 1 | 2 | 1 | 3 | 2 | 3 | 1 |
| 47 | 2 | 3 | 1 | 3 | 2 | 3 | 1 | 2 | 2 | 1 | 3 | 1 | 2 |
| 48 | 2 | 3 | 1 | 3 | 2 | 3 | 1 | 2 | 3 | 2 | 1 | 2 | 3 |
| 49 | 2 | 3 | 2 | 1 | 3 | 1 | 2 | 3 | 1 | 3 | 2 | 3 | 1 |
| 50 | 2 | 3 | 2 | 1 | 3 | 1 | 2 | 3 | 2 | 1 | 3 | 1 | 2 |
| 51 | 2 | 3 | 2 | 1 | 3 | 1 | 2 | 3 | 3 | 2 | 1 | 2 | 3 |
| 52 | 2 | 3 | 3 | 2 | 1 | 2 | 3 | 1 | 1 | 3 | 2 | 3 | 1 |
| 53 | 2 | 3 | 3 | 2 | 1 | 2 | 3 | 1 | 2 | 1 | 3 | 1 | 2 |
| 54 | 2 | 3 | 3 | 2 | 1 | 2 | 3 | 1 | 3 | 2 | 1 | 2 | 3 |

열 14~26:
| | 14 | 15 | 16 | 17 | 18 | 19 | 20 | 21 | 22 | 23 | 24 | 25 | 26 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 |
| 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 |
| 42 (원문) | 1 | 2 | 3 | 2 | 3 | 2 | 3 | 2 | 3 | 2 | 3 | 2 | 3 |
| 5 | 2 | 3 | 1 | 3 | 1 | 3 | 1 | 3 | 1 | 3 | 1 | 3 | 1 |
| 6 | 3 | 1 | 2 | 1 | 2 | 1 | 2 | 1 | 2 | 1 | 2 | 1 | 2 |
| 7 | 1 | 3 | 2 | 3 | 2 | 3 | 2 | 3 | 2 | 3 | 2 | 3 | 2 |
| 8 | 2 | 1 | 3 | 1 | 3 | 1 | 3 | 1 | 3 | 1 | 3 | 1 | 3 |
| 9 | 3 | 2 | 1 | 2 | 1 | 2 | 1 | 2 | 1 | 2 | 1 | 2 | 1 |
| 10 | 3 | 1 | 1 | 1 | 1 | 2 | 3 | 2 | 3 | 2 | 3 | 2 | 3 |
| 11 | 1 | 2 | 2 | 2 | 2 | 3 | 1 | 3 | 1 | 1 | 3 | 1 | 3 |
| 12 | 2 | 3 | 3 | 3 | 3 | 1 | 2 | 1 | 2 | 2 | 1 | 2 | 1 |
| 13 | 3 | 2 | 3 | 2 | 3 | 3 | 2 | 3 | 2 | 1 | 1 | 1 | 1 |
| 14 | 1 | 3 | 1 | 3 | 1 | 1 | 3 | 1 | 3 | 2 | 2 | 2 | 2 |
| 15 | 2 | 1 | 2 | 1 | 2 | 2 | 1 | 2 | 1 | 3 | 3 | 3 | 3 |
| 16 | 3 | 3 | 2 | 3 | 2 | 1 | 1 | 1 | 1 | 2 | 3 | 2 | 3 |
| 17 | 1 | 1 | 3 | 1 | 3 | 2 | 2 | 2 | 2 | 3 | 1 | 3 | 1 |
| 18 | 2 | 2 | 1 | 2 | 1 | 3 | 3 | 3 | 3 | 1 | 2 | 1 | 2 |
| 19 | 3 | 1 | 1 | 2 | 3 | 1 | 1 | 3 | 2 | 2 | 3 | 3 | 2 |
| 20 | 1 | 2 | 2 | 3 | 1 | 2 | 2 | 1 | 3 | 3 | 1 | 1 | 3 |
| 21 | 2 | 3 | 3 | 1 | 2 | 3 | 3 | 2 | 1 | 1 | 2 | 2 | 1 |
| 22 | 3 | 2 | 3 | 3 | 2 | 2 | 3 | 1 | 1 | 3 | 2 | 1 | 1 |
| 23 | 1 | 3 | 1 | 1 | 3 | 3 | 1 | 2 | 2 | 1 | 3 | 2 | 2 |
| 24 | 2 | 1 | 2 | 2 | 1 | 1 | 2 | 3 | 3 | 2 | 1 | 3 | 3 |
| 25 | 3 | 3 | 2 | 1 | 1 | 3 | 2 | 2 | 3 | 1 | 1 | 2 | 3 |
| 26 | 1 | 1 | 3 | 2 | 2 | 1 | 3 | 3 | 1 | 2 | 2 | 3 | 1 |
| 27 | 2 | 2 | 1 | 3 | 3 | 2 | 1 | 1 | 2 | 3 | 3 | 1 | 2 |
| 28 | 1 | 1 | 1 | 3 | 2 | 3 | 2 | 2 | 3 | 2 | 3 | 1 | 1 |
| 29 | 2 | 2 | 2 | 1 | 3 | 1 | 3 | 3 | 1 | 3 | 1 | 2 | 2 |
| 30 | 3 | 3 | 3 | 2 | 1 | 2 | 1 | 1 | 2 | 1 | 2 | 3 | 3 |
| 31 | 1 | 2 | 3 | 1 | 1 | 1 | 1 | 3 | 2 | 3 | 2 | 2 | 3 |
| 32 | 2 | 3 | 1 | 2 | 2 | 2 | 2 | 1 | 3 | 1 | 3 | 3 | 1 |
| 33 | 3 | 1 | 2 | 3 | 3 | 3 | 3 | 2 | 1 | 2 | 1 | 1 | 2 |
| 34 | 1 | 3 | 2 | 2 | 3 | 2 | 3 | 1 | 1 | 1 | 1 | 3 | 2 |
| 35 | 2 | 1 | 3 | 3 | 1 | 3 | 1 | 2 | 2 | 2 | 2 | 1 | 3 |
| 36 | 3 | 2 | 1 | 1 | 2 | 1 | 2 | 3 | 3 | 3 | 3 | 2 | 1 |
| 37 | 2 | 1 | 1 | 2 | 3 | 3 | 2 | 1 | 1 | 3 | 2 | 2 | 3 |
| 38 | 3 | 2 | 2 | 3 | 1 | 1 | 3 | 2 | 2 | 1 | 3 | 3 | 1 |
| 39 | 1 | 3 | 3 | 1 | 2 | 2 | 1 | 3 | 3 | 2 | 1 | 1 | 2 |
| 40 | 2 | 2 | 3 | 3 | 2 | 1 | 1 | 2 | 3 | 1 | 1 | 3 | 2 |
| 41 | 3 | 3 | 1 | 1 | 3 | 2 | 2 | 3 | 1 | 2 | 2 | 1 | 3 |
| 42 | 1 | 1 | 2 | 2 | 1 | 3 | 3 | 1 | 2 | 3 | 3 | 2 | 1 |
| 43 | 2 | 3 | 2 | 1 | 1 | 2 | 3 | 3 | 2 | 2 | 3 | 1 | 1 |
| 44 | 3 | 1 | 3 | 2 | 2 | 3 | 1 | 1 | 3 | 3 | 1 | 2 | 2 |
| 45 | 1 | 2 | 1 | 3 | 3 | 1 | 2 | 2 | 1 | 1 | 2 | 3 | 3 |
| 46 | 2 | 1 | 1 | 3 | 2 | 2 | 3 | 3 | 2 | 1 | 1 | 2 | 3 |
| 47 | 3 | 2 | 2 | 1 | 3 | 3 | 1 | 1 | 3 | 2 | 2 | 3 | 1 |
| 48 | 1 | 3 | 3 | 2 | 1 | 1 | 2 | 2 | 1 | 3 | 3 | 1 | 2 |
| 49 | 2 | 2 | 3 | 1 | 1 | 3 | 2 | 1 | 1 | 2 | 3 | 3 | 2 |
| 50 | 3 | 3 | 1 | 2 | 2 | 1 | 3 | 2 | 2 | 3 | 1 | 1 | 3 |
| 51 | 1 | 1 | 2 | 3 | 3 | 2 | 1 | 3 | 3 | 1 | 2 | 2 | 1 |
| 52 | 2 | 3 | 2 | 2 | 3 | 1 | 1 | 2 | 3 | 3 | 2 | 1 | 1 |
| 53 | 3 | 1 | 3 | 3 | 1 | 2 | 2 | 3 | 1 | 1 | 3 | 2 | 2 |
| 54 | 1 | 2 | 1 | 1 | 2 | 3 | 3 | 1 | 2 | 2 | 1 | 3 | 3 |

### 7.3 Analyze Taguchi Design — 출력 개요 (analyze-taguchi-design__before-you-start__exampl_076df8c3.txt)
메뉴 `Stat > DOE > Taguchi > Analyze Taguchi Design`. 대화상자 필드(문서 확인): `Response data are in`(잡음 요인 열들, 예 Driver, Iron); `Analysis` 버튼 → `Fit linear model for`: `Signal to Noise ratios`, `Means` 체크; `Terms` 버튼(Available/Selected Terms, 예 A: Material, B: Diameter, C: Dimples, D: Thickness, AB); `Options` 버튼 → `Signal to Noise Ratio`: `Larger is better`(다른 S/N 유형 라벨은 문서에 없음); `Analysis Graphs` → `Four in one`.

출력 개요(한 단락): 선택한 반응 특성(S/N 비, 평균)마다 **Estimated Model Coefficients for SN ratios / for Means** 표(열 `Term | Coef | SE Coef | T | P`; 항은 `Material Liquid`, `Diameter 118` 처럼 "요인명 수준값" 형식, 교호작용은 `Material*Diameter Liquid 118`), **Model Summary**(`S | R-Sq | R-Sq(adj)` — 대소문자 `R-Sq` 표기), **Analysis of Variance for SN ratios / for Means**(열 `Source | DF | Seq SS | Adj SS | Adj MS | F | P`; 행 각 항 → `Residual Error` → `Total`; Model/Linear 그룹 행 없음), 그리고 **Response Table for Signal to Noise Ratios**(부제 `Larger is better`) / **Response Table for Means**(행 `Level 1`, `Level 2`, `Delta`, `Rank`; 열은 요인). Delta = 요인별 최고 평균 − 최저 평균, Rank 1 = 최대 Delta. S/N 비는 항상 최대화. 예제 수치: S/N 모형 S = 1.2793, R-Sq 99.21%, R-Sq(adj) 97.23%; 평균 모형 S = 22.9035, R-Sq 97.88%, R-Sq(adj) 92.58%; S/N Response Table Delta = Material 6.87, Diameter 7.93, Dimples 5.96, Thickness 6.96 → Rank 3, 1, 4, 2; Means Delta = 73.73, 102.60, 46.50, 45.68 → Rank 2, 1, 3, 4. 후속으로 `Predict Taguchi Results` 사용.

---

## 8. 구현 시 주의할 점

1. **CCD 설계 카탈로그는 Summary 표를 룩업으로 고정**하고, 요인 수·fraction·블록 수 조합마다 cube runs / center(cube, axial) / default α / rotatable 을 그대로 재현할 것. 산식(Runs = cube + 2K + center)은 43/44 행에서 맞지만 "3 Full 14 1" 행은 원문과 불일치(원문 오타 추정)하므로 이 한 행은 Minitab 실측으로 확인 필요.
2. **Default α 와 중앙점의 우선순위**: 블록 없음 → 회전성(α = F^0.25), 블록 있음 → 직교 블록 우선(예: 3요인 2블록 α = 1.633, 회전 불가). Face Centered 는 α = 1 고정, Custom 은 임의값. 설계표의 축 수준은 ±α 를 표시 자리수(예제: 1.633 / 1.41421)로 출력.
3. **범주형 요인 처리**: CCD/BB 에서 범주형 요인은 각 수준마다 전체 연속 설계(중앙점 포함)를 복제한다(2수준 범주형 + 2요인 14런 → 28런). 설계표에서 범주형은 정수 1, 2 로 표시.
4. **블록 × 반복 규칙 3가지**를 CCD·BB 공통 로직으로 구현(블록 없음/있음 × block-on-replicates 여부). BB 는 요인 수별 허용 블록 수가 고정(3 불가, 4→3, 5·6·7·10→2, 9→5 또는 10)이며 8요인 BB 는 카탈로그에 없음.
5. **RSM ANOVA 의 그룹 행 구조**: Model → (Blocks) → Linear → Square → 2-Way Interaction → Error → Lack-of-Fit → Pure Error → Total. Lack-of-Fit/Pure Error 는 두 조건(적합 가능하지만 빠진 항 존재 + 반복 존재)에서만 분리. 그룹 라벨은 문서에 `2-Way Interaction`/`2-Way Interactions` 두 표기가 공존하므로 어느 쪽을 쓸지 결정 필요. 계수표는 코드화 단위, 회귀식은 비코드화 단위로 별도 출력.
6. **혼합물 모형은 절편이 없다**: 성분 선형항이 절편 역할을 하므로 계수표에 Constant 행 없음, 선형항 T/P 는 `*`, DF Regression = p − 1(선형 그룹 DF = 성분 수 − 1), Seq SS 와 Adj SS 를 둘 다 표시, Model Summary 에 PRESS 포함. ANOVA 는 `Component Only` / `Component * <공정변수>` 그룹 제목 행(값 없음)을 가진다.
7. **혼합물 단위 변환 3종**(amount / proportion / pseudocomponent)과 동치 조건 표를 그대로 구현. Pseudo = (prop − low)/(1 − Σlow). 역항(inverse terms)은 비율 단위 + 하한 0 아님 조건에서만 허용. 성분 문자는 T 를 건너뛰고, 공정 변수는 X1..Xn(최대 7개, 2수준, full/fractional).
8. **PtType 코드의 의미가 제약 여부에 따라 달라짐**: 비제약은 "블렌드 성분 수"(1 꼭지점, 2 double, 3 triple ...), 제약은 1 꼭지점 / 2 모서리점; 공통으로 0 = 중앙점, −1 = 축점. 증강 기본값은 축점 + 중앙점 ON. 선형 제약은 최대 10개, extreme vertices 전용(XVERT + CONAEV).
9. **Select Optimal Design 은 후보 행 순서에 의존**하며 복원 추출로 중복점이 생길 수 있다. 지시자 열 규약(양수 = 포함·반복 수, 음수 = 보호, 0 = 후보)과 OptPoint 열 생성·새 워크시트 복사까지가 출력 사양. 통계 6종(Condition number, D(det XᵀX), A(trace (XᵀX)⁻¹), G(avg/max leverage), V(avg leverage), Max leverage) 중 Condition number 산식은 문서에 없음. Distance-based 는 교환·반복 없음, general full factorial 에서 불가.
10. **수식 본문은 대부분 이미지라 문서 텍스트에 없다.** 이 요약의 "공식"은 텍스트로 남은 식(b = (X′X)⁻¹X′y, 단위 변환, DF 규칙, p = 1 − P(F ≤ f), SSR 조건식)에 한정된다. 나머지(SE Coef, VIF, PRESS, R² 계열, Cook's D, DFITS, AICc/BIC, 신뢰·예측구간)는 표준 선형모형 정의를 쓰되 Minitab 예제 수치(SealStrength, FondueRecipe, CrystalGrowth optimal)로 반드시 검증할 것.
11. **ko-kr 라벨은 메뉴 경로가 문서마다 다르다**(`혼합` vs `혼합물 설계`), 설계표 열 `Run` 이 RS 는 `런`, 혼합물은 `실행`, 공정변수 `High` 가 `많음` 으로 번역되어 있음. 한국어 UI 구현 시 Minitab 실제 문자열과 대조 필요.
12. **문서에 없는 항목을 추측으로 채우지 말 것**: `what-is-an-optimal-design` 페이지 부재, Display Available Designs 표 부재, Terms 드롭다운의 전체 라벨 목록(`Linear + squares`, `Linear` 만 확인), Analyze Mixture 의 Type of Model/Analyze Components in/Model Fitting Method 의 나머지 라디오 라벨, Response Trace Plot 의 Piepel 방향 라벨 등은 추가 소스 확보 전까지 "미확인"으로 표시.
