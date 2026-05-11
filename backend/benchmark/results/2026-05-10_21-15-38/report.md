# PIPELINE BENCHMARK — 2026-05-10_21-15-38

## Overall Pipeline Score: 6.0 / 10

> The pipeline excels at personalizing narratives based on interview responses but suffers from severe logic flaws in gender mapping and adaptive pathway integration.

### Dimension Averages
```
  Authenticity             ██████░░░░  6.3
  Personalization          ████████░░  8.3
  Interview Quality        ███████░░░  7.3
  Pathway Distinctness     █████░░░░░  5.2
```

### Per-Persona Scorecard

| Persona | Overall | Auth | Pers | IQ | Distinct | Compliance |
|---------|:-------:|:----:|:----:|:--:|:--------:|:----------:|
| Young female swimmer                   | **5** | 4 | 8 | 7 | 3 | ✓ |
| Tall male power athlete                | **5** | 5 | 8 | 8 | 8 | ✓ |
| Adaptive athlete — partial visual impa | **6** | 5 | 8 | 8 | 4 | ✓ |
| Veteran ultramarathon runner           | **7** | 8 | 9 | 7 | 4 | ✓ |
| Youth gymnast — time travel to 2032    | **8** | 8 | 8 | 7 | 7 | ✓ |
| Hostile ex-boxer — distrusts Olympics  | **8** | 8 | 9 | 7 | 9 | ✓ |
| Congenitally blind — goalball and tand | **4** | 3 | 8 | 8 | 6 | ✓ |
| Above-knee amputee — para-sprinter     | **7** | 8 | 9 | 8 | 4 | ✓ |
| Congenital limb difference — adaptive  | **5** | 5 | 6 | 8 | 3 | ✓ |
| Early-stage ALS — former competitive t | **6** | 6 | 7 | 8 | 5 | ✓ |
| Retired gymnastics coach — time travel | **4** | 7 | 8 | 4 | 2 | ✓ |
| Para-rower with SCI — time travel to 2 | **7** | 6 | 9 | 7 | 8 | ✓ |
| T4 paraplegic — wheelchair racer and b | **6** | 5 | 9 | 7 | 5 | ✓ |
| Profoundly deaf — competitive 400m spr | **7** | 8 | 9 | 8 | 4 | ✓ |
| Competitive powerlifter — high BMI, el | **8** | 9 | 9 | 8 | 6 | ✓ |

### What's Working Well
- Exceptional personalization, seamlessly weaving specific interview answers and biometrics into the scouting verdicts (e.g., 04_veteran_endurance_runner, 06_hostile_ex_boxer, 15_powerlifter_high_bmi).
- Strong interview quality with logical, progressive questions that adapt well even to difficult or hostile inputs (e.g., 06_hostile_ex_boxer).

### What Needs Improvement
- Severe gender mapping failures in adaptive event recommendations, frequently assigning Men's events to Female athletes and vice versa (e.g., 01_young_female_swimmer, 02_tall_power_athlete, 07_congenitally_blind_goalball, 09_congenital_limb_difference_swimmer).
- Failure to integrate adaptive pathways into the actual narrative text, leaving those recommendations feeling disconnected (e.g., 03_adaptive_visual_impairment, 04_veteran_endurance_runner, 14_deaf_sprinter).
- Age and life-stage logic errors, such as recommending explosive sports to older casual athletes or offering 'decades of experience' to a 26-year-old (e.g., 10_early_stage_als, 11_retired_gymnast_time_travel_1984).

### ⚠ Critical Issues
- 01_young_female_swimmer: Distinctness score of 3.
- 07_congenitally_blind_goalball: Authenticity score of 3 due to recommending Men's +100kg powerlifting to a 60kg female.
- 09_congenital_limb_difference_swimmer: Distinctness score of 3.
- 11_retired_gymnast_time_travel_1984: Distinctness score of 2.

### Suggested Improvements
**Adaptive Pathway Logic**: Implement a strict gender-matching constraint for all recommended events to prevent assigning Men's events to Female athletes and vice versa.

**Narrative Generation**: Update the prompt template to explicitly require the inclusion and contextualization of adaptive pathways within the main scouting verdicts.

**Age and Life Stage Coherence**: Add dynamic age-filtering to interview questions and sport recommendations to prevent offering 'decades of experience' to young users or highly explosive sports to older, casual athletes.

**Distinctness**: Increase the temperature or adjust the penalty parameters in the LLM configuration to generate more varied and unique scouting reports across different personas.

### Dimension Analysis
- **Authenticity**: Generally plausible biometric-to-sport mapping is frequently undermined by glaring gender mismatches and age-inappropriate recommendations.
- **Personalization**: Consistently excellent across all personas, with the pipeline expertly weaving exact interview phrases and physical traits into the final verdicts.
- **Interview Quality**: Strong and logical, featuring progressive questions with meaningfully distinct options that effectively funnel users into specific athletic profiles.
- **Pathway Distinctness**: Noticeably weak, with repetitive narrative structures and a failure to differentiate adaptive pathways from standard standing pathways.
