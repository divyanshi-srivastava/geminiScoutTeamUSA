# PIPELINE BENCHMARK — 2026-05-10_20-44-49

## Overall Pipeline Score: 5.5 / 10

> While the pipeline excels at personalizing narratives and integrating user biometrics for standing sports, it suffers from catastrophic gender and weight class hallucinations in adaptive pathways and frequently fails compliance by omitting adaptive experiences from the final verdicts.

### Dimension Averages
```
  Authenticity             █████░░░░░  5.4
  Personalization          ████████░░  8.0
  Interview Quality        ███████░░░  6.7
  Pathway Distinctness     ████░░░░░░  4.4
```

### Per-Persona Scorecard

| Persona | Overall | Auth | Pers | IQ | Distinct | Compliance |
|---------|:-------:|:----:|:----:|:--:|:--------:|:----------:|
| Young female swimmer                   | **6** | 8 | 8 | 7 | 3 | ✗ |
| Tall male power athlete                | **4** | 4 | 7 | 4 | 7 | ✓ |
| Adaptive athlete — partial visual impa | **6** | 5 | 9 | 7 | 3 | ✓ |
| Veteran ultramarathon runner           | **6** | 7 | 9 | 6 | 3 | ✓ |
| Youth gymnast — time travel to 2032    | **4** | 2 | 8 | 7 | 3 | ✗ |
| Hostile ex-boxer — distrusts Olympics  | **7** | 7 | 9 | 8 | 4 | ✓ |
| Congenitally blind — goalball and tand | **4** | 2 | 8 | 6 | 3 | ✓ |
| Above-knee amputee — para-sprinter     | **6** | 8 | 9 | 8 | 2 | ✗ |
| Congenital limb difference — adaptive  | **5** | 5 | 6 | 8 | 3 | ✓ |
| Early-stage ALS — former competitive t | **6** | 4 | 9 | 8 | 3 | ✓ |
| Retired gymnastics coach — time travel | **5** | 3 | 8 | 5 | 3 | ✓ |
| Para-rower with SCI — time travel to 2 | **8** | 7 | 9 | 8 | 8 | ✓ |
| T4 paraplegic — wheelchair racer and b | **3** | 2 | 4 | 5 | 6 | ✓ |
| Profoundly deaf — competitive 400m spr | **8** | 8 | 9 | 7 | 7 | ✓ |
| Competitive powerlifter — high BMI, el | **8** | 9 | 8 | 7 | 8 | ✓ |

### What's Working Well
- Excellent personalization and integration of specific interview responses into the narrative, particularly for standing pathways (e.g., 03_adaptive_visual_impairment, 04_veteran_endurance_runner, 12_para_rower_time_travel_2036).
- Strong life stage coherence, accurately capturing the psychological and physical realities of specific ages like Elite Peak and Legacy (e.g., 05_youth_time_travel_2032, 11_retired_gymnast_time_travel_1984, 12_para_rower_time_travel_2036).

### What Needs Improvement
- Catastrophic gender and weight class hallucinations in the adaptive pathways, frequently assigning lightweight female athletes to Men's +100kg events (e.g., 05_youth_time_travel_2032, 07_congenitally_blind_goalball, 11_retired_gymnast_time_travel_1984, 13_wheelchair_racer_paraplegic).
- Severe narrative depth imbalance where adaptive pathways are completely ignored in the generated text (e.g., 01_young_female_swimmer, 05_youth_time_travel_2032, 08_above_knee_amputee_sprinter).

### ⚠ Critical Issues
- 01_young_female_swimmer: Compliance failure (adaptive pathway ignored) and distinctness score of 3
- 03_adaptive_visual_impairment: Distinctness score of 3
- 04_veteran_endurance_runner: Distinctness score of 3
- 05_youth_time_travel_2032: Compliance failure (adaptive pathways ignored), authenticity score of 2, distinctness score of 3
- 07_congenitally_blind_goalball: Authenticity score of 2, distinctness score of 3
- 08_above_knee_amputee_sprinter: Compliance failure (adaptive pathways ignored), distinctness score of 2
- 09_congenital_limb_difference_swimmer: Distinctness score of 3
- 10_early_stage_als: Distinctness score of 3
- 11_retired_gymnast_time_travel_1984: Authenticity score of 3, distinctness score of 3
- 13_wheelchair_racer_paraplegic: Overall score of 3, authenticity score of 2

### Suggested Improvements
**Adaptive Pathway Mapping**: Implement strict demographic filters to ensure adaptive event recommendations match the user's gender and weight class, preventing assignments like Men's +100kg for lightweight females.

**Compliance & Narrative Balance**: Update the prompt instructions to explicitly mandate equal paragraph weighting and dedicated text for both standing and adaptive pathways in the final verdict.

**Interview Quality**: Refine the LLM interviewer prompt to avoid catch-all options (e.g., 'A balanced mix') and force distinct, biomechanically focused forks to better differentiate athlete profiles.

**Distinctness**: Introduce higher temperature or varied structural templates in the generation phase to prevent repetitive phrasing and formulaic report layouts across different users.

### Dimension Analysis
- **Authenticity**: Highly variable, with strong biometric matching for standing sports but catastrophic gender and weight hallucinations in adaptive event assignments.
- **Personalization**: Consistently excellent across all personas, seamlessly weaving exact ages, biometrics, and specific interview quotes into the narratives.
- **Interview Quality**: Generally logical and progressive, though occasionally hindered by generic questions or catch-all options that fail to force meaningful biomechanical differentiation.
- **Pathway Distinctness**: Consistently poor across the batch, suggesting the pipeline relies heavily on rigid, formulaic templates that fail to structurally differentiate between diverse athlete profiles.
