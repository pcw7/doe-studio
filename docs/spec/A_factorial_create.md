# A. 요인 설계 생성 · Screening 생성 · Quick Designs · Display/Modify Design — Minitab 지원 문서 구조화 요약

- 소스: `scratchpad\minitab_pages\en-us\` (영문), `...\ko-kr\` (한국어판 일부)
- 근거 파일명은 각 절 끝 또는 항목 옆 괄호에 표기. 파일명이 길어서 `create-factorial-design__` 접두는 생략하고 해시(예: `ec5a63ac`)로 가리키는 경우가 있음. 전체 대응표는 0절 참조.
- 문서에 없는 내용은 **"문서에 없음"**으로 표기했고 추측하지 않았다.
- UI 라벨·열 이름·설계 이름 등 식별자는 영어 원문 유지.

---

## 0. 담당 파일 목록과 역할

### 0.1 Create Factorial Design (doe__how-to__factorial__create-factorial-design__…)
| 해시/파일 | 내용 |
|---|---|
| select-a-factorial-design | 메인 메뉴의 5개 설계 유형 선택 안내 |
| 5ecd5eb4 | Default Generators: Specify the type of design |
| e061dc71 | Default Generators: Display available designs (2-level & PB) |
| ae688ce8 | Default Generators: Designs 하위 대화상자 |
| 714cd4ab | Default Generators: Factors 하위 대화상자 |
| 097ff548 | Default Generators: Options 하위 대화상자 |
| e70d0850 | Default Generators: Results 하위 대화상자 |
| f7581e96 | Default Generators: Key results (해석) |
| ec5a63ac | Default Generators: All statistics (가장 상세) |
| ed4326a1 | Default Generators 예제(6요인 1/4 fraction) |
| 6f11c314 | Default Generators 블록 예제(5요인 1/2 fraction, 4 blocks) |
| 5b8a47e5 | Specify Generators: Designs 하위 대화상자 |
| 6b4d4bea | Specify Generators: Generators 하위 대화상자 |
| 04b9e5df = create-2-level-factorial-specify-generators__before-you-start__example | Specify Generators 예제(9요인 32런) — **내용 동일(바이트 동일)** |
| 878cf6c2 | Split-Plot: Designs 하위 대화상자 |
| a216f1b3 | Split-Plot: Display available designs |
| 02a08c7c = create-2-level-split-plot__before-you-start__example | Split-Plot 예제(4요인 1 HTC) — **동일 파일** |
| 65794334 | Plackett-Burman: Designs 하위 대화상자 |
| 20447def | Plackett-Burman: Display available designs(e061dc71 와 동일 본문) |
| 21568bf0 = create-plackett-burman__before-you-start__example | PB 예제(9요인 12런 + 3 CP) — **동일 파일** |
| 6d1e7681 | General Full Factorial: Designs 하위 대화상자 |
| e2876de5 | General Full Factorial: Factors 하위 대화상자 |
| 8ea1dee7 = create-general-full-factorial__before-you-start__example | GFF 예제(3요인 3수준) — **동일 파일** |

### 0.2 기타
- define-custom-factorial-design: `define-a-custom-factorial-design`, `define-custom-_d53e092e`
- display-and-modify-design: `before-you-start__overview`, `perform-the-analysi_5e0c94bc`(Display Design options), `perform-the-analysi_ac33fb1b`(Specify design modifications), `add-axial-points`, `fold-design`, `modify-factors`, `randomize-design`, `replicate-design`
- quick-designs: `overview`, `k-factor-designs`, `designs__create-2-level-factorial-design`, `designs__create-screening-design`, `designs__create-response-surface-design`, `designs__create-mixture-design`
- screening: `create-plackett-burman-design`(개요 링크만), `display-and-modify-design`(개요 링크만), `create-definitive-screening-design__before-you-start__example`, `…create-the_fa255d56`(Display available DSD), `…create-the_239c7815`(DSD Designs), `…create-the_a2f1adf2`(DSD Factors), `…create-the_bf049d39`(DSD Options), `…examine-th_a1d7bcef`(DSD All statistics)
- supporting-topics/factorial-and-screening-designs: `factorial-and_fba51f9d`(Factorial and fractional factorial designs), `available-2-l_b8869970`(Available 2-level factorial designs), `design-genera_cd92332a`(Design generators for 2-level designs), `what-is-a-design-generator`, `what-is-a-defining-relation`, `what-is-design-resolution`, `what-is-folding`, `determine-the_760d5ac6`(saturated model 항 수), `how-minitab-adds-center-points`, `how-minitab-h_2a28cf90`(handles center points), `how-minitab-s_cfbcd3e7`(stores factorial designs), `what-does-min_5ae32a40`(DOE design matrix), `how-error-is-partitioned`, `split-plot-de_2f9547fe`, `plackett-burman-designs`, `definitive-screening-designs`, `available-def_1882c84f`(Available DSD)
- supporting-topics/basics: `which-standard-designs-can-minitab-create`, `how-minitab-stores-design-information`, `coded-units-and-uncoded-units`, `how-is-a-coefficient-for-a-main-effect-calculated`, `optimality-criteria`, `what-points-can-i-use-in-a-designed-experiment`

---

## 1. 명령별 대화상자 구조

### 1.1 Create Factorial Design 메인 대화상자 (Stat > DOE > Factorial > Create Factorial Design)
(select-a-factorial-design, 5ecd5eb4, ed4326a1, 02a08c7c, 21568bf0, 8ea1dee7)

| 필드 | 선택지 / 제약 |
|---|---|
| **Type of Design** (라디오) | `2-level factorial (default generators)` — 2 ~ 15 factors<br>`2-level factorial (specify generators)` — 기본 생성자 대신 사용자 생성자<br>`2-level split-plot (hard-to-change factors)` — **최대 7 factors**<br>`Plackett-Burman design` — 2 ~ 47 factors, 각 2 levels<br>`General full factorial design` — 임의 수준 수 |
| **Number of factors** (드롭다운) | 위 범위. Split-Plot 에서는 라벨이 **Total number of factors** |
| **Display Available Designs** 버튼 | 입력 없음. 2-level/PB 용 표(Number of factors, Number of runs, Resolution) 표시 (e061dc71, 20447def). Split-plot 용은 hard-to-change 요인 수, easy-to-change 요인 수, whole plots 수, subplot runs 수, resolution, 해당되는 경우 whole plot 과 교락되는 최저차 교호작용을 표시 (a216f1b3). **표의 실제 숫자는 이 두 페이지에 없음** → 2절의 "Available 2-level factorial designs" 표로 대체 |
| **Designs…** 버튼 | 설계 생성 전 반드시 클릭해야 함("Before Minitab creates the design, you must click Designs") (5ecd5eb4) |
| **Factors…**, **Options…**, **Results…** 버튼 | 각 하위 대화상자 |

General Full Factorial 의 Number of factors 범위: 문서에 없음.

### 1.2 Create 2-Level Factorial Design (Default Generators)

#### 1.2.1 Designs 하위 대화상자 (ae688ce8, ec5a63ac)
| 필드 | 내용 / 기본값 / 제약 |
|---|---|
| **Designs table** (목록) | 요인 수에 따른 가능한 base design 목록: Full factorial / 1/2 fraction / 1/4 fraction … 각각 Runs, Resolution 포함(예제에서 "Select the 1/4 fraction design"). 목록의 정확한 열 구성은 문서에 없음(예제 표현상 `Full factorial`, `1/2 fraction`, `1/4 fraction` 이라는 행 이름 사용) |
| **Number of center points per block** | 중앙점 수. 블록이 2개 이상이면 **각 블록마다** 지정 수를 추가. 텍스트 요인 있으면 텍스트 요인 수준 조합마다 추가(3.6절). 반복(replicate)을 늘려도 중앙점은 늘지 않음(블록 수를 늘릴 때만 증가). 예: 3 CP, 2 replicates, 1 block → 총 CP 3 |
| **Number of replicates for corner points** | 1 = base design. Modify Design 으로 나중에 추가 가능 |
| **Number of blocks** | 블록 수 = replicate 수이면 replicate 하나가 블록 하나. 다르면 **블록당 런 수가 같은** 설계를 만든다. 최대 블록 수는 2.1절 표의 셀 하단 숫자 |

기본값(center points=0, replicates=1, blocks=1)은 예제의 Design Summary 출력(`Replicates: 1`, `Blocks: 1`, `Center pts (total): 0`)에서 확인됨. 대화상자의 기본 선택 설계(어느 fraction이 기본 선택인지)는 문서에 없음.

#### 1.2.2 Factors 하위 대화상자 (714cd4ab)
| 열 | 내용 |
|---|---|
| **Name** | 기본값: 알파벳 순 A, B, C, …, **I 는 건너뜀** (…H, J, K, …) |
| **Type** | `Numeric` / `Text`. 중앙점이 있고 텍스트·숫자 혼합이면 텍스트 요인의 각 수준 × 숫자 요인 중간값에 중앙점 추가 |
| **Low / High** | 기본값 코드화 단위 −1 / +1. 텍스트 요인은 자연 순서 없으면 어느 쪽을 low/high 로 해도 됨 |

#### 1.2.3 Options 하위 대화상자 (097ff548)
| 그룹 | 필드 | 내용 |
|---|---|---|
| **Fold Design** (Designs 에서 fractional 선택 시 활성) | `Do not fold` (기본) | 접지 않음 |
| | `Fold on all factors` | 모든 요인 부호 반전 복제 런 추가. 정의관계에서 **홀수 글자 단어 제거**. 모든 단어가 짝수 글자면 반복만 추가되므로 **경고 표시 후 설계를 만들지 않음** |
| | `Fold just on factor` (요인 선택) | 지정 요인만 부호 반전. 정의관계에서 **그 요인을 포함하는 단어 제거** |
| **Fraction** | `Use principal fraction` (기본) | 모든 생성자 부호가 + 인 fraction |
| | `Use fraction number` (정수 입력) | 1/4 fraction 이면 1~4, 1/8 fraction 이면 1~8. **principal fraction = 가장 큰 번호**(1/8 이면 8). 다른 fraction 을 원하면 1/8 의 경우 1~7 입력 |
| **Randomize runs** (체크, 기본 ON) | | 블록 내에서 런 순서 랜덤화. 해제 시 표준 순서로 저장 |
| | **Base for random data generator** (정수) | 같은 base 면 같은 런 순서 |
| **Store design in worksheet** (체크, 기본 ON) | | 해제하면 워크시트에 저장하지 않고 출력(런 수, alias table 등)만 표시. 분석하려면 반드시 저장 필요 |

주의: 원문에 "Do not fold: Fold on all factors to decrease…" 로 라벨이 붙어 있으나 문맥상 `Do not fold` / `Fold on all factors` / `Fold just on factor` 세 선택지로 해석됨(한국어판 라벨: `접지 않음`, `다음 요인에 대해서만 접기`).

#### 1.2.4 Results 하위 대화상자 (e70d0850)
| 그룹 | 선택지 | 내용 |
|---|---|---|
| **Printed Results** | `None` | 출력 억제 |
| | `Summary table` | 설계 속성 + 설계 생성자. 접은 경우 생성자는 **접기 전** 설계의 것 |
| | `Summary table and alias table` (문서에서는 "Alias table" 항목으로 설명) | alias 구조 |
| | `Summary table, alias table, design table` ("Design table") | 런별 요인 설정 |
| | `Summary table, alias table, design table, defining relation` ("Defining relation") | 접은 경우 **접은 후** 설계의 정의관계 표시 |
| **Content of Alias Table** | `Default interactions` | ≤7 factors: 모든 alias 항 표시 / 8–10 factors: 3-factor 교호작용까지 / 11–15 factors: 2-factor 교호작용까지 |
| | `Interactions up through order` (정수) | 예: 2 → 주효과와 2-factor 교호작용만 |

라디오 라벨의 정확한 문자열은 예제에서 "Select Summary table, alias table, design table, defining relation" 및 "Select Summary table and design table" 으로 나타남(04b9e5df, 02a08c7c, 21568bf0, 8ea1dee7). 어느 항목이 기본값인지는 문서에 없음(예제 ed4326a1 은 Results 를 건드리지 않고 Summary + Alias + 워크시트가 출력됨).

### 1.3 Create 2-Level Factorial Design (Specify Generators)

#### 1.3.1 Designs 하위 대화상자 (5b8a47e5)
| 필드 | 내용 |
|---|---|
| **Available designs** (목록) | base design 의 런 수와 해상도 선택. 최종 해상도는 추가 생성자에 따라 달라짐 |
| **Number of center points per block** | 1.2.1 과 동일 규칙. "Replicates do not add additional center points beyond what you specify" |
| **Number of replicates for corner points** | 1.2.1 과 동일 |
| **Generators…** 버튼 | base design 지정 후 클릭 |

Number of blocks 필드는 이 대화상자 설명에 없음(블록은 Generators 에서 block generator 로 정의).

#### 1.3.2 Generators 하위 대화상자 (6b4d4bea, what-is-a-design-generator)
| 필드 | 규칙 |
|---|---|
| **Add factors to the base design by listing their generators (e.g. F=ABC)** | 예: 8요인 설계에 `J = ABCDEFGH`. 규칙: ① 추가 요인은 알파벳 순, **I 건너뜀**(Identity) ② 전체 요인 수 ≤ 15 ③ 요인마다 고유 생성자 ④ 생성자는 base design 요인들의 교호작용 ⑤ 음수 가능 `D = -AB` |
| **Define blocks by listing their generators (e.g., ABCD)** | base 요인과 추가 요인 모두 사용 가능. 블록 수 = 2^p (p = 블록 생성자 수). 예: 6요인에 `ABCF ABDE` → 4 blocks |

base design 결정법: (원하는 총 요인 수) − (생성자 수) = base 요인 수 → 그 요인 수에서 원하는 런 수를 가진 설계 선택. 예: 2^(5-2) 8런에서 D=AB, E=BC 를 쓰려면 Number of factors=3, Designs=Full factorial, Generators 에 `D = AB E = BC` (what-is-a-design-generator).

### 1.4 Create 2-Level Split-Plot Design

#### 1.4.1 메인: Type of Design=`2-level split-plot (hard-to-change factors)`, **Total number of factors** (최대 7) (02a08c7c, select-a-factorial-design)

#### 1.4.2 Designs 하위 대화상자 (878cf6c2)
| 필드 | 내용 |
|---|---|
| **Number of hard-to-change factors** | HTC 요인 수 |
| **Designs table** | whole plots 수, subplots 수, runs, resolution 선택. 목록 순서: whole plots 수 오름차순 → 같은 whole plots 내에서는 subplots(=runs) 오름차순, 따라서 같은 whole plots 수에서 아래로 갈수록 해상도 증가. 예제 항목명: `Full factorial with 2 whole plots and 8 subplots` |
| **Number of whole-plot replicates** | base design 반복 횟수. 일부 설계에서 1 이면 HTC 요인의 유의성을 계산할 수 없어 **Minitab 이 기본값을 2 로 설정** |
| **Block on replicates** (체크) | replicate 마다 별도 블록 |
| **Number of subplot replicates** | whole plot 내에서 easy-to-change 요인 조합 반복. 예: base 2 runs/whole plot, subplot replicates 2 → whole plot 당 4 runs |

- 중앙점: **분할구 설계에서는 사용 불가**(how-minitab-adds-center-points 의 Note).
- 가용 분할구 설계의 실제 표(숫자): 문서에 없음(a216f1b3 은 열 설명만).
- Factors/Options/Results 하위 대화상자의 분할구 전용 설명: 문서에 없음(예제에서 Results 는 2-level 과 같은 4단계 선택 사용).

### 1.5 Create Plackett-Burman Design (65794334, 21568bf0, plackett-burman-designs)
메인: Type of Design=`Plackett-Burman design`, Number of factors 2~47.

| Designs 필드 | 내용 |
|---|---|
| **Number of runs** | 12 ~ 48, 4의 배수. 요인 수 < 런 수 (20런 → 최대 19 요인). **8런·16런 PB 는 제공하지 않음**(동등 이상 해상도의 2-level 설계가 있어서) |
| **Number of center points per replicate** | 텍스트 요인이 있으면 수준별로 추가(2배). **replicate 마다 중앙점이 두 배**: 3 CP/replicate × 2 replicates → 6 CP. 블록 여부와 무관 |
| **Number of replicates** | corner points 반복 |
| **Block on replicates** (체크) | replicate 마다 블록 |

같은 Designs 대화상자가 Stat > DOE > Screening > Create Screening Design > Designs 에도 쓰임.

### 1.6 Create General Full Factorial Design (6d1e7681, e2876de5, 8ea1dee7)
| 하위 대화상자 | 필드 |
|---|---|
| **Designs** | **Factor table**: `Name`, `Number of Levels` / **Number of replicates** / **Block on replicates** (체크) |
| **Factors** | `Name`(기본 알파벳, I 건너뜀), `Type`(Text/Numeric), `Level Values`(각 수준 라벨) |

- 중앙점·fold·axial 없음(Modify Design 에서 GFF 는 fold·axial 불가, 6절).
- which-standard-designs 에서는 "The factors are all categorical" 이라고 설명하지만 Factors 대화상자는 Text/Numeric 지정 가능.

### 1.7 Create Screening Design — Definitive Screening (Stat > DOE > Screening > Create Screening Design)
(create-definitive-screening-design 예제, 239c7815, a2f1adf2, bf049d39, fa255d56)

| 대화상자 | 필드 / 규칙 |
|---|---|
| 메인 | **Type of Design**: `Definitive Screening` / `Plackett-Burman` (PB 선택 시 1.5 와 동일 Designs) ; **Number of factors** ; **Display Available Designs**(DSD 용: Number of factors, Number of runs 두 열만, 입력 없음) |
| **Designs** | **Number of replicates** ; **Number of blocks** — 블록 수 = replicate 수이면 replicate 하나가 블록 하나. 한 블록에 여러 replicate 가능, **각 블록의 replicate 수는 같음** |
| **Factors** | `Name`(알파벳, I 건너뜀), `Type`(Text/Numeric; **범주형은 2 수준만**), `Low/High`(기본 −1/+1). **텍스트 요인이 1개라도 있으면 base design 에 replicate 당 중앙점 2개, 없으면 1개** |
| **Options** | **Randomize runs**(블록 내 랜덤화) ; **Base for random data generator** |
| Results | 예제: "Select Summary table and design table" — 세부 선택지 목록은 문서에 없음 |

### 1.8 Define Custom Factorial Design (define-a-custom-factorial-design, define-custom-_d53e092e)
- 하위 명령: `Define Custom 2-Level Factorial Design`, `Define Custom 2-Level Split-Plot Design`, `Define Custom General Full Factorial Design` (desktop app 전용 표기).
- Define Custom 2-Level Factorial Design:
  - **Factors**: 요인 설정이 들어 있는 열들(필수, 유일하게 필요한 정보).
  - **Low/High…** 버튼: 반드시 검토해야 설계가 정의됨.
  - 선택 정보: `Blocks`, `Standard Order`, `Run Order`, `Center Point` 열 — 워크시트에 없으면 Minitab 이 생성.
  - 예시 워크시트: `Time | Temperature | Catalyst | Blocks | Standard Order | Run Order | Center Points` (Time, Temperature 숫자, Catalyst 텍스트).

### 1.9 한국어 UI 라벨 매핑 (ko-kr 파일에서 확인된 것만)
(ko-kr: 04b9e5df, 097ff548, 6f11c314, 714cd4ab, ae688ce8, ed4326a1, split 02a08c7c, GFF 8ea1dee7, PB 21568bf0, quick create-2-level, DSD example, what-is-a-design-generator)

| 영어 | 한국어 |
|---|---|
| Stat > DOE > Factorial > Create Factorial Design | 통계분석 > 실험계획법 > 요인 설계 > 요인 설계 생성 |
| Stat > DOE > Screening > Create Screening Design | 통계분석 > 실험계획법 > 선별 설계 > 선별 설계 생성 |
| Stat > DOE > Quick Designs | 통계분석 > 실험계획법 > 빠른 설계 |
| Stat > DOE > Modify Design / Display Design | 통계분석 > 실험계획법 > 설계 수정 / 설계 표시 |
| Type of Design | 설계 유형 |
| 2-level factorial (default generators) | 2-수준 요인(기본 생성자) |
| 2-level factorial (specify generators) | 2-수준 요인(생성자 지정) |
| 2-level split-plot (hard-to-change factors) | 2-수준 분할구(HTC 요인) |
| Plackett-Burman design | Plackett-Burman 설계 |
| General full factorial design | 일반 완전 요인 설계 |
| Definitive Screening | 확정 선별 |
| Number of factors / Total number of factors | 요인 수 / 전체 요인 수 |
| Designs / Factors / Options / Results / Generators (버튼) | 설계 / 요인 / 옵션 / 결과 / 생성자 |
| Full factorial / 1/2 fraction / 1/4 fraction | 완전 요인 설계 / 1/2 부분 / 1/4 부분 |
| Number of blocks | 블럭 수 |
| Number of center points per block | 블럭당 중앙점 수 |
| Number of replicates for corner points | 꼭지점의 반복실험 횟수 |
| Number of replicates | 반복실험 횟수 |
| Number of runs | 런 수 |
| Number of center points per replicate | 반복실험당 중앙점 개수 |
| Number of hard-to-change factors | HTC 요인 수 |
| Full factorial with 2 whole plots and 8 subplots | 주구가 2개이고 분할구가 8개인 완전 요인 설계 |
| Number of whole-plot replicates | 주구 반복실험의 수 |
| Name / Type / Text / Number of Levels / Level Values | 이름 / 유형 / 텍스트 / 수준 개수 / 수준 값 |
| Low / High | 낮음 / 높음 |
| Add factors to the base design by listing their generators (e.g. F=ABC) | 관련 생성자(예: F=ABC)를 나열하여 기본 설계에 요인 추가 |
| Summary table, alias table, design table, defining relation | 요약 표, 별칭 표, 설계 표, 정의 관계 |
| Content of Alias Table / Interactions up through order | 별칭 표 내용 / 교호작용의 최대 차수 |
| Fold Design / Do not fold / Fold just on factor | 설계 접기 / 접지 않음 / 다음 요인에 대해서만 접기 |
| Fraction / Use principal fraction / Use fraction number | 부분 설계 / 주 부분 사용 / 부분 번호 사용 |
| Randomize runs / Base for random data generator | 런 랜덤화 / 랜덤 데이터 생성자를 위한 기준값 |
| Store design in worksheet | 워크시트에 설계 저장 |
| Design Summary | 설계 요약 |
| Factors: / Runs: / Blocks: | 요인: / 런: / 블럭: |
| Base Design: / Replicates: / Center pts (total): | 기본 설계: / 반복실험: / 중앙점(전체): |
| Resolution: / Resolution with blocks: / Fraction: | 해: / 블럭을 포함한 해: / 부분: |
| Design Generators: / Block Generators: / Defining Relation: | 설계 생성자: / 블럭 생성자: / 정의 관계: |
| Alias Structure / Alias Structure (up to order 2) | 별칭 구조 / 별칭 구조(2차까지) |
| Blk1 = AB + CDE (alias 표 내) | 블록1 = AB + CDE |
| * NOTE * Blocks are confounded with two-way interactions. | * 참고 * 블럭이 2차 교호작용과 교락되어 있습니다. |
| Design Table (randomized) | 설계 표(랜덤화) |
| Run / Blk / WP (설계표 열) | 런 / 블록 / 주구 지시자 |
| StdOrder / RunOrder / CenterPt / Blocks (워크시트 열) | 표준 순서 / 런 순서 / 중앙점 / 블럭 |
| Whole plots: / Hard-to-change: / Runs per whole plot: / Whole-plot replicates: / Subplot replicates: | 주구: / HTC: / 주구당 런 수: / 주구 반복실험: / 하위구 반복실험: |
| Hard-to-change factors: / Whole Plot Generators: | HTC 요인: / 주구 생성자: |
| All terms are free from aliasing. | 모든 항에 별칭이 없습니다. |
| Base runs: / Total runs: / Base blocks: / Total blocks: / Center points: | 기본 런: / 전체 런 수: / 기본 블럭: / 전체 블럭 수: / 중앙점: |
| Number of levels: 3, 3, 3 | 수준 개수: 3, 3, 3 |
| Quick Designs: Select a Six-Factor Design | 6-요인 설계 선택 |
| Quick Designs: Estimate main and interaction effects | 주효과와 교호작용 효과를 추정합니다 |
| Quick Designs: Create an experiment with two or more continuous factors | (한국어판 표기) 두 개 또는 세 개의 요인이 숫자 값의 범위로 구성된 경우 효과를 추정합니다 |
| Quick Designs: Enter the name of your response variable | 반응 변수의 이름 입력 |
| Quick Designs: Continuous / None (replicates) | 계량형 / 없음 |
| Interpret the results | 결과 해석 |

---

## 2. 가용 설계 표 (숫자 원문 그대로)

### 2.1 Available 2-level factorial designs (available-2-l_b8869970)
"2-level default designs 및 specify-generators 의 base design 요약. 셀 첫 항목 = 블록 없는 설계의 resolution, 둘째 숫자 = 사용 가능한 최대 블록 수."

| Number of runs \ factors | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 4 | full 2 | III 1 | | | | | | | | | | | | |
| 8 | | full 4 | IV 4 | III 2 | III 2 | III 1 | | | | | | | | |
| 16 | | | full 8 | V 8 | IV 8 | IV 8 | IV 8 | III 4 | III 4 | III 4 | III 4 | III 2 | III 2 | III 1 |
| 32 | | | | full 16 | VI 16 | IV 8 | IV 8 | IV 8 | IV 8 | IV 8 | IV 8 | IV 8 | IV 8 | IV 8 |
| 64 | | | | | full 32 | VII 16 | V 16 | IV 16 | IV 16 | IV 16 | IV 16 | IV 16 | IV 16 | IV 16 |
| 128 | | | | | | full 64 | VIII 32 | VI 16 | V 16 | V 16 | IV 16 | IV 16 | IV 16 | IV 16 |

### 2.2 Design generators for 2-level designs (design-genera_cd92332a)
형식: 첫 줄 = 요인 수, 런 수, 블록 없는 해상도, base design 생성자. 이어서 블록 생성자: `N(생성자들)R` = N 블록, 괄호 안 블록 생성자, R = 블록 설계의 해상도. 예 `2(AB)3` = 2 blocks, 생성자 AB, 해상도 3.

| Factors | Runs | Resolution | Design Generators (및 블록 생성자) |
|---|---|---|---|
| 2 | 4 | - | Full 2(AB)3 |
| 3 | 4 | III | C=AB No blocking |
| 3 | 8 | - | Full 2(ABC)4 4(AB,AC)3 |
| 4 | 8 | IV | D=ABC 2(AB)3 4(AB,AC)3 |
| 4 | 16 | - | Full 2(ABCD)5 4(BC,ABD)3 8(AB,BC,CD)3 |
| 5 | 8 | III | D=AB, E=AC 2(BC)3 |
| 5 | 16 | V | E=ABCD (E=ABC for 8 blocks) 2(AB)3 4(AB,AC)3 8(AB,AC,AD)3 |
| 5 | 16 | V | E=ABCD (E=ABC for 8 blocks) 2(AB)3 4(AB,AC)3 8(AB,AC,AD)3 *(원문에 같은 행이 두 번 있음)* |
| 5 | 32 | - | Full 2(ABCDE)6 4(ABC,CDE)4 8(AC,BD,ADE)3 16(AB,AC,CD,DE)3 |
| 6 | 8 | III | D=AB, E=AC, F=BC 2(BE)3 |
| 6 | 16 | IV | E=ABC, F=BCD 2(ACD)4 4(AE,ACD)3 8(AB,BC,BF)3 |
| 6 | 32 | VI | F=ABCDE 2(ABF)4 4(BC,ABF)3 8(AD,BC,ABF)3 16(AB,BC,CD,DE)3 |
| 6 | 64 | - | Full 2(ABCDEF)7 4(ABCF,ABDE)5 8(ACE,ADF,BCF)4 16(AD,BE,CE,ABF)3 32(AB,BC,CD,DE,EF)3 |
| 7 | 8 | III | D=AB, E=AC, F=BC, G=ABC no blocking |
| 7 | 16 | IV | E=ABC, F=BCD, G=ACD 2(ABD)4 4(AB,AC)3 8(AB,AC,AD)3 |
| 7 | 32 | IV | F=ABCD, G=ABDE 2(CDE)4 4(CF,CDE)3 8(AB,AD,CG)3 |
| 7 | 64 | VII | G=ABCDEF 2(CDE)4 4(ACF,CDE)4 8(ACF,ADG,CDE)4 16(AB,AC,EF,EG)3 |
| 7 | 128 | - | Full 2(ABCDEFG)8 4(ABDE,ABCFG)5 8(ABC,AFG,DEF)4 16(ABE,ADG,CDE,EFG)4 32(AC,BD,CE,DF,ABG)3 64(AB,BC,CD,DE,EF,FG)3 |
| 8 | 16 | IV | E=BCD, F=ACD, G=ABC, H=ABD 2(AB)3 4(AB,AC)3 8(AB,AC,AD)3 |
| 8 | 32 | IV | F=ABC, G=ABD, H=BCDE 2(ABE)4 4(EH,ABE)3 8(AB,AC,BD)3 |
| 8 | 64 | V | G=ABCD, H=ABEF 2(ACE)4 4(ACE,BDF)4 8(BC,FH,BDF)3 16(BC,DE,FH,BDF)3 |
| 8 | 128 | VIII | H=ABCDEFG 2(ABCD)5 4(ABCD,ABEF)5 8(ABCD,ABEF,BCEG)5 16(BF,DE,ABG,AEH)3 32(AC,BD,BF,DE,AEH)3 |
| 9 | 16 | III | E=ABC, F=BCD, G=ACD, H=ABD, J =ABCD 2(AB)3 4(AB,AC)3 |
| 9 | 32 | IV | F=BCDE,G=ACDE,H=ABDE,J=ABCE 2(AEF)4 4(AB,CD)3 8(AB,AC,CD)3 |
| 9 | 64 | IV | G=ABCD, H=ACEF, J=CDEF 2(BCE)4 4(ABF,ACJ)4 8(AD,AH,BDE)3 16(AC,AD,AJ,BF)3 |
| 9 | 128 | VI | H=ACDFG, J=BCEFG 2(CDEJ)5 4(ABFJ,CDEJ)5 8(ACF,AHJ,BCJ)4 16(AE,CG,BCJ,BDE)3 |
| 10 | 16 | III | E=ABC, F=BCD, G=ACD, H=ABD, J =ABCD, K=AB 2(AC)3 4(AD,AG)3 |
| 10 | 32 | IV | F=BCDE,G=ACDE,H=ABDE,J=ABCE 2(AB)3 4(AB,BC)3 8(AB,AC,AH)3 *(원문 그대로; 10요인인데 생성자가 4개만 적혀 있음 — K 생성자 누락으로 보임, 문서 원문 기준)* |
| 10 | 64 | IV | G=BCDF, H=ACDF, J=ABDE, K=ABCE 2(AGJ)4 4(CD,AGJ)3 8(AG,CJ,CK)3 16(AC,AG,CJ,CK)3 |
| 10 | 128 | V | H=ABCG, J=BCDE, K=ACDF 2(ADG)4 4(ADG,BDF)4 8(AEH,AGK,CDH)4 16(BH,EG,JK,ADG)3 |
| 11 | 16 | III | E=ABC, F=BCD, G=ACD, H=ABD, J=ABCD, K=AB, L=AC 2(AD)3 4(AE,AH)3 |
| 11 | 32 | IV | F=ABC, G=BCD, H=CDE, J=ACD, K=ADE, L=BDE 2(ABD)4 4(AK,ABD)3 8(AB,AC,AD)3 |
| 11 | 64 | IV | G=CDE, H=ABCD, J=ABF, K=BDEF, L=ADEF 2(AHJ)4 4(FL,AHJ)3 8(CD,CE,DL)3 16(AB,AC,AE,AF)3 |
| 11 | 128 | V | H=ABCG, J=BCDE, K=ACDF 2(ADJ)4 4(ADJ,BFH)4 8(ADJ,AHL,BFH)4 16(BC,DF,GL,BFH)3 *(원문 그대로; L 생성자 미기재)* |
| 12 | 16 | III | E=ABC, F=ABD, G=ACD, H=BCD, J=ABCD, K=AB, L=AC, M=AD 2(AG)3 4(AF,AG)3 |
| 12 | 32 | IV | F=ACE, G=ACD, H=ABD, J=ABE, K=CDE, L=ABCDE, M=ADE 2(ABC)4 4(DG,DH)3 8(AB,AC,AD)3 |
| 12 | 64 | IV | G=DEF, H=ABC, J=BCDE, K=BCDF, L=ABEF, M=ACEF 2(ABM)4 4(AB,AC)3 8(AB,AC,BM)3 16(AB,AD,BE,BM)3 |
| 12 | 128 | IV | H=ACDG, J=ABCD, K=BCFG, L=ABDEFG, M=CDEF 2(ACF)4 4(BG,BJ)3 8(BG,BJ,AGM)3 16(BG,BJ,FM,AGM)3 |
| 13 | 16 | III | E=ABC, F=ABD, G=ACD, H=BCD, J=ABCD, K=AB, L=AC, M=AD, N=BC 2(AG)3 |
| 13 | 32 | IV | F=ACE, G=BCE, H=ABC, J=CDE, K=ABCDE, L=ABE, M=ACD, N=ADE 2(ABD)4 4(CG,GH)3 8(AB,AC,AD)3 |
| 13 | 64 | IV | G=ABC, H=DEF, J=BCDF, K=BCDE, L=ABEF, M=ACEF, N=BCEF 2(AB)3 4(AB,AC)3 8(AB,AC,AN)3 16(AB,AD,BE,BM)3 |
| 13 | 128 | IV | H=DEFG, J=BCEG, K=BCDFG, L=ABDEF, M=ACEF, N=ABC 2(ACF)4 4(BG,BJ)3 8(BG,BJ,AGM)3 16(BG,BJ,FM,AGM)3 |
| 14 | 16 | III | E=ABC, F=ABD, G=ACD, H=BCD, J=ABCD, K=AB, L=AC, M=AD, N=BC, O=BD 2(AG)3 |
| 14 | 32 | IV | F=ABC, G=ABD, H=ABE, J=ACD, K=ACE, L=ADE, M=BCD, N=BCE, O=BDE 2(ACL)4 4(AB,ACL)3 8(AC,AL,AO)3 |
| 14 | 64 | IV | G=BEF, H=BCF, J=DEF, K=CEF, L=BCE, M=CDF, N=ACDE, O=BCDEF 2(ABC)4 4(BC,BE)3 8(BC,BE,BG)3 16(AB,BC,BE,BG)3 |
| 14 | 128 | IV | H=EFG, J=BCFG, K=BCEG, L=ABEF, M=ACEF, N=BCDEF, O=ABC 2(ADE)4 4(AB,AC)3 8(AB,AC,BM)3 16(AB,AC,BM,DG)3 |
| 15 | 16 | III | E=ABC, F=ABD, G=ACD, H=BCD, J=ABCD, K=AB, L=AC, M=AD, N=BC, O=BD,P=CD No blocking |
| 15 | 32 | IV | F=ABC, G=ABD, H=ABE, J=ACD, K=ACE, L=ADE, M=BCD, N=BCE, O=BDE, P=CDE 2(ABP)4 4(AB,BP)3 8(AB,AD,AK)3 |
| 15 | 64 | IV | G=ABC, H=ABD, J=ABE, K=ABF, L=ACD, M=ACE, N=ACF, O=ADE, P=ADF 2(ABL)4 4(AM,ABL)3 8(AB,AC,AD)3 16(AB,AC,AD,AE)3 |
| 15 | 128 | IV | H=ABFG, J=ACDEF, K=BEF, L=ABCEG, M=CDFG, N=ACDEG, O=EFG, P=ABDEFG 2(ADE)4 4(EG,GP)3 8(EG,GP,OP)3 16(BO,EG,GP,OP)3 |

(요인 문자는 A…H, J…P — I 없음. 15요인 → P.)

### 2.3 Available definitive screening designs (available-def_1882c84f)
"런 수는 모든 요인이 연속형인 단일 replicate 기준. 범주형 요인이 포함되면 replicate 당 1 run 추가."

| Number of factors | Number of runs |
|---|---|
| 2–6 | 13 |
| 7–8 | 17 |
| 9–10 | 21 |
| 11–12 | 25 |
| 13–14 | 29 |
| 15–16 | 33 |
| 17–18 | 37 |
| 19–20 | 41 |
| 21–24 | 49 |
| 25–26 | 53 |
| 27–30 | 61 |
| 31–32 | 65 |
| 33–38 | 77 |
| 39–42 | 85 |
| 43–44 | 89 |
| 45–48 | 97 |

(DSD All statistics 예: 4 factors → base 13 runs; 8 factors → 17 runs, 2 replicates → 34.)

### 2.4 Plackett-Burman 가용 설계와 생성 열 (plackett-burman-designs)
- 런 수 n = 12, 16?, … **아니다**: "Each design is based on the number of runs, from 12 to 48, and is always a multiple of 4" → n ∈ {12, 16, 20, 24, 28, 32, 36, 40, 44, 48}. 단, **8런·16런은 Create Factorial Design 에서 제공하지 않음**(Note). 아래 생성열 목록에도 16 은 없음 → 실제 제공: 12, 20, 24, 28, 32, 36, 40, 44, 48.
- 요인 수 k ≤ n − 1. k < n − 1 이면 **처음 k 열만 사용**.
- 구성법: n = 28 외에는 **첫 열 하나**(아래에 행으로 표기)를 **순환 치환(cyclic permutation)** 하여 (n−1)×(n−1) 행렬을 만들고 **마지막에 모두 − 인 행**을 추가. n = 28 은 아래 9행으로 시작 → 9열씩 3블록으로 나눔 → 3블록을 행 방향으로 순환 치환 → 마지막에 모두 − 인 **열** 추가.
- 12, 20, 24런 설계는 각 주효과가 둘 이상의 2-way 교호작용과 부분 교락.

생성 열(원문 그대로):
```
12 Runs
 + + - + + + - - - + -
