# PIPELINE BENCHMARK — 2026-05-10_21-40-26

## Overall Pipeline Score: 5.5 / 10

> The pipeline excels at personalization and life-stage integration but suffers from critical logic failures in adaptive pathway assignments, including severe gender and weight class mismatches, as well as frequently omitting adaptive narratives entirely.

### Dimension Averages
```
  Authenticity             ██████░░░░  6.0
  Personalization          ████████░░  7.7
  Interview Quality        ███████░░░  7.1
  Pathway Distinctness     █████░░░░░  4.6
```

### Per-Persona Scorecard (avg ± variance across rounds)

| Persona | Rounds | Overall | Auth | Pers | IQ | Distinct | Compliance |
|---------|:------:|:-------:|:----:|:----:|:--:|:--------:|:----------:|
| Young female swimmer                   | 3 | **5.0** (4–6) | 4.3 (4–5) | 8.0 | 6.3 (5–8) | 3.7 (2–6) | 2/3✓ |
| Tall male power athlete                | 3 | **6.0** | 7.7 (5–9) | 8.0 | 7.3 (7–8) | 4.3 (3–6) | 3/3✓ |
| Adaptive athlete — partial visual impa | 3 | **6.3** (6–7) | 7.0 (6–8) | 8.0 | 6.7 (6–8) | 4.7 (3–8) | 3/3✓ |
| Veteran ultramarathon runner           | 3 | **5.0** | 5.3 (4–6) | 8.3 (8–9) | 7.3 (7–8) | 2.0 | 2/3✓ |
| Youth gymnast — time travel to 2032    | 3 | **6.7** (6–8) | 6.0 (4–9) | 7.7 (6–9) | 7.7 (7–8) | 5.7 (4–7) | 3/3✓ |
| Hostile ex-boxer — distrusts Olympics  | 3 | **7.3** (6–8) | 8.3 (8–9) | 7.7 (5–9) | 7.7 (7–8) | 5.0 (4–7) | 3/3✓ |
| Congenitally blind — goalball and tand | 3 | **3.0** (2–4) | 3.7 (2–7) | 6.0 (4–8) | 6.0 (5–8) | 2.7 (2–3) | 1/3✓ |
| Above-knee amputee — para-sprinter     | 3 | **7.0** (6–8) | 7.0 | 8.0 (6–9) | 7.7 (7–8) | 6.3 (3–8) | 3/3✓ |
| Congenital limb difference — adaptive  | 3 | **4.0** | 4.7 (4–6) | 5.7 (2–8) | 7.3 (7–8) | 3.0 (2–5) | 2/3✓ |
| Early-stage ALS — former competitive t | 3 | **6.0** (5–7) | 5.7 (5–6) | 7.7 (6–9) | 7.0 (6–8) | 4.7 (3–8) | 3/3✓ |
| Retired gymnastics coach — time travel | 3 | **4.7** (4–5) | 3.0 | 6.7 (6–8) | 7.0 | 5.7 (3–8) | 3/3✓ |
| Para-rower with SCI — time travel to 2 | 3 | **7.0** (6–8) | 5.7 (3–8) | 8.7 (8–9) | 7.7 (7–8) | 6.3 (4–8) | 3/3✓ |
| T4 paraplegic — wheelchair racer and b | 3 | **6.3** (4–8) | 6.3 (3–8) | 8.0 | 6.7 (6–7) | 4.3 (2–7) | 2/3✓ |
| Profoundly deaf — competitive 400m spr | 3 | **7.0** | 7.3 (6–8) | 8.7 (8–9) | 7.0 (6–8) | 4.3 (3–5) | 3/3✓ |
| Competitive powerlifter — high BMI, el | 3 | **7.0** | 7.7 (6–9) | 8.3 (8–9) | 7.3 (7–8) | 5.7 (4–7) | 3/3✓ |

### What's Working Well
- Exceptional personalization, seamlessly weaving exact biometrics and specific interview quotes into the narrative (e.g., 04_veteran_endurance_runner, 12_para_rower_time_travel_2036).
- Strong life-stage coherence for time-travel personas, accurately capturing the tone and physical realities of specific ages (e.g., 05_youth_time_travel_2032, 11_retired_gymnast_time_travel_1984).

### What Needs Improvement
- Severe gender mismatches in the Authenticity dimension, assigning Men's events to females (01_young_female_swimmer, 07_congenitally_blind_goalball) and Women's events to males (02_tall_power_athlete, 15_powerlifter_high_bmi).
- Critical weight class mismatches in the Authenticity dimension, assigning +100kg powerlifting to 55-60kg athletes (07_congenitally_blind_goalball, 11_retired_gymnast_time_travel_1984, 13_wheelchair_racer_paraplegic).
- Frequent failure in the Distinctness dimension to generate adaptive narratives, completely ignoring adaptive pathways in the text (04_veteran_endurance_runner, 09_congenital_limb_difference_swimmer).

### ⚠ Critical Issues
- Compliance failures due to narrative depth imbalance (ignoring adaptive pathways) in 04_veteran_endurance_runner, 07_congenitally_blind_goalball, 09_congenital_limb_difference_swimmer, and 13_wheelchair_racer_paraplegic.
- Compliance failure for incorrect Games formatting and gender mismatch in 01_young_female_swimmer.
- Authenticity scores of ≤3 due to extreme gender/weight mismatches and physiological contradictions in 07_congenitally_blind_goalball, 11_retired_gymnast_time_travel_1984, 12_para_rower_time_travel_2036, and 13_wheelchair_racer_paraplegic.
- Overall scores of ≤3 for 07_congenitally_blind_goalball due to assigning Men's heavyweight events to a 60kg female.

### Suggested Improvements
**Adaptive Pathway Logic**: Implement strict gender and weight-class filtering rules for adaptive event recommendations to prevent assigning Men's or heavyweight events to lightweight female athletes.

**Narrative Generation**: Update the prompt template to explicitly require separate, distinct paragraphs for standing and adaptive pathways to resolve the narrative depth imbalance.

**Physiological Matching**: Add logic constraints to prevent mapping athletes with explicitly stated endurance backgrounds and older ages to explosive sprint archetypes.

### Dimension Analysis
- **Authenticity**: Severely compromised by glaring logic errors in adaptive event assignments, including gender and weight class mismatches, as well as forcing endurance athletes into sprint archetypes.
- **Personalization**: Consistently excellent across all personas, expertly weaving exact biometrics, interview quotes, and life-stage context into cohesive narratives.
- **Interview Quality**: Strong and logical, with questions effectively narrowing down athletic profiles, though the final archetype mapping sometimes ignores the user's choices.
- **Pathway Distinctness**: Poor overall, primarily because the pipeline frequently merges or completely omits the adaptive pathway narrative, failing to provide distinct standing versus adaptive verdicts.
