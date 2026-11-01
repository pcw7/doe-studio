"""도움말 — 실험 흐름, 목적별 설계 고르기, 결과 읽는 법, 용어 사전, 자주 묻는 질문(한/영)."""
import streamlit as st

from app.i18n import T

st.title(T("도움말", "Help"))
st.caption(T("처음 실험계획법을 쓰는 연구원을 위한 안내", "A guide for researchers new to design of experiments"))

tab_flow, tab_choose, tab_read, tab_terms, tab_faq = st.tabs([
    T("실험 흐름", "Workflow"), T("설계 고르기", "Choosing a design"), T("결과 읽기", "Reading results"),
    T("용어", "Glossary"), T("자주 묻는 질문", "FAQ")])

FLOW = [
    ("계획", "Plan", "검정력·표본 크기", "Power & sample size",
     "찾고 싶은 효과 크기와 잡음(표준편차)으로 필요한 반복 수를 정합니다.",
     "Decide how many replicates you need from the effect you want to detect and the noise (standard deviation)."),
    ("설계", "Design", "설계 생성", "Create design",
     "요인·수준·설계 종류를 고르면 실험 순서표(런 순서)가 만들어집니다.",
     "Pick factors, levels and the design type to get a run sheet in run order."),
    ("실험", "Run", "워크시트·설계 수정", "Worksheet & modify design",
     "런 순서대로 실험하고 결과를 반응 열에 적습니다. Excel·CSV 로 내보내 실험실에서 써도 됩니다.",
     "Run the experiments in run order and enter results in a response column. You can export to Excel or CSV."),
    ("분석", "Analyze", "분석·그래프", "Analyze & graphs",
     "유의한 항을 찾고 모형을 줄입니다(p 값, 효과도, 단계적 선택). 잔차 그림으로 가정을 확인합니다.",
     "Find the significant terms and reduce the model (p-values, effects plots, stepwise). Check assumptions with "
     "residual plots."),
    ("최적화", "Optimize", "반응 최적화·예측", "Response optimizer & predict",
     "목표(최대·최소·목표값)를 정하면 가장 좋은 조건과 그 조건의 예측값을 알려 줍니다.",
     "Set goals (maximize, minimize, target) to get the best settings and their predicted responses."),
    ("확인·보고", "Confirm & report", "보고서 내려받기", "Report downloads",
     "최적 조건에서 확인 실험을 하고, 결과를 Excel·HTML·PDF 보고서로 공유합니다.",
     "Run confirmation runs at the optimal settings and share the results as Excel, HTML or PDF reports."),
]

with tab_flow:
    st.write(T("실험계획법은 아래 순서로 진행합니다. 각 단계의 화면은 왼쪽 메뉴에 있습니다.",
               "A designed experiment follows these steps. Each step has a page in the left menu."))
    for i, (ko, en, page_ko, page_en, d_ko, d_en) in enumerate(FLOW, start=1):
        st.markdown(T(f"**{i}. {ko}** — *{page_ko}* 화면  \n{d_ko}", f"**{i}. {en}** — *{page_en}* page  \n{d_en}"))

CHOOSE = [
    ("요인이 많고(5개 이상) 중요한 요인을 추리고 싶다", "Many factors (5 or more); find the important few",
     "Plackett-Burman, 2수준 부분요인(해상도 III–IV), 확정적 선별설계(곡률도 확인)",
     "Plackett-Burman, 2-level fractional factorial (resolution III–IV), definitive screening (also detects curvature)"),
    ("요인 2~5개의 주효과와 교호작용을 알고 싶다", "Main effects and interactions of 2–5 factors",
     "2수준 완전요인 또는 해상도 V 이상 부분요인 + 중앙점(곡면성 확인)",
     "2-level full factorial or resolution V+ fraction, plus center points (to check curvature)"),
    ("최적 조건(곡면의 꼭대기·골짜기)을 찾고 싶다", "Find the optimum (a peak or valley of a curved surface)",
     "반응표면 설계(중심합성 CCD, Box-Behnken) → 반응 최적화",
     "Response surface design (central composite, Box-Behnken), then the response optimizer"),
    ("배합 비율(성분 합이 100%)이 요인이다", "The factors are blend proportions that add up to 100%",
     "혼합물 설계(심플렉스 격자·중심, 극꼭지점), 공정 변수를 함께 넣을 수 있음",
     "Mixture design (simplex lattice or centroid, extreme vertices), optionally with process variables"),
    ("범주형 요인이 3수준 이상이다(예: 촉매 A/B/C)", "A categorical factor has 3 or more levels (e.g. catalyst A/B/C)",
     "일반 완전요인설계", "General full factorial design"),
    ("바꾸기 어려운 요인이 있다(예: 반응기 온도)", "Some factors are hard to change (e.g. reactor temperature)",
     "분할구 설계", "Split-plot design"),
    ("잡음에 강한 조건(산포가 작은 조건)을 찾고 싶다", "Find settings that are robust to noise (small variation)",
     "Taguchi 설계(S/N 비), 또는 반복 측정 + 산포 분석 → 최적화에서 평균은 목표값·표준편차는 최소화",
     "Taguchi design (S/N ratios), or repeated measurements with Analyze Variability, then optimize the mean to a "
     "target while minimizing the standard deviation"),
    ("결과가 합격/불합격, 불량 여부다", "The result is pass/fail or defect/no defect",
     "이항 반응 분석(로지스틱)", "Analyze binary response (logistic)"),
    ("실험 횟수가 제한되거나 실험 영역에 제약이 있다", "Runs are limited or the region is constrained",
     "최적 설계(D-최적)로 후보점에서 고르기", "Optimal design (D-optimal) chosen from candidate points"),
]

