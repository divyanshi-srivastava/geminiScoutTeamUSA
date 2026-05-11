# PIPELINE BENCHMARK — 2026-05-10_22-30-08

## Overall Pipeline Score: 7.4 / 10

> The pipeline consistently generates highly evocative, biometrically plausible scouting reports, but struggles with seasonal event logic and occasionally contradicts explicit user preferences.

### Dimension Averages
```
  Authenticity             ████████░░  7.6
  Personalization          ████████░░  8.0
  Interview Quality        ████████░░  7.6
  Pathway Distinctness     ████████░░  8.2
```

### Per-Persona Scorecard (avg ± variance across rounds)

| Persona | Rounds | Overall | Auth | Pers | IQ | Distinct | Compliance |
|---------|:------:|:-------:|:----:|:----:|:--:|:--------:|:----------:|
| Young female swimmer                   | 3 | **8.0** | 8.7 (8–9) | 9.0 | 8.0 | 8.0 | 3/3✓ |
| Tall male power athlete                | 3 | **7.7** (7–9) | 8.7 (8–9) | 6.7 (5–9) | 6.7 (6–8) | 8.7 (8–9) | 3/3✓ |
| Adaptive athlete — partial visual impa | 3 | **7.0** (6–8) | 6.0 (5–7) | 8.0 | 7.7 (7–8) | 8.3 (8–9) | 3/3✓ |
| Veteran ultramarathon runner           | 3 | **8.0** | 9.0 | 8.0 | 8.0 | 8.0 | 3/3✓ |
| Youth gymnast — time travel to 2032    | 3 | **6.7** (6–8) | 5.3 (4–8) | 8.3 (8–9) | 8.0 | 8.0 (6–9) | 3/3✓ |
| Hostile ex-boxer — distrusts Olympics  | 3 | **8.7** (8–9) | 9.0 | 9.0 (8–10) | 7.3 (6–8) | 8.7 (8–9) | 3/3✓ |
| Congenitally blind — goalball and tand | 3 | **7.3** (6–8) | 7.0 (4–9) | 8.0 | 7.3 (7–8) | 8.7 (8–9) | 3/3✓ |
| Above-knee amputee — para-sprinter     | 3 | **7.3** (6–8) | 8.0 | 7.0 (4–9) | 7.7 (7–8) | 8.3 (8–9) | 3/3✓ |
| Congenital limb difference — adaptive  | 3 | **8.3** (8–9) | 8.3 (8–9) | 8.7 (8–9) | 7.7 (7–8) | 8.7 (8–9) | 3/3✓ |
| Early-stage ALS — former competitive t | 3 | **8.0** | 7.3 (7–8) | 8.3 (8–9) | 7.7 (7–8) | 7.7 (7–8) | 3/3✓ |
| Retired gymnastics coach — time travel | 3 | **7.7** (7–8) | 7.0 (6–8) | 8.7 (8–9) | 7.0 | 8.0 | 3/3✓ |
| Para-rower with SCI — time travel to 2 | 3 | **6.7** (4–8) | 6.0 (3–8) | 7.3 (4–9) | 8.0 | 7.0 (6–8) | 3/3✓ |
| T4 paraplegic — wheelchair racer and b | 3 | **7.0** (6–8) | 8.0 (7–9) | 6.7 (4–9) | 7.7 (7–8) | 8.0 | 3/3✓ |
| Profoundly deaf — competitive 400m spr | 3 | **7.7** (7–8) | 7.7 (7–8) | 8.3 (7–9) | 7.0 (5–8) | 8.3 (8–9) | 3/3✓ |
| Competitive powerlifter — high BMI, el | 3 | **8.0** | 8.7 (8–9) | 8.0 (7–9) | 7.7 (7–8) | 8.3 (8–9) | 3/3✓ |

### What's Working Well
- Exceptional integration of user attitude and psychological drivers into the narrative, particularly for defiant or non-standard inputs (06_hostile_ex_boxer).
- Highly accurate and realistic biometric mapping for extreme physical profiles, matching massive frames to appropriate heavy-athletics pathways (15_powerlifter_high_bmi, 02_tall_power_athlete).

### What Needs Improvement
- Seasonal and geographical hallucinations, such as recommending Alpine Skiing for Summer Games host cities like Brisbane 2032 (05_youth_time_travel_2032) and LA 1984 (11_retired_gymnast_time_travel_1984) in the authenticity dimension.
- Directly contradicting user interview selections in the personalization dimension, such as assigning solo sports to users who explicitly requested team environments (12_para_rower_time_travel_2036, 02_tall_power_athlete).
- Hallucinating interview responses the user did not select or ignoring rich custom text inputs in the personalization dimension (13_wheelchair_racer_paraplegic, 15_powerlifter_high_bmi).

### Suggested Improvements
**Authenticity**: Implement a strict seasonal filter mapping sports to their correct Summer or Winter Games to prevent winter sports from appearing in summer host cities.

**Personalization**: Add a validation step that cross-references the final archetype's core traits (e.g., team vs. solo, endurance vs. explosive) against the user's explicit choices to prevent direct contradictions.

**Personalization**: Enhance the prompt to explicitly extract and incorporate custom free-text inputs, like specific weightlifting metrics, rather than relying solely on multiple-choice mappings.

**Interview Quality**: Eliminate redundant final confirmation turns that do not provide meaningful forks for the athlete's psychological or physical profile.

### Dimension Analysis
- **Authenticity**: Biometric matching is highly realistic, but overall authenticity is occasionally compromised by seasonal event mismatches and assigning sports that contradict the user's physiological strengths.
- **Personalization**: Narratives are deeply tailored and evocative, though the system sometimes forces pre-determined archetypes that ignore or contradict explicit user preferences.
- **Interview Quality**: The interview funnels logically from broad physical traits to specific psychological drivers, though some paths rely on generic options or unnecessary confirmation turns.
- **Pathway Distinctness**: The pipeline consistently excels at providing two highly differentiated athletic pathways that explore distinct facets of the user's profile.