20 Runs
 + + - - + + + + - + - + - - - - + + -
24 Runs
+ + + + + - + - + + - - + + - - + - + - - - -
28 Runs
+ - + + + + - - - - + - - - + - - + + + - + - + + - +
+ + - + + + - - - - - + + - - + - - - + + + + - + + -
- + + + + + - - - + - - - + - - + - + - + - + + - + +
- - - + - + + + + - - + - + - - - + + - + + + - + - +
- - - + + - + + + + - - - - + + - - + + - - + + + + -
- - - - + + + + + - + - + - - - + - - + + + - + - + +
+ + + - - - + - + - - + - - + - + - + - + + - + + + -
+ + + - - - + + - + - - + - - - - + + + - + + - - + +
+ + + - - - - + + - + - - + - + - - - + + - + + + - +
32 Runs
 - - - - + - + - + + + - + + - - - + + + + + - - + + - + - - +
36 Runs
 - + - + + + - - - + + + + + - + + + - - + - - - - + - + - + + - - + -
40 Runs (derived by duplicating the 20 run design)
 + + - - + + + + - + - + - - - - + + - + + - - + + + + - + - + - - - - + + -
44 Runs
 + + - - + - + - - + + + - + + + + + - - - + - + + + - - - - - + - - - + +- + - + + -