with tab_choose:
    st.write(T("실험 목적에 맞는 설계를 고르세요.", "Choose the design that matches your goal."))
    head = T("| 목적 | 추천 설계 |\n|---|---|\n", "| Goal | Suggested design |\n|---|---|\n")
    st.markdown(head + "\n".join(T(f"| {g_ko} | {d_ko} |", f"| {g_en} | {d_en} |") for g_ko, g_en, d_ko, d_en in CHOOSE))
    st.info(T("처음에는 적은 실험으로 요인을 추리고(선별), 중요한 요인으로 반응표면 설계를 해 최적 조건을 찾는 순차 실험이 "
              "효율적입니다.",
              "Sequential experimentation is efficient: screen the factors with few runs first, then run a response "
              "surface design on the important ones to find the optimum."))

READ = [
    ("P-Value", "p 값이 유의수준 α(보통 0.05)보다 작으면 그 항의 효과가 있다고 봅니다.",
     "A term is significant when its p-value is below the significance level α (usually 0.05)."),
    ("Coef · Effect", "코드화 단위의 계수. 2수준 요인의 효과 = 2 × 계수(낮은 수준 → 높은 수준의 반응 변화).",
     "Coefficients in coded units. For 2-level factors, effect = 2 × coefficient (change from low to high level)."),
    ("R-sq · R-sq(adj) · R-sq(pred)", "모형이 설명하는 변동의 비율. R-sq(pred) 가 R-sq 보다 많이 낮으면 과적합을 의심합니다.",
     "Share of variation explained. If R-sq(pred) is much lower than R-sq, suspect overfitting."),
    ("S", "잔차의 표준편차(반응 단위). 작을수록 예측이 정확합니다.",
     "Standard deviation of the residuals (response units). Smaller means more precise predictions."),
    ("Lack-of-Fit", "적합성 결여 p 값이 작으면 모형이 데이터를 충분히 설명하지 못합니다(항 추가를 검토).",
     "A small lack-of-fit p-value means the model misses something (consider adding terms)."),
    ("Curvature", "곡면성이 유의하면 2수준 모형으로는 부족하므로 반응표면 설계(축점 추가)를 검토합니다.",
     "Significant curvature means a 2-level model is not enough; consider a response surface design (add axial "
     "points)."),
    ("VIF", "5~10 보다 크면 항끼리 겹쳐(다중공선성) 계수가 불안정합니다.",
     "Above 5–10, terms overlap (multicollinearity) and coefficients are unstable."),
    ("Residual plots", "정규확률도가 직선에 가깝고, 적합치·순서에 대해 무늬가 없어야 합니다.",
     "Points should follow the line on the normal plot and show no pattern versus fits or order."),
    ("Desirability", "만족도 0~1. 1 이면 모든 목표를 완전히 만족합니다.",
     "Desirability from 0 to 1; 1 means every goal is fully met."),
]

with tab_read:
    head = T("| 결과 | 읽는 법 |\n|---|---|\n", "| Output | How to read it |\n|---|---|\n")
    st.markdown(head + "\n".join(T(f"| {k} | {ko} |", f"| {k} | {en} |") for k, ko, en in READ))

