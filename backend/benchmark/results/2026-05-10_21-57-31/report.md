# PIPELINE BENCHMARK — 2026-05-10_21-57-31

## Overall Pipeline Score: 6.5 / 10

> The pipeline excels at weaving user interview responses into highly personalized narratives but frequently fails at authentic archetype matching by forcing athletes into sports that contradict their explicit physical preferences or adaptive needs.

### Dimension Averages
```
  Authenticity             ██████░░░░  5.9
  Personalization          ████████░░  7.9
  Interview Quality        ████████░░  7.6
  Pathway Distinctness     ██████░░░░  6.1
```

### Per-Persona Scorecard (avg ± variance across rounds)

| Persona | Rounds | Overall | Auth | Pers | IQ | Distinct | Compliance |
|---------|:------:|:-------:|:----:|:----:|:--:|:--------:|:----------:|
| Young female swimmer                   | 3 | **6.3** (5–7) | 6.3 (4–8) | 8.3 (8–9) | 7.7 (7–8) | 5.0 (4–6) | 3/3✓ |
| Tall male power athlete                | 3 | **8.0** | 8.3 (8–9) | 8.7 (8–9) | 7.7 (7–8) | 8.3 (8–9) | 3/3✓ |
| Adaptive athlete — partial visual impa | 3 | **5.0** (3–6) | 3.3 (3–4) | 6.7 (3–9) | 7.7 (7–8) | 4.7 (2–7) | 3/3✓ |
| Veteran ultramarathon runner           | 3 | **6.7** (6–7) | 5.3 (4–6) | 9.0 | 7.3 (6–8) | 7.3 (5–9) | 3/3✓ |
| Youth gymnast — time travel to 2032    | 3 | **7.7** (7–8) | 7.3 (5–9) | 8.0 (7–9) | 8.3 (8–9) | 8.0 (7–9) | 3/3✓ |
| Hostile ex-boxer — distrusts Olympics  | 3 | **5.3** (5–6) | 4.3 (4–5) | 7.0 (6–8) | 7.0 (5–8) | 3.3 (3–4) | 3/3✓ |
| Congenitally blind — goalball and tand | 3 | **5.0** (4–6) | 4.7 (3–7) | 6.3 (6–7) | 6.7 (6–7) | 6.3 (5–7) | 3/3✓ |
| Above-knee amputee — para-sprinter     | 3 | **7.0** (6–8) | 8.7 (8–9) | 8.3 (8–9) | 8.0 | 4.7 (2–7) | 2/3✓ |
| Congenital limb difference — adaptive  | 3 | **5.7** (5–6) | 4.3 (3–6) | 7.7 (6–9) | 8.0 | 4.7 (3–6) | 2/3✓ |
| Early-stage ALS — former competitive t | 3 | **7.0** (5–8) | 6.0 (4–7) | 8.0 (6–9) | 8.0 | 7.7 (7–8) | 3/3✓ |
| Retired gymnastics coach — time travel | 3 | **7.7** (7–8) | 7.7 (7–8) | 8.7 (8–9) | 7.7 (7–8) | 6.3 (4–8) | 3/3✓ |
| Para-rower with SCI — time travel to 2 | 3 | **6.3** (4–8) | 4.3 (2–6) | 8.7 (8–9) | 8.0 | 7.0 (4–9) | 3/3✓ |
| T4 paraplegic — wheelchair racer and b | 3 | **5.3** (5–6) | 4.3 (4–5) | 6.3 (5–8) | 7.3 (7–8) | 6.3 (4–8) | 3/3✓ |
| Profoundly deaf — competitive 400m spr | 3 | **7.7** (7–8) | 7.3 (6–9) | 8.7 (8–9) | 7.7 (7–8) | 6.7 (4–8) | 3/3✓ |
| Competitive powerlifter — high BMI, el | 3 | **6.3** (6–7) | 6.3 (5–8) | 7.7 (5–9) | 7.0 (5–8) | 4.7 (3–7) | 3/3✓ |

### What's Working Well
- Exceptional personalization that seamlessly integrates specific user quotes, biometrics, and custom inputs into the narrative (e.g., 01_young_female_swimmer, 15_powerlifter_high_bmi).
- Strong handling of time-travel and life-stage constraints, accurately adjusting tone for Elite Peak and Legacy athletes (e.g., 05_youth_time_travel_2032, 11_retired_gymnast_time_travel_1984).

### What Needs Improvement
- Severe authenticity failures where the secondary archetype directly contradicts the user's explicit interview choices, such as assigning endurance sports to explosive athletes (e.g., 03_adaptive_visual_impairment, 13_wheelchair_racer_paraplegic).
- Distinctness failures regarding adaptive pathways, as the narratives often ignore the user's disability and treat para-athletes with generic able-bodied prose (e.g., 08_above_knee_amputee_sprinter, 09_congenital_limb_difference_swimmer).

### ⚠ Critical Issues
- 03_adaptive_visual_impairment: Overall score of 3 due to hallucinating interview answers to force-fit incompatible individual archetypes.
- 12_para_rower_time_travel_2036: Authenticity score of 2 for recommending the 10-event Decathlon to a 48-year-old who explicitly requested a singular signature movement.
- 08_above_knee_amputee_sprinter: Compliance failure for using 'The 2028 Games' instead of the required city-inclusive format.
- 09_congenital_limb_difference_swimmer: Compliance failure for omitting host cities (e.g., 'The 2032 Games').

### Suggested Improvements
**Archetype Matching Engine**: Implement a hard constraint system where explicit user rejections of energy systems (e.g., endurance vs. explosive) immediately filter out incompatible sports.

**Adaptive Narrative Generation**: Add a specific prompt directive requiring the LLM to explicitly address the user's adaptive classification and how it translates to the recommended Paralympic sport pathways.

**Compliance Formatting**: Enforce a strict regex validation or post-processing step for Games naming conventions to ensure the 'The [City] [Year] Games' format is always used.

**Secondary Archetype Logic**: Prevent the system from selecting a secondary archetype that serves as an 'inverted contrast' if it violates the user's primary physical biometrics or stated preferences.

### Dimension Analysis
- **Authenticity**: Frequently compromised by a matching engine that forces secondary archetypes contradicting the user's explicit physical preferences or realistic age capabilities.
- **Personalization**: Consistently exceptional across all personas, seamlessly weaving exact interview quotes, biometrics, and custom inputs into the narrative.
- **Interview Quality**: Strong and logically progressive, offering genuinely distinct forks that effectively probe the athlete's psychological and physiological profile.
- **Pathway Distinctness**: Generally weak, particularly for adaptive athletes, as the narratives often fail to uniquely explore Paralympic pathways or differentiate the prose from able-bodied templates.