48 Runs
 + + + + + - + + + + - - + - + - + + + - - + - - + + - + + - - - + - + - + + - - - - + - - - -
```
원문 표기 주의: 44 Runs 행에 `+-` 가 붙어 있음(43개 부호로 세면 맞음). 40 Runs 행은 원문 그대로 세면 38개 부호(39개여야 함) — 문서 원문 오류 가능성, "derived by duplicating the 20 run design" 규칙(20런 생성열 반복)을 우선 적용 여부는 구현 시 검증 필요.

### 2.5 Display Available Designs 대화상자
- 2-level/PB: Number of factors, Number of runs, Resolution 표 — **표 숫자는 문서에 없음**(e061dc71, 20447def). 2.1 표로 대체 가능.
- Split-plot: 열 구성만 기술 — **숫자 문서에 없음**(a216f1b3).
- DSD: Number of factors, Number of runs — 2.3 표.

### 2.6 Fraction 번호 순서 표 (factorial-and_fba51f9d)
6요인 8런(D=AB, E=AC, F=BC, 1/8 fraction)의 8개 fraction 순서:

| Fraction | Standard (Yates) Order | Design Generator |
|---|---|---|
| 1 | – – – | D = –AB, E = –AC, F = –BC |
| 2 | + – – | D = +AB, E = –AC, F = –BC |
| 3 | – + – | D = –AB, E = +AC, F = –BC |
| 4 | + + – | D = +AB, E = +AC, F = –BC |
| 5 | – – + | D = –AB, E = –AC, F = +BC |
| 6 | + – + | D = +AB, E = –AC, F = +BC |
| 7 | – + + | D = –AB, E = +AC, F = +BC |
| 8 | + + + | D = +AB, E = +AC, F = +BC |

principal fraction 은 항상 마지막(모두 +). 두 번째 fraction 예(3요인 full factorial + D=AB, E=−AC, F=−BC):

| Run | A | B | C | D = AB | E = –AC | F = –BC |
|---|---|---|---|---|---|---|
| 1 | – | – | – | + | – | – |
| 2 | + | – | – | – | + | – |
| 3 | – | + | – | – | – | + |
| 4 | + | + | – | + | + | + |
| 5 | – | – | + | + | + | + |
| 6 | + | – | + | – | – | + |
| 7 | – | + | + | – | + | – |
| 8 | + | + | + | + | – | – |

5요인 8런(1/4 fraction)의 4개 fraction 순서: `D = –AB E = –AC` / `D = AB E = –AC` / `D = –AB E = AC` / `D = AB E = AC`(= principal). 모든 요인 high 인 런은 principal 에만 있고 3번째 fraction 에는 없음.

---

## 3. 설계 생성 알고리즘

### 3.1 생성자(design generator)로 fraction 구성 (what-is-a-design-generator, ec5a63ac)
1. base 요인들의 full factorial 을 **표준(Yates) 순서**로 만든다: 첫 요인이 가장 빨리 바뀜(−,+,−,+…), 두 번째는 2런마다, 세 번째는 4런마다….
2. 추가 요인 = 생성자에 적힌 요인 열들의 곱. 예 D = ABC:

| A | B | C | D = ABC |
|---|---|---|---|
| –1 | –1 | –1 | –1 |
| +1 | –1 | –1 | +1 |
| –1 | +1 | –1 | +1 |
| +1 | +1 | –1 | –1 |
| –1 | –1 | +1 | +1 |
| +1 | –1 | +1 | –1 |
| –1 | +1 | +1 | –1 |
| +1 | +1 | +1 | +1 |

3. 기본 생성자는 "해당 요인 수·런 수에서 **가장 높은 해상도**를 주는 것"(2.2 표). 음의 생성자(D = −AB)는 fraction 번호 선택과 동일한 효과(2.6).

### 3.2 정의관계(defining relation)와 alias 구조 계산 (what-is-a-defining-relation, ec5a63ac "Defining relation")
- 정의관계 = fraction 을 정의하기 위해 상수로 고정된 모든 단어(word)의 집합. 생성자 D=AB, E=AC → `I = ABD = ACE = BCDE` (생성자 단어들과 그 곱들 전체; 1/4 fraction → 3개 단어 + I).
- 규칙: 같은 문자끼리 곱하면 I (A×A = I), I×A = A.
- 어떤 항의 alias = 그 항 × 정의관계의 각 단어, 제곱 문자 제거. 예 BC: (BC)(ABD)=ACD, (BC)(ACE)=ABE, (BC)(BCDE)=DE → `BC + DE + ABE + ACD`.
- 알고리즘 결과(5요인 1/4):
```
Defining Relation:  I = ABD = ACE = BCDE
Alias Structure
I + ABD + ACE + BCDE
A + BD + CE + ABCDE
B + AD + CDE + ABCE
C + AE + BDE + ABCD
D + AB + BCE + ACDE
E + AC + BCD + ABDE
BC + DE + ABE + ACD
BE + CD + ABC + ADE
```
- 행 순서: I 행 → 주효과(알파벳 순) → 2-factor 교호작용(아직 등장하지 않은 것, 알파벳 순) → …. 각 행 내부는 **차수 오름차순, 같은 차수는 알파벳 순**(예: `A + BD + CE + ABCDE`, `AB + CE + ACDF + BDEF`). 행 수(I 제외) = 런 수 − 1 (saturated model 항 수, 3.13).
- 열 I 는 코드화 단위에서 항상 1의 열이므로 I = ABD 이면 A·B·D 열의 곱이 1의 열.
- 블록이 있으면 I 행 다음에 `Blk1 = AB + CDE`, `Blk2 = AC + BDE`, `Blk3 = BC + ADE` 형식의 블록 행이 들어가고, 블록과 교락된 2-way 항(AB, AC, BC)은 이후 행에서 빠짐(6f11c314).
- 9요인 32런(1/16) 예의 정의관계(15 단어): `I = ABCDF = ABCEG = ABDEH = CDEJ = DEFG = CEFH = ABEFJ = CDGH = ABDGJ = ABCHJ = ABFGH = CFGJ = DFHJ = EGHJ = ABCDEFGHJ` — 생성자 4개 → 2^4−1 = 15 단어, 생성자 단어 → 두 개씩 곱 → 세 개씩 곱 → 네 개 곱 순으로 나열(04b9e5df).

### 3.3 해상도(resolution) (what-is-design-resolution, ec5a63ac, f7581e96)
- 블록 없는 설계: **정의관계에서 가장 짧은 단어의 길이**. `I = ABD = ACE = BCDE` → III.
- III: 주효과끼리는 aliased 아님, 주효과 ↔ 2FI aliased. IV: 주효과 ↔ 3FI, 일부 2FI ↔ 2FI. V: 2FI ↔ 3FI, 주효과 ↔ 4FI.
- 블록이 있으면 Design Summary 라벨이 `Resolution with blocks:` 로 바뀌고 값은 블록 생성자까지 고려(2.2 표의 괄호 뒤 숫자). 블록이 2-way 와 교락되면 `* NOTE * Blocks are confounded with two-way interactions.`, 주효과가 2-way 와 교락되면(res III) `* NOTE * Some main effects are confounded with two-way interactions.` 를 Design Summary 아래에 출력.
- 블록은 해상도를 낮출 수 있고 fold 는 높일 수 있음. 6요인 1/4 16런: 블록 1 → IV, 블록 4 → III, 블록 4 + replicates 2 → IV ("블록이 부분적으로 replicate 로부터 생성되므로").
- Full factorial 의 Resolution 은 2.2 표에서 `-`; Design Summary 에서 어떻게 표기되는지는 문서에 없음(분할구 full 예제는 "All terms are free from aliasing." 출력).

### 3.4 Fraction 번호 (097ff548, ec5a63ac "Fraction number", fba51f9d)
- 1/2^p fraction 은 2^p 개 fraction 이 있고 번호는 Yates 순서로 생성자 부호를 (−,−,…) 부터 (+,+,…) 까지 매김(2.6). principal = 최대 번호 = 분모.
- `Fraction number` 는 사용자가 변경했을 때만 Design Summary 에 표시("Minitab only displays the fraction number when you change the fraction") — 표시 위치/라벨 형식은 문서에 없음.
- 모든 fraction 에서 추정 가능한 항은 동일.

### 3.5 블록 생성자와 블록 배정 (ec5a63ac "Block generators", 6b4d4bea, 2.2 표)
- replicate 수가 블록 수의 배수가 아니면 블록 생성자를 사용. 블록 수 = 2^p (p = 블록 생성자 수). 기본 블록 생성자는 2.2 표(최고 해상도).
- 배정: 표준 순서 설계에서 블록 생성자 열(예 AB)의 값을 계산 → 같은 값끼리 같은 블록. 예 4요인 1/2, 2 blocks, AB:

| A | B | C | D | AB | Blocks |
|---|---|---|---|---|---|
| –1 | –1 | –1 | –1 | +1 | 1 |
| +1 | –1 | –1 | +1 | –1 | 2 |
| –1 | +1 | –1 | +1 | –1 | 2 |
| +1 | +1 | –1 | –1 | +1 | 1 |
| –1 | –1 | +1 | +1 | +1 | 1 |
| +1 | –1 | +1 | –1 | –1 | 2 |
| –1 | +1 | +1 | –1 | –1 | 2 |
| +1 | +1 | +1 | +1 | +1 | 1 |

→ **AB = +1 이 Block 1, −1 이 Block 2**(첫 런(모두 −1)이 Block 1). 이후 블록별로 묶고 **블록 순서와 블록 내 런 순서를 랜덤화**. 랜덤화 후 예(문서):

| A | B | C | D | AB | Blocks |
|---|---|---|---|---|---|
| +1 | –1 | +1 | –1 | –1 | 2 |
| –1 | +1 | +1 | –1 | –1 | 2 |
| –1 | +1 | –1 | +1 | –1 | 2 |
| +1 | –1 | –1 | +1 | –1 | 2 |
| +1 | +1 | +1 | +1 | +1 | 1 |
| +1 | +1 | –1 | –1 | +1 | 1 |
| –1 | –1 | +1 | +1 | +1 | 1 |
| –1 | –1 | –1 | –1 | +1 | 1 |

- 두 개 이상 생성자(예 AB, AC → 4 blocks)일 때 (+,+),(+,−),(−,+),(−,−) 조합과 블록 번호 1~4 의 대응 규칙은 문서에 없음. 다만 예제 6f11c314(5요인 16런, E=ABCD, 블록 생성자 AB, AC)의 워크시트 첫 6행에서: StdOrder 4 (A+,B+,C+,D−,E−: AB=+,AC=+) → Block 1; StdOrder 2 (A−,B−,C+,D−,E−: AB=+,AC=−)… 도 Block 1 로 보이므로 단순 부호 조합이 아님 — **문서만으로 확정 불가**. 블록 배정 열에는 설계 (E=ABCD 포함) 전체를 고려한 혼합 규칙이 있을 수 있음. (구현 시 주의)
  - 정정: StdOrder 2 는 표준 순서상 A=+1,B=−1,C=−1,D=−1 이어야 하나 표에는 A=−1,B=−1,C=1 로 적혀 있음 → StdOrder 가 "블록 정렬 후 재번호" 되었을 가능성. 즉 **StdOrder 는 블록별로 재정렬된 뒤 1부터 매겨진 번호**일 수 있음(예제 표: Block 1 에 StdOrder 1,2,4,8 / Block 2 에 7,12). 문서에 명시 없음.
- 분할구: whole plot generators 로 whole plot 을 구성(예 `Whole Plot Generators: A`).
- 블록이 있는 설계를 fold 하면 블록당 런 수가 2배, **블록 생성자는 그대로**.

### 3.6 중앙점 추가 규칙 (how-minitab-adds-center-points, ae688ce8, f7581e96, 65794334, a2f1adf2)
2-level factorial:
- 모든 요인 숫자: 블록 없음 → 지정 수만큼 추가 / 블록 있음 → **각 블록에** 지정 수만큼 추가.
- 모든 요인 텍스트: **중앙점 추가 불가**.
- 숫자+텍스트 혼합(pseudo-center points): 텍스트 요인 수준의 **모든 조합마다** 지정 수 추가 → Q개의 텍스트 요인이면 **2^Q 배**. 블록이 있으면 각 블록마다 2^Q 배. 예: 2^3, A·C 숫자(0/10, .2/.3), B 텍스트, 3 CP 지정 → 6개:

| Factor A | Factor B | Factor C |
|---|---|---|
| 5 | present | .25 |
| 5 | present | .25 |
| 5 | present | .25 |
| 5 | absent | .25 |
| 5 | absent | .25 |
| 5 | absent | .25 |

  2^5, 텍스트 3개, 2 blocks, 2 CP/block → 8×2 = 16 개를 **각 블록에** 추가. 출력 NOTE: `* NOTE * The number of centerpoints specified is doubled for each categorical factor. For Q categorical factors, the result is 2^Q times as many centerpoints.`
- replicates 는 중앙점 수를 늘리지 않음(블록 수를 늘릴 때만).
- Design Summary 의 `Center pts (total):` 은 블록·텍스트 요인 배수를 모두 반영한 총수. Runs = base runs × replicates(+fold) + total center points.
- 분할구: 중앙점 불가.
- PB: `Number of center points per replicate` — **replicate 마다 추가**(3 CP × 2 rep = 6), 블록 여부 무관. 텍스트 요인 배수 규칙 동일.
- DSD: 숫자만 → replicate 당 1 CP(base 런 수에 포함, 2.3 표), 텍스트 요인 1개 이상 → replicate 당 2 CP(런 1개 추가). 사용자 지정 불가.
- 중앙점의 요인 값: 숫자 요인은 (low+high)/2 (100/200 → 150, 5/10 → 7.5), 설계표에는 `0`, 워크시트 CenterPt=0.

### 3.7 분석 시 중앙점 처리 (how-minitab-h_2a28cf90)
- 중앙점 항을 모형에 포함: 꼭짓점으로 평면 적합 후 중앙점을 별도 적합 → 곡면성 검정 가능하나 설계 외 점 예측 불가.
- 포함하지 않음: 모든 점으로 하나의 평면 적합 → 곡면성 검정 불가, 예측 가능.

### 3.8 접기(folding) (what-is-folding, 097ff548, ec5a63ac "Folded on factors", fold-design)
- 워크시트 데이터를 복제해 **아래에 추가**, 접는 요인 열의 부호 반전. 다른 요인은 그대로.
- 3요인 4런 예:

| 원본 | A | B | C |
|---|---|---|---|
| | – | – | + |
| | + | – | – |
| | – | + | – |
| | + | + | + |

Folded on all factors (4런 추가, 모두 반전):
```
– – +
+ – –
– + –
+ + +
+ + –
– + +
+ – +
– – –
```
Folded on factor A (A 만 반전):
```
– – +
+ – –
– + –
+ + +
+ – +
– – –
+ + –
– + +
```
- 정의관계: 전체 접기 → 홀수 글자 단어 삭제(`I + ABD + ACE + BCDE` → `I + BCDE`). 단일 요인 A 접기 → A 포함 단어 삭제(Options 문서는 결과를 `I + ACE` 라고 적었으나 what-is-folding 는 두 경우 모두 `I + BCDE` 로 표기 — 규칙대로면 A 접기 결과는 `I + BCDE`; 097ff548 의 `I + ACE` 는 원문 오류로 보임, 구현은 규칙 기준).
- 정의관계가 줄지 않으면(모든 단어 짝수 등) replicate 만 추가되는 것이므로 **오류/경고 후 설계 미생성**.
- Res III → 전체 접기 → Res IV. 단일 요인 접기 → 그 요인과 그 요인의 2FI 가 다른 주효과·2FI 와 분리.
- Summary table 의 Design Generators 는 접기 전 것, Defining relation 은 접은 후 것. Design Summary 에 `Folded on factors` 항목(all / 단일 요인) 표시 — 정확한 라벨 문자열은 문서에 없음.
- PB 도 fold 가능(split-plot 도 Modify Design 에서 fold 가능).
- Key results: "Each replicate or fold adds runs equal to the number of corner points in the base design."

### 3.9 분할구(split-plot) 구조 (split-plot-de_2f9547fe, 878cf6c2, 02a08c7c)
- HTC 요인 수준을 여러 런 동안 고정한 묶음 = whole plot; 그 안에서 ETC 요인 조합 = subplot. whole plot 순서와 whole plot 내 subplot 순서 모두 랜덤화(Randomize 는 "runs are randomized within whole plots, which may be within blocks").
- 예제: 4요인, HTC 1 (A), `Full factorial with 2 whole plots and 8 subplots`, whole-plot replicates 2 → Whole plots 4, Runs per whole plot 8, Runs 32, Blocks 1, Subplot replicates 1. `Whole Plot Generators: A`.
- 워크시트/설계표에 `WP` 열(whole plot 번호) 추가; 설계표에서 같은 WP 의 런이 연속(WP 2 → 3 → 1 → 4 순으로 랜덤).
- 오차항(분석): whole plot 오차와 subplot 오차가 분리됨; 문서는 Block*A 등 ANOVA 모델 지정 방식 설명(분석 영역).

### 3.10 코드화/비코드화 단위 (coded-units-and-uncoded-units, 5e0c94bc, how-minitab-s_cfbcd3e7)
- 코드화: low=−1, high=+1, center=0(텍스트 요인도 −1/+1). 분석은 **항상 코드화 단위**로 수행.
- Factors 에서 수준을 지정했으면 워크시트에는 비코드화 값 표시, 지정 안 했으면 −1/+1 저장. Display Design 으로 전환 가능.
- 비코드화로 분석하면 직교성 상실 가능.

### 3.11 Plackett-Burman 구성 → 2.4 절. Res III(보통), 12/20/24런은 부분 교락. 분석은 Analyze Factorial Design.

### 3.12 DSD 특성 (definitive-screening-designs, which-standard-designs)
- Res IV 성격(주효과 ↔ 2FI 비교락), 연속 요인당 3수준(−, 0, +)으로 제곱항 추정 가능, 2FI 는 서로/제곱항과 부분 교락. 범주형 요인은 2수준만.
- 설계표에서 각 런은 **한 요인이 0 이고 나머지가 ±** 인 쌍(fold-over 쌍)과 전부 0 인 중앙점으로 구성(예제 표 참조). 생성 알고리즘(conference matrix 등)은 문서에 없음.

### 3.13 Saturated model 항 수 (determine-the_760d5ac6)
| Model | 항 수 |
|---|---|
| 중앙점·블록 없음 | base design 의 고유 corner points 수 − 1 |
| 중앙점 있음, 블록 없음 | 고유 corner points 수 |
블록 있으면 (블록 수 − 1) df 와 중앙점 1 df 를 뺀 나머지. 간단히 Alias Structure 의 행 수(I 제외)를 세고 중앙점 있으면 +1.

### 3.14 오차 분할(참고, 분석 영역) (how-error-is-partitioned)
pure error df = m(r−1) + (c−1) (m corner points, r replicates, c center points); curvature 1 df; lack-of-fit = 나머지.

### 3.15 주효과 계수(참고) (how-is-a-coefficient…)
균형 직교 설계에서 (−1,0,1) 코딩이면 수준 평균 − 전체 평균. 예시 표: Experience Advanced 16−12.92=3.08, Beginner −3.08, RoadType Dirt 4.58, Gravel −0.42, Paved −4.17.

### 3.16 Optimality(참고) (optimality-criteria): D-optimality, Distance-based(GFF 에서는 불가). 요인 설계 생성 자체에는 사용되지 않음.

---

## 4. 워크시트 열과 저장되는 설계 정보

### 4.1 생성 시 예약 열 (how-minitab-s_cfbcd3e7, how-minitab-stores-design-information, f7581e96)
| 열 | 이름 | 내용 |
|---|---|---|
| C1 | **StdOrder** | 표준(Yates) 순서 — 비랜덤 순서 |
| C2 | **RunOrder** | 실험 수행 순서(랜덤). Residuals vs order 그래프에 사용 |
| C3 | **CenterPt** (2-level factorial) / **PtType** (Plackett-Burman, definitive screening, split-plot, general full factorial, response surface, mixture) | 1 = corner point, 0 = center point, −1 = axial point, 2 = edge point(DSD edge midpoint, Box-Behnken), 3 = triple blend(mixture) |
| C4 | **Blocks** | 블록 없으면 모두 1 |
| C5~Cn | 요인/성분 열 | 이름 지정 안 하면 알파벳(I 제외). 수준 지정 안 하면 −1/+1 |
| (split-plot) | **WP** | 예제 설계표의 열. 워크시트상 정확한 열 위치/이름은 문서에 없음(설계표 헤더는 `Run | Blk | WP`) |

- 예제 워크시트 헤더: `StdOrder | RunOrder | CenterPt | Blocks | A | B | …` (ed4326a1, 6f11c314). All statistics 의 한 예시는 `StdOrder | RunOrder | Blocks | CenterPt | …` 순서이지만(ec5a63ac "Runs"), 저장 규칙 문서(C3=CenterPt, C4=Blocks)와 다른 모든 예시는 CenterPt 가 먼저.
- 점 유형 표(what-points-can-i-use):

| Point | Screening | Factorial | Response Surface | Mixture |
|---|---|---|---|---|
| 0 | center point | center point | center point | centroid |
| 1 | corner point | corner point (cube point) | cube point (corner point) | vertex |
| −1 | - | - | axial point | axial point |
| 2 | edge midpoint*(DSD만) | - | edge midpoint**(Box-Behnken만) | edge midpoint (double blend) |
| 3 | - | - | - | triple blend |

### 4.2 설계 객체 규칙 (how-minitab-stores-design-information)
- 설계 열은 **삭제·이동 불가**. 마지막 설계 열 뒤에 반응·공변량 등 자유 입력.
- 런 삭제 가능(적합 불가 항은 자동 제거), 런 추가 가능(StdOrder/RunOrder/CenterPt/PtType/Blocks/요인 열 길이 동일해야 함; StdOrder/RunOrder 는 임의 숫자 가능—정렬에만 사용).
- 수준 값 변경은 Modify Design 으로(직접 타이핑하면 분석 오류). botched run 은 개별 셀 수정 가능. 요인 타입(numeric↔text) 변경 불가.
- 요인 추가는 워크시트에 열 추가 후 Define Custom Design.
- 손상 시 Define Custom Factorial Design 으로 재정의.

### 4.3 DOE design matrix (what-does-min_5ae32a40)
회귀용 X 행렬: 열 순서 = 상수(1) → covariates(각 1열) → factors(요인당 df 개 열; 3수준 → 2열) → interactions(관련 요인 열 수의 곱; 2수준 2FI → 1열). 블록 k 개 → k−1 열.

---

## 5. 출력 형식

### 5.1 Design Summary 표 레이아웃
**2-level factorial(default/specify)** — 3행 × 6칸(라벨/값 3쌍):
```
Design Summary
Factors: | 6 | Base Design: | 6, 16 | Resolution: | IV
Runs:    | 16 | Replicates: | 1 | Fraction: | 1/4
Blocks:  | 1 | Center pts (total): | 0 | |
```
- `Base Design:` = "요인 수, base 런 수". 블록 ≥2 이면 3번째 열 라벨 `Resolution with blocks:`.
- 표 아래 줄: `* NOTE * …`(해당 시) → `Design Generators: E = ABC, F = BCD` → (블록 시) `Block Generators: AB, AC` → (Results 에서 선택 시) `Defining Relation:  I = …` → `Alias Structure` (또는 `Alias Structure (up to order 2)`) → `Design Table (randomized)`.
- 문서에 나온 Design Summary 변형들(f7581e96, ec5a63ac):
  - `Factors: 3 | Base Design: 3, 4 | Resolution: III / Runs: 10 | Replicates: 2 | Fraction: 1/2 / Blocks: 1 | Center pts (total): 2` (4×2 + 2 = 10)
  - `Factors: 6 | 6, 16 | Resolution with blocks: III / Runs: 16 | Replicates: 1 | 1/4 / Blocks: 4 | 0`
  - `Factors: 6 | 6, 16 | Resolution with blocks: IV / Runs: 32 | Replicates: 2 | 1/4 / Blocks: 4 | 0`
  - `Factors: 6 | 6, 16 | Resolution: IV / Runs: 18 | 1 | 1/4 / Blocks: 1 | Center pts (total): 2`
  - `Factors: 6 | 6, 16 | Resolution: IV / Runs: 20 | 1 | 1/4 / Blocks: 1 | Center pts (total): 4` (텍스트 요인 1개, CP 2 지정)
  - `Factors: 5 | 5, 8 | Resolution: III / Runs: 8 | 1 | 1/4 / Blocks: 1 | 0` + `* NOTE * Some main effects are confounded with two-way interactions.` + `Design Generators: D = AB, E = AC`
  - `Factors: 9 | 5, 32 | Resolution: IV / Runs: 32 | 1 | Fraction: 1/16 / Blocks: 1 | 0` (specify generators; Base Design 은 base 요인 수 5)

**Split-plot** — 4행 × 4칸:
```
Factors: | 4 | Whole plots: | 4
Hard-to-change: | 1 | Runs per whole plot: | 8
Runs: | 32 | Whole-plot replicates: | 2
Blocks: | 1 | Subplot replicates: | 1
```
이어서 `Hard-to-change factors: A` / `Whole Plot Generators: A` / `All terms are free from aliasing.` / `Design Table (randomized)`.

**Plackett-Burman / General Full Factorial / DSD** — 3행 × 4칸:
```
Factors: | 9 | Replicates: | 1
Base runs: | 15 | Total runs: | 15
Base blocks: | 1 | Total blocks: | 1
```
- PB: 아래에 `Center points: 3` (Base runs 는 중앙점 포함 15).
- GFF: 아래에 `Number of levels: 3, 3, 3`.
- DSD: 표 안에 빈 행 1개 후 `Center points: | 2` 행 포함(Base runs 17 은 CP 1 포함; 2 replicates → Total runs 34, Center points 2).

### 5.2 Alias Structure 레이아웃
- 한 줄에 한 alias 집합, `+` 로 연결, 차수 오름차순·알파벳 순. 첫 줄은 `I + …`.
- `Interactions up through order 2` 선택 시 제목이 `Alias Structure (up to order 2)` 가 되고 각 줄에 2차 이하 항만 남김; 혼자 남는 항은 단독 표기(`A`, `AB` …) (04b9e5df).
- 블록: `Blk1 = AB + CDE` 형식의 줄이 I 다음에 옴.
- Full factorial/분할구 full: `All terms are free from aliasing.`

### 5.3 Design Table 레이아웃
- 제목 `Design Table (randomized)` (Randomize 해제 시 제목이 어떻게 되는지는 문서에 없음).
- 열: `Run | Blk | A | B | …` (블록 없어도 `Blk` 열 표시—PB·GFF·DSD·2-level 32런 예). 9요인 specify 예제에서는 `Run | A | … | J` 로 **Blk 열 없음**(Blocks 1). 분할구: `Run | Blk | WP | A…`.
- 값: `+` high, `-` low, `0` center. GFF 는 수준 번호 1,2,3. DSD 는 −/0/+.
- 요인 문자는 생성 시 입력 순서의 A,B,C,…(I 제외).

### 5.4 예제 설계표 전문 (테스트 정답용)

#### (a) 6요인 1/4 fraction, 기본 생성자 — 워크시트 처음 6행 (ed4326a1)
Design Generators: E = ABC, F = BCD
```
Alias Structure
I + ABCE + ADEF + BCDF
A + BCE + DEF + ABCDF
B + ACE + CDF + ABDEF
C + ABE + BDF + ACDEF
D + AEF + BCF + ABCDE
E + ABC + ADF + BCDEF
F + ADE + BCD + ABCEF
AB + CE + ACDF + BDEF
AC + BE + ABDF + CDEF
AD + EF + ABCF + BCDE
AE + BC + DF + ABCDEF
AF + DE + ABCD + BCEF
BD + CF + ABEF + ACDE
BF + CD + ABDE + ACEF
ABD + ACF + BEF + CDE
ABF + ACD + BDE + CEF
```
| StdOrder | RunOrder | CenterPt | Blocks | A | B | C | D | E | F |
|---|---|---|---|---|---|---|---|---|---|
| 12 | 1 | 1 | 1 | 1 | −1 | −1 | −1 | 1 | −1 |
| 2 | 2 | 1 | 1 | −1 | 1 | 1 | −1 | −1 | −1 |
| 6 | 3 | 1 | 1 | −1 | −1 | −1 | −1 | −1 | −1 |
| 9 | 4 | 1 | 1 | −1 | −1 | −1 | 1 | −1 | 1 |
| 10 | 5 | 1 | 1 | −1 | −1 | 1 | −1 | 1 | 1 |
| 1 | 6 | 1 | 1 | 1 | 1 | −1 | 1 | −1 | −1 |

(주의: 이 표의 StdOrder 와 요인 부호가 표준 Yates 순서와 일치하지 않음 — 예: StdOrder 1 이 A=+1. 문서 예시 값 그대로 옮김.)

#### (b) 5요인 1/2 fraction, 4 blocks (6f11c314)
```
Design Summary
Factors: 5 | Base Design: 5, 16 | Resolution with blocks: III
Runs: 16 | Replicates: 1 | Fraction: 1/2
Blocks: 4 | Center pts (total): 0
* NOTE * Blocks are confounded with two-way interactions.
Design Generators: E = ABCD
Block Generators: AB, AC
Alias Structure
I + ABCDE
Blk1 = AB + CDE
Blk2 = AC + BDE
Blk3 = BC + ADE
A + BCDE
B + ACDE
C + ABDE
D + ABCE
E + ABCD
AD + BCE
AE + BCD
BD + ACE
BE + ACD
CD + ABE
CE + ABD
DE + ABC
```
| StdOrder | RunOrder | CenterPt | Blocks | A | B | C | D | E |
|---|---|---|---|---|---|---|---|---|
| 4 | 1 | 1 | 1 | 1 | 1 | 1 | −1 | −1 |
| 2 | 2 | 1 | 1 | −1 | −1 | 1 | −1 | −1 |
| 8 | 3 | 1 | 1 | 1 | 1 | −1 | 1 | −1 |
| 1 | 4 | 1 | 1 | −1 | −1 | −1 | −1 | 1 |
| 7 | 5 | 1 | 2 | 1 | 1 | 1 | 1 | 1 |
| 12 | 6 | 1 | 2 | −1 | −1 | 1 | 1 | 1 |

#### (c) 9요인 32런 specify generators (04b9e5df)
Base: 5요인 Full factorial; Generators `F = ABCD G = ABCE H = ABDE J = CDE`; Results: 4개 모두 + up through order 2.
```
Design Summary
Factors: 9 | Base Design: 5, 32 | Resolution: IV
Runs: 32 | Replicates: 1 | Fraction: 1/16
Blocks: 1 | Center pts (total): 0
Design Generators: F = ABCD, G = ABCE, H = ABDE, J = CDE
Defining Relation:  I = ABCDF = ABCEG = ABDEH = CDEJ = DEFG = CEFH = ABEFJ = CDGH = ABDGJ = ABCHJ = ABFGH = CFGJ = DFHJ = EGHJ = ABCDEFGHJ
Alias Structure (up to order 2)
I
A
B
C
D
E
F
G
H
J
AB
AC
AD
AE
AF
AG
AH
AJ
BC
BD
BE
BF
BG
BH
BJ
CD + EJ + GH
CE + DJ + FH
CF + EH + GJ
CG + DH + FJ
CH + DG + EF
CJ + DE + FG
DF + EG + HJ
```
Design Table (randomized)
| Run | A | B | C | D | E | F | G | H | J |
|---|---|---|---|---|---|---|---|---|---|
| 1 | + | - | - | - | - | - | - | - | - |
| 2 | + | + | - | + | - | - | + | - | + |
| 3 | - | - | - | - | - | + | + | + | - |
| 4 | + | - | - | - | + | - | + | + | + |
| 5 | - | - | - | + | - | - | + | - | + |
| 6 | + | - | + | - | + | + | - | + | - |
| 7 | - | + | + | + | + | - | - | - | + |
| 8 | + | - | - | + | + | + | + | - | - |
| 9 | + | + | + | + | + | + | + | + | + |
| 10 | + | + | + | - | + | - | + | - | - |
| 11 | - | + | - | - | + | - | + | + | + |
| 12 | + | + | + | + | - | + | - | - | - |
| 13 | + | - | - | + | - | + | - | + | + |
| 14 | + | + | + | - | - | - | - | + | + |
| 15 | + | + | - | - | + | + | - | - | + |
| 16 | - | + | - | - | - | - | - | - | - |
| 17 | + | - | + | + | + | - | - | - | + |
| 18 | - | + | - | + | + | + | + | - | - |
| 19 | - | - | + | - | - | - | - | + | + |
| 20 | - | + | - | + | - | + | - | + | + |
| 21 | - | + | + | + | - | - | + | + | - |
| 22 | - | - | + | + | + | + | + | + | + |
| 23 | + | - | + | + | - | - | + | + | - |
| 24 | - | - | + | - | + | - | + | - | - |
| 25 | - | - | - | - | + | + | - | - | + |
| 26 | + | + | - | + | + | - | - | + | - |
| 27 | - | + | + | - | - | + | + | - | + |
| 28 | - | + | + | - | + | + | - | + | - |
| 29 | + | + | - | - | - | + | + | + | - |
| 30 | - | - | - | + | + | - | - | + | - |
| 31 | + | - | + | - | - | + | + | - | + |
| 32 | - | - | + | + | - | + | - | - | - |

#### (d) 5요인 1/4 fraction(8런) — Alias (ec5a63ac, f7581e96)
```
Design Summary
Factors: 5 | Base Design: 5, 8 | Resolution: III
Runs: 8 | Replicates: 1 | Fraction: 1/4
Blocks: 1 | Center pts (total): 0
* NOTE * Some main effects are confounded with two-way interactions.
Design Generators: D = AB, E = AC
Defining Relation:  I = ABD = ACE = BCDE
Alias Structure
I + ABD + ACE + BCDE
A + BD + CE + ABCDE
B + AD + CDE + ABCE
C + AE + BDE + ABCD
D + AB + BCE + ACDE
E + AC + BCD + ABDE
BC + DE + ABE + ACD
BE + CD + ABC + ADE
```

#### (e) 5요인 16런 × 2 replicates, 4 blocks — Design Table (ec5a63ac "Design table")
"16 runs in 4 blocks, with 32 total runs"; 런 31 에서 모두 + → principal fraction.
| Run | Blk | A | B | C | D | E |
|---|---|---|---|---|---|---|
| 1 | 2 | + | + | + | - | - |
| 2 | 2 | - | - | + | - | - |
| 3 | 2 | + | + | - | + | - |
| 4 | 2 | - | - | - | - | + |
| 5 | 2 | + | + | + | + | + |
| 6 | 2 | - | - | + | + | + |
| 7 | 2 | + | + | - | - | + |
| 8 | 2 | - | - | - | + | - |
| 9 | 3 | + | - | + | - | + |
| 10 | 3 | - | + | + | + | - |
| 11 | 3 | - | + | - | - | - |
| 12 | 3 | + | - | - | + | + |
| 13 | 3 | - | + | + | - | + |
| 14 | 3 | + | - | + | + | - |
| 15 | 3 | + | - | - | - | - |
| 16 | 3 | - | + | - | + | + |
| 17 | 1 | + | - | - | - | - |
| 18 | 1 | - | + | + | - | + |
| 19 | 1 | + | - | + | + | - |
| 20 | 1 | - | + | - | + | + |
| 21 | 1 | - | + | + | + | - |
| 22 | 1 | + | - | - | + | + |
| 23 | 1 | + | - | + | - | + |
| 24 | 1 | - | + | - | - | - |
| 25 | 4 | - | - | + | - | - |
| 26 | 4 | - | - | + | + | + |
| 27 | 4 | + | + | + | - | - |
| 28 | 4 | - | - | - | + | - |
| 29 | 4 | - | - | - | - | + |
| 30 | 4 | + | + | - | - | + |
| 31 | 4 | + | + | + | + | + |
| 32 | 4 | + | + | - | + | - |

(블록 2·4 는 AB=+ 인 런, 블록 1·3 은 AB=− 인 런 — 블록 생성자 AB 와 일치; 각 블록 8런 중 같은 조합 2번 = 2 replicates.)

#### (f) 4요인 분할구, HTC=A, whole-plot replicates 2 (02a08c7c)
| Run | Blk | WP | A | B | C | D |
|---|---|---|---|---|---|---|
| 1 | 1 | 2 | + | + | + | - |
| 2 | 1 | 2 | + | - | + | - |
| 3 | 1 | 2 | + | + | - | + |
| 4 | 1 | 2 | + | - | - | - |
| 5 | 1 | 2 | + | + | + | + |
| 6 | 1 | 2 | + | - | + | + |
| 7 | 1 | 2 | + | + | - | - |
| 8 | 1 | 2 | + | - | - | + |
| 9 | 1 | 3 | - | - | + | - |
| 10 | 1 | 3 | - | + | + | + |
| 11 | 1 | 3 | - | + | - | - |
| 12 | 1 | 3 | - | - | - | + |
| 13 | 1 | 3 | - | + | + | - |
| 14 | 1 | 3 | - | - | + | + |
| 15 | 1 | 3 | - | - | - | - |
| 16 | 1 | 3 | - | + | - | + |
| 17 | 1 | 1 | - | - | - | - |
| 18 | 1 | 1 | - | + | + | - |
| 19 | 1 | 1 | - | - | + | + |
| 20 | 1 | 1 | - | + | - | + |
| 21 | 1 | 1 | - | + | + | + |
| 22 | 1 | 1 | - | - | - | + |
| 23 | 1 | 1 | - | - | + | - |
| 24 | 1 | 1 | - | + | - | - |
| 25 | 1 | 4 | + | - | + | - |
| 26 | 1 | 4 | + | - | + | + |
| 27 | 1 | 4 | + | + | + | - |
| 28 | 1 | 4 | + | - | - | + |
| 29 | 1 | 4 | + | - | - | - |
| 30 | 1 | 4 | + | + | - | - |
| 31 | 1 | 4 | + | + | + | + |
| 32 | 1 | 4 | + | + | - | + |

(WP 1·3 = A−, WP 2·4 = A+.)

#### (g) PB 9요인 12런 + 3 CP (21568bf0)
| Run | Blk | A | B | C | D | E | F | G | H | J |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | + | + | + | - | + | + | - | + | - |
| 2 | 1 | + | - | + | - | - | - | + | + | + |
| 3 | 1 | - | - | + | + | + | - | + | + | - |
| 4 | 1 | + | - | + | + | - | + | - | - | - |
| 5 | 1 | - | + | - | - | - | + | + | + | - |
| 6 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 7 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 8 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 9 | 1 | - | - | - | - | - | - | - | - | - |
| 10 | 1 | - | - | - | + | + | + | - | + | + |
| 11 | 1 | - | + | + | + | - | + | + | - | + |
| 12 | 1 | + | + | - | + | + | - | + | - | - |
| 13 | 1 | - | + | + | - | + | - | - | - | + |
| 14 | 1 | + | - | - | - | + | + | + | - | + |
| 15 | 1 | + | + | - | + | - | - | - | + | + |

(검증 힌트: 12런 생성열 `+ + - + + + - - - + -` 의 순환 행렬 11열 중 처음 9열 + 마지막 모두 − 행(Run 9).)

#### (h) GFF 3요인 3수준 (8ea1dee7)
Designs: Name=Website/Product/Message style, Number of Levels 3 each; Factors: Type=Text, Level Values = News/Social Media/Sports, Car/Video Game/Medicine, "You know you should."/"Just the facts."/"That is awesome!".
| Run | Blk | A | B | C |
|---|---|---|---|---|
| 1 | 1 | 1 | 3 | 3 |
| 2 | 1 | 1 | 1 | 1 |
| 3 | 1 | 2 | 2 | 2 |
| 4 | 1 | 1 | 2 | 3 |
| 5 | 1 | 2 | 3 | 3 |
| 6 | 1 | 3 | 3 | 2 |
| 7 | 1 | 3 | 1 | 3 |
| 8 | 1 | 3 | 3 | 3 |
| 9 | 1 | 3 | 1 | 2 |
| 10 | 1 | 2 | 2 | 3 |
| 11 | 1 | 2 | 1 | 3 |
| 12 | 1 | 1 | 3 | 1 |
| 13 | 1 | 1 | 2 | 2 |
| 14 | 1 | 2 | 3 | 1 |
| 15 | 1 | 1 | 1 | 2 |
| 16 | 1 | 3 | 3 | 1 |
| 17 | 1 | 3 | 2 | 1 |
| 18 | 1 | 1 | 1 | 3 |
| 19 | 1 | 1 | 3 | 2 |
| 20 | 1 | 2 | 1 | 2 |
| 21 | 1 | 3 | 2 | 3 |
| 22 | 1 | 2 | 1 | 1 |
| 23 | 1 | 2 | 3 | 2 |
| 24 | 1 | 2 | 2 | 1 |
| 25 | 1 | 3 | 2 | 2 |
| 26 | 1 | 1 | 2 | 1 |
| 27 | 1 | 3 | 1 | 1 |

(설계표는 코드화 수준 번호; 워크시트에는 요인 이름과 수준 이름 표시.)

#### (i) DSD 8요인, 2 replicates (DSD example, a1d7bcef)
| Run | Blk | A | B | C | D | E | F | G | H |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | - | + | - | - | + | + | - | 0 |
| 2 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 3 | 1 | 0 | - | - | - | - | - | - | - |
| 4 | 1 | + | - | - | + | 0 | + | - | + |
| 5 | 1 | - | + | + | - | 0 | - | + | - |
| 6 | 1 | + | - | 0 | - | + | + | + | - |
| 7 | 1 | + | + | - | + | + | - | 0 | - |
| 8 | 1 | - | - | + | - | - | + | 0 | + |
| 9 | 1 | - | + | + | - | 0 | - | + | - |
| 10 | 1 | + | 0 | + | - | + | - | - | + |
| 11 | 1 | - | 0 | - | + | - | + | + | - |
| 12 | 1 | 0 | + | + | + | + | + | + | + |
| 13 | 1 | - | + | - | - | + | + | - | 0 |
| 14 | 1 | - | - | - | 0 | + | - | + | + |
| 15 | 1 | + | + | + | 0 | - | + | - | - |
| 16 | 1 | + | - | - | + | 0 | + | - | + |
| 17 | 1 | 0 | + | + | + | + | + | + | + |
| 18 | 1 | + | - | 0 | - | + | + | + | - |
| 19 | 1 | + | + | - | - | - | 0 | + | + |
| 20 | 1 | - | + | 0 | + | - | - | - | + |
| 21 | 1 | 0 | - | - | - | - | - | - | - |
| 22 | 1 | - | - | - | 0 | + | - | + | + |
| 23 | 1 | + | - | + | + | - | - | + | 0 |
| 24 | 1 | + | 0 | + | - | + | - | - | + |
| 25 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 26 | 1 | - | 0 | - | + | - | + | + | - |
| 27 | 1 | + | + | - | + | + | - | 0 | - |
| 28 | 1 | - | - | + | - | - | + | 0 | + |
| 29 | 1 | - | + | 0 | + | - | - | - | + |
| 30 | 1 | - | - | + | + | + | 0 | - | - |
| 31 | 1 | - | - | + | + | + | 0 | - | - |
| 32 | 1 | + | + | + | 0 | - | + | - | - |
| 33 | 1 | + | + | - | - | - | 0 | + | + |
| 34 | 1 | + | - | + | + | - | - | + | 0 |

(17개 고유 런: 8쌍 fold-over + 중앙점 1; 각 런이 2번씩 등장. 문서 본문은 "The design includes 2 center points, which are runs 12 and 34" 라고 적었으나 표상 전부 0 인 런은 2, 25 — 원문 그대로 기록.)

#### (j) 기타 소형 예시 워크시트
- 2요인 Temperature/Time + CP (f7581e96): `StdOrder|RunOrder|CenterPt|Blocks|Temperature|Time|Strength` — (6,1,1,1,100,5), (2,2,1,1,200,10), (9,3,0,1,150,7.5), (5,4,1,1,200,10), (1,5,1,1,200,5).
- 2요인 full 4런 (ec5a63ac "Runs"): `StdOrder|RunOrder|Blocks|CenterPt|Factor 1|Factor 2|Response` — (1,4,1,1,−1,−1,11), (2,2,1,1,1,−1,12), (3,1,1,1,−1,1,10), (4,3,1,1,1,1,9).
- Display Design coded/uncoded (5e0c94bc): `StdOrder|RunOrder|Pressure|Primer|Adhesion` — coded (5,1,−1,−1,4.52),(1,2,1,−1,4.55),(12,3,−1,1,5.05),(3,4,1,1,4.69); uncoded Pressure 310/380, Primer One/Two.

---

## 6. Display Design / Modify Design (Stat > DOE > Display Design, Stat > DOE > Modify Design)

### 6.1 Display Design (overview, 5e0c94bc)
| 필드 | 선택지 |
|---|---|
| **Order for all points in the worksheet** | `Run order for design` (기본 표시) / `Standard order for design` (Yates). 설계 열 전부 정렬 + 행 수가 설계 행 수 이하인 비설계 열도 정렬. 더 긴 열은 정렬 불가 |
| **Columns not to reorder** (하위 대화상자) | 정렬하지 않을 비설계 열 지정 |
| **Units for factors** (screening/factorial/RS) | `Coded units` (−1/+1/0) / `Uncoded units` (Factors 또는 Low/High 에서 지정한 값). 분석은 항상 coded |
| Units for process variables (mixture) | Coded / Uncoded |
| Units for components (mixture) | Amount / Proportions(기본) / Pseudocomponents |

### 6.2 Modify Design — Modification 라디오 (ac33fb1b, overview)
공통: `Put modified design in a new worksheet` 체크 → 기존 워크시트 보존. `Specify…` 버튼으로 하위 대화상자.

| Modification | 적용 설계 | 하위 대화상자 필드 |
|---|---|---|
| **Modify factors** | screening, factorial, RS | 표: `Factor`(읽기 전용) / `Name` / `Type`(읽기 전용) / `Low` / `High`. 보통 −1/+1 기본 수준을 실제 값으로 바꿀 때 사용. 워크시트 직접 타이핑 금지(분석 오류) |
| Modify variables | mixture | 성분 이름, 공정변수 이름·low/high |
| **Replicate design** | screening, factorial, RS, mixture | **최대 10 replicates 추가**. 워크시트의 모든 런(중앙점 포함) 복제. 추가 replicate 는 새 블록 번호(예시: Blocks 2), StdOrder 는 이어서 번호(6~10), RunOrder 도 이어서. 복제 후 순서가 같으므로 **다시 Randomize 필요** |
| **Randomize design** | screening, factorial, RS, mixture | `Randomize entire design`(블록 내 런 랜덤화 후 런 순서 랜덤화; 반응 데이터 있으면 비권장; 분할구는 whole plot 내 랜덤화) / `Randomize just block` (블록 1개만, 블록 순서 유지; 순차 실험용) / `Base for random data generator`(양의 정수; 같은 base+같은 base design 순서 → 같은 결과) / `Display the design in run order`(미선택 시 RunOrder 열만 갱신하고 행 재배열 안 함) / `Columns not to reorder`(설계에 포함되지 않은 열만; 짧은 열은 빈 셀에 `*`) |
| **Renumber design** | 전부 | RunOrder 열을 현재 워크시트 행 번호와 같게. 하위 대화상자 없음(OK) |
| **Fold design** | factorial, PB, split-plot (**GFF 불가**) | `Fold on all factors` / `Fold just on factor`(요인 선택). 정의관계 축소 규칙은 3.8. 축소 안 되면 replicate 만 추가(오류) |
| **Add axial points** | 2-level factorial, PB (**모든 요인 numeric 일 때만**; split-plot·GFF 불가) | `Value of Alpha`: `Default (rotatable if possible)`(corner point 수 기반 α) / `Face Centered` (α=1) / `Custom`(코드화 단위 α 입력); `Add the following number of center points (to the axial block)`(양의 정수). 결과: 설계가 **central composite response surface design** 으로 바뀜 |
| DSD/RS/mixture | | 동일하되 fold·axial 없음 |

Add axial points 예시(3요인 Pressure 75/150, Injection 85/100, Cooling 25/50, CP 3 → 7런; 축점 6개 추가, 새 블록 2, CenterPt=−1):
| StdOrder | RunOrder | CenterPt | Blocks | Pressure | Injection | Cooling |
|---|---|---|---|---|---|---|
| 8 | 8 | −1 | 2 | 59.467 | 92.500 | 37.5000 |
| 9 | 9 | −1 | 2 | 165.533 | 92.500 | 37.5000 |
| 10 | 10 | −1 | 2 | 112.500 | 81.893 | 37.5000 |
| 11 | 11 | −1 | 2 | 112.500 | 103.107 | 37.5000 |
| 12 | 12 | −1 | 2 | 112.500 | 92.500 | 19.8223 |
| 13 | 13 | −1 | 2 | 112.500 | 92.500 | 55.1777 |
(기존 7행 StdOrder 4,1,2,6,7,3,5 / RunOrder 1~7 / CenterPt 1,1,1,0,0,1,0 / Blocks 1. α = (150−112.5)/… → 165.533 = 112.5 + 37.5×1.41421 → **α = √2 = 1.414(8 corner points 의 rotatable α = 8^(1/4))**.)

Replicate 예시(base 5행 StdOrder 5,1,4,2,3 → 추가 10,6,9,7,8 / Blocks 2 / RunOrder 6~10 / Temperature·Pressure 동일).

### 6.3 Define Custom 가 필요한 경우
워크시트에 설계가 있으나 Display/Modify 가 안 되면 먼저 Define Custom … Design 사용(overview).

---

## 7. Quick Designs (Stat > DOE > Quick Designs)

### 7.1 개요 (overview)
- Minitab 설계의 **부분집합**을 적은 질문으로 선택하게 하는 마법사. 포함: 일반 요인 설계(main+interaction), Screening(DSD), Response surface(main+interaction+quadratic), 2-level split-plot(HTC), Mixture, Taguchi.
- 1단계 질문 "How many factors do you want to study?": **2, 3, 4, 5, 6 또는 more**. 2~6 → 요인 수 선택(`Select a Two-Factor Design` … `Select a Six-Factor Design`), **7개 이상 → `Select a Screening Design`** (`Create an experiment with 7-48 factors`).
- 이 단계에서 "factors" 에 mixture components 포함.

### 7.2 K-factor designs (k-factor-designs)
2단계: 요인 유형 질문. 선택지는 K(요인 수)에 따라 라벨 변동:
- 연속 요인 0개 → `Create an experiment with K categorical factors`
- 연속 요인 1개 → `Create an experiment with K categorical and one continuous factor`
- 연속 요인 2개 이상 → K 에 따라 `Create an experiment with two continuous factors` / `Create an experiment with two or three continuous factors` / `Create an experiment with two or more continuous factors` 중 보이는 것
- 혼합물 → `Create an experiment with K components of a mixture`
3단계(목표): `Estimate main and interaction effects`(→ 2-level factorial) / `Estimate main, interaction and quadratic effects`(→ response surface) / `Understand the effect of changes in the proportions of components of a mixture`(→ mixture). (HTC·Taguchi 분기 문구는 문서에 없음.)

### 7.3 Quick Designs 의 Create 2-Level Factorial Design 대화상자 (designs__create-2-level-factorial-design)
| 필드 | 내용 |
|---|---|
| **Enter the name of your response variable** | 워크시트에 그 이름의 반응 열 생성 |
| **Table of factors** | `Name` / `Type`(Continuous/Categorical) / `Low` / `High`. 연속: 숫자(낮은 값을 Low). 범주형: 라벨(숫자·텍스트), 순서 임의 |
| **Number of replicates** | `None`, … (corner points 반복). Modify Design 으로 추후 추가 가능 |
예제: 6요인 연속, replicates None → **35 runs = 32 corner + 3 center points**, 워크시트는 랜덤 run order. (→ Quick Designs 는 6요인에 대해 **32런(1/2 fraction, res VI) + 중앙점 3개**를 자동 선택. 요인 수별 자동 선택 규칙 표는 문서에 없음.)

### 7.4 Quick Designs 의 Create Definitive Screening Design (designs__create-screening-design)
필드: 반응 이름 / **Number of factors**(표가 바뀜) / 요인 표(Name, Type, Low, High) / Number of replicates. 예제: 7요인 연속 → **17 base runs(중앙점 1 포함)**, 랜덤 run order.

### 7.5 Quick Designs 의 Response Surface / Mixture (참고)
- RS: 3요인 연속, replicates None → **20 base runs**(CCD). 필드: 반응 이름, 요인 표(Continuous/Categorical, Low/High), Number of replicates.
- Mixture: 3성분 Lower 0 / Upper 1, replicates None → **15 runs**. 필드: 반응 이름, 성분 표(Name, Lower, Upper), Number of replicates. 하한을 바꾸면 다른 성분의 달성 가능한 상한을 자동 계산.

---

## 8. 구현 시 주의할 점

1. **요인 문자에서 I 를 건너뛴다**(A…H, J, K, …, P). 기본 요인 이름, 생성자 파싱, alias 표, 설계표 헤더 모두 동일 규칙. 15요인 → P.
2. **기본 생성자·블록 생성자는 2.2 표를 그대로 룩업**해야 Minitab 과 같은 alias/해상도가 나온다. 2.2 표 원문에는 중복 행(5|16|V)과 생성자 수가 부족해 보이는 행(10|32, 11|128)이 있으므로 데이터화할 때 별도 검증 필요. 5요인 16런은 **8 blocks 일 때만 E=ABC** 로 바뀜.
3. **중앙점 총수 = 지정값 × 블록 수 × 2^Q(텍스트 요인 수)**; replicates 는 영향 없음(2-level). PB 는 **replicate 마다** 지정값이 반복되고 블록 수와 무관. DSD 는 사용자가 지정하지 않고 숫자만이면 1, 텍스트 포함이면 2 per replicate. 모든 요인이 텍스트면 중앙점 입력을 막아야 하고, 분할구는 중앙점 자체가 없다.
4. **Runs(총 런) = base corner × replicates × (fold 시 2) + 총 중앙점**. Design Summary 의 `Base Design:` 은 (base 요인 수, base 런 수)이며 specify-generators 에서는 base 요인 수(예 5)가 최종 요인 수(9)와 다르다.
5. **해상도 표기 분기**: 블록 1 → `Resolution:`, 블록 ≥2 → `Resolution with blocks:` + 2.2 표의 블록 해상도. res III 이면 `* NOTE * Some main effects are confounded with two-way interactions.`, 블록이 2FI 와 교락이면 `* NOTE * Blocks are confounded with two-way interactions.`. 블록 수 = replicates 의 배수면 블록 생성자 없이 replicate 로 블록을 만든다(해상도 유지).
6. **Alias 표 생성**: 정의관계 전체(2^p − 1 단어) × 각 항 → 제곱 제거 → 차수 오름차순·알파벳 정렬; 행 순서는 I → 주효과 → 미등장 2FI → …; 요인 수에 따른 기본 차수 상한(≤7 전부, 8–10 은 3차, 11–15 는 2차)과 `Interactions up through order` 옵션(제목 `Alias Structure (up to order 2)`, 단독 항은 혼자 출력)을 지원. 블록 행 `Blk1 = AB + CDE` 는 I 바로 다음.
7. **Fraction 번호**: Yates 순서로 생성자 부호 조합에 1…2^p 를 부여하고 principal(모두 +) = 2^p. 사용자가 번호를 바꾼 경우에만 Design Summary 에 fraction number 를 표시한다(라벨 문자열은 문서에 없음 → 별도 확인).
8. **Fold 검증**: 접기 후 정의관계가 줄지 않으면(모든 단어 짝수, 또는 단일 요인이 어떤 단어에도 없음) 설계를 만들지 말고 경고. Summary 의 Design Generators 는 접기 전, Defining Relation 은 접기 후. 블록 설계 fold 시 블록 생성자 유지, 블록당 런 2배. GFF 는 fold 불가.
9. **워크시트 열 규칙**: C1 StdOrder, C2 RunOrder, C3 CenterPt(2-level) 또는 PtType(PB/DSD/split-plot/GFF/RS/mixture; 0 center, 1 corner, −1 axial, 2 edge), C4 Blocks(없으면 전부 1), C5~ 요인. 분할구는 WP 열 추가(정확한 위치는 문서에 없음). 설계 열은 삭제·이동 불가 상태로 관리해야 하며, 수준 변경은 Modify factors 경로로만.
10. **랜덤화는 블록 내**(분할구는 whole plot 내, whole plot 순서도 랜덤)이며 `Base for random data generator` 로 재현 가능해야 한다. 테스트 정답으로 쓸 예제 설계표는 Minitab 의 RNG 결과이므로 **런 순서까지 일치시키려 하지 말고** (a) 고유 런 집합·블록/WP 배정·중앙점 수·alias 구조가 일치하는지, (b) 랜덤화 OFF 시 표준 순서(첫 요인이 가장 빨리 바뀜)가 맞는지로 검증한다. 블록 예제의 StdOrder 는 블록별 재정렬 후 매겨진 것으로 보이므로 StdOrder 부여 규칙은 추가 확인 필요.
11. **PB 생성**: 12~48 런(4의 배수, 8·16 제외), 생성열 순환 치환 + 마지막 전부 − 행(28런은 9×27 블록 순환 + 전부 − 열), 요인 k<n−1 이면 처음 k 열 사용. 문서의 40런 생성열은 부호 수가 맞지 않으므로 "20런 설계 복제" 규칙으로 재생성 후 검증, 44런 행의 `+-` 는 두 부호로 분리.
12. **Add axial points** 는 모든 요인이 numeric 인 2-level/PB 에만 허용하고, 결과 설계 타입을 CCD(response surface)로 바꾸며 축점을 새 블록에 CenterPt(PtType) = −1 로 추가한다. 기본 α 는 corner 수 기반 rotatable(예: 8 corner → 1.414).
13. **Replicate design(Modify)** 은 워크시트의 모든 행(중앙점 포함)을 복제해 새 블록 번호로 뒤에 붙이고 StdOrder/RunOrder 를 이어서 매긴다(최대 10회). 생성 시의 replicates 와 달리 중앙점도 함께 늘어난다.