TERMS = [
    ("요인", "Factor", "실험에서 바꾸는 변수(온도, 압력, 촉매).", "A variable you change (temperature, pressure, catalyst)."),
    ("수준", "Level", "요인이 갖는 값(예: 150 °C, 200 °C).", "A value of a factor (e.g. 150 °C, 200 °C)."),
    ("런", "Run", "요인 수준 조합 하나로 하는 실험 한 번.", "One experiment at one combination of factor levels."),
    ("반복", "Replicate", "같은 조건의 실험을 처음부터 다시 함(오차 추정).",
     "Running the same conditions again from scratch (estimates error)."),
    ("반복 측정", "Repeat", "한 런에서 여러 번 측정함(측정 변동).", "Several measurements within one run (measurement variation)."),
    ("블록", "Block", "날짜·원료 로트처럼 조건이 비슷한 런의 묶음.", "A group of runs under similar conditions, such as a day or a lot."),
    ("중앙점", "Center point", "모든 숫자 요인이 가운데 값인 런. 곡면성과 순수 오차를 봅니다.",
     "A run with every numeric factor at its midpoint; checks curvature and pure error."),
    ("랜덤화", "Randomization", "런 순서를 무작위로 해 시간에 따른 영향을 섞음.",
     "Running in random order so time-related effects are spread out."),
    ("교호작용", "Interaction", "한 요인의 효과가 다른 요인의 수준에 따라 달라짐.",
     "The effect of one factor depends on the level of another."),
    ("별칭(교락)", "Alias (confounding)", "부분요인설계에서 서로 구별할 수 없는 효과.",
     "Effects that cannot be told apart in a fractional design."),
    ("해상도", "Resolution", "별칭의 심한 정도. V 이상이면 주효과·2차 교호작용을 분리합니다.",
     "How severe the aliasing is; resolution V or higher separates main effects and 2-way interactions."),
    ("포화 모형", "Saturated model", "계수 수 = 런 수라 오차 자유도가 0 인 모형.",
     "A model with as many coefficients as runs, so no error degrees of freedom."),
    ("검정력", "Power", "실제 효과가 있을 때 그것을 유의하다고 찾아낼 확률.",
     "The probability of detecting an effect that really exists."),
    ("S/N 비", "Signal-to-noise ratio", "Taguchi 설계에서 평균과 산포를 함께 담은 지표. 클수록 좋습니다.",
     "In Taguchi designs, a measure combining mean and variation; larger is better."),
    ("만족도", "Desirability", "여러 반응의 목표 달성 정도를 0~1 로 나타낸 값.",
     "How well several responses meet their goals, from 0 to 1."),
    ("유사성분", "Pseudo-component", "혼합물에서 하한을 뺀 뒤 0~1 로 다시 잡은 성분 척도.",
     "A mixture component rescaled to 0–1 after removing the lower bounds."),
]

with tab_terms:
    head = T("| 용어 | 영어 | 뜻 |\n|---|---|---|\n", "| Term | Meaning |\n|---|---|\n")
    st.markdown(head + "\n".join(T(f"| {ko} | {en} | {d_ko} |", f"| {en} | {d_en} |") for ko, en, d_ko, d_en in TERMS))

FAQ = [
    ("Minitab 과 결과가 같은가요?", "Do the results match Minitab?",
     "공식 문서 예제의 출력표와 글자 단위로 대조해 검증했습니다. 문서에 없는 표시 규칙 몇 가지는 예제로 추정했습니다.",
     "Outputs were checked character by character against the examples in Minitab's documentation. A few display rules "
     "not stated in the documentation were inferred from the examples."),
    ("가지고 있는 데이터(Excel·CSV·Minitab)를 분석할 수 있나요?", "Can I analyze data I already have (Excel, CSV, Minitab)?",
     "시작 화면에서 파일을 불러와 요인 열을 고르면 설계 종류를 알아보고 정의합니다(사용자 설계 정의).",
     "Open the file on the Home page and pick the factor columns; the design type is detected and defined (custom design)."),
    ("실패한 런이 있으면?", "What if some runs failed?",
     "반응 칸을 비워 두면 그 런은 분석에서 빠집니다. 별칭이 생겨 추정할 수 없는 항은 자동으로 뺍니다.",
     "Leave the response blank and that run is left out. Terms that become inestimable are removed automatically."),
    ("결과는 어떻게 저장하나요?", "How do I save results?",
     "워크시트는 JSON·CSV·Excel 로, 분석 결과는 각 화면의 보고서 내려받기(Excel·HTML·PDF)로 저장합니다.",
     "Save the worksheet as JSON, CSV or Excel, and analysis results with the report downloads (Excel, HTML, PDF) on "
     "each page."),
    ("영어 화면으로 바꿀 수 있나요?", "Can I switch to English?",
     "왼쪽 사이드바 아래의 언어 선택에서 English 를 고르면 화면·그래프·보고서가 영어로 바뀝니다.",
     "Choose English in the language switch at the bottom of the sidebar; pages, graphs and reports switch to English."),
]

with tab_faq:
    for q_ko, q_en, a_ko, a_en in FAQ:
        with st.expander(T(q_ko, q_en)):
            st.write(T(a_ko, a_en))
