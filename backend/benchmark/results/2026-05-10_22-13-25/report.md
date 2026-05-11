# PIPELINE BENCHMARK — 2026-05-10_22-13-25

## Overall Pipeline Score: 6.5 / 10

> The pipeline excels at primary biometric matching and deep narrative personalization, but suffers from severe logic failures in secondary archetype matching and consistently neglects adaptive pathways.

### Dimension Averages
```
  Authenticity             ███████░░░  6.6
  Personalization          ████████░░  7.7
  Interview Quality        ████████░░  7.7
  Pathway Distinctness     ██████░░░░  6.5
```

### Per-Persona Scorecard (avg ± variance across rounds)

| Persona | Rounds | Overall | Auth | Pers | IQ | Distinct | Compliance |
|---------|:------:|:-------:|:----:|:----:|:--:|:--------:|:----------:|
| Young female swimmer                   | 3 | **6.7** (6–8) | 6.7 (6–8) | 8.3 (8–9) | 7.7 (7–8) | 7.0 (5–8) | 3/3✓ |
| Tall male power athlete                | 3 | **7.7** (7–8) | 8.3 (8–9) | 7.0 (5–8) | 8.0 | 7.0 (5–8) | 3/3✓ |
| Adaptive athlete — partial visual impa | 3 | **5.3** (4–8) | 5.0 (3–8) | 6.7 (4–9) | 7.7 (7–8) | 5.7 (2–8) | 2/3✓ |
| Veteran ultramarathon runner           | 3 | **5.7** (5–6) | 4.3 (3–5) | 8.3 (8–9) | 8.0 | 5.0 (3–6) | 3/3✓ |
| Youth gymnast — time travel to 2032    | 3 | **7.3** (7–8) | 6.7 (5–8) | 8.3 (8–9) | 7.0 (6–8) | 6.7 (4–9) | 3/3✓ |
| Hostile ex-boxer — distrusts Olympics  | 1 +2err | **8.0** | 7.0 | 9.0 | 8.0 | 9.0 | 1/1✓ |
| Congenitally blind — goalball and tand | 3 | **7.0** (6–8) | 7.3 (6–8) | 7.0 (5–9) | 6.7 (5–8) | 8.0 (6–9) | 3/3✓ |
| Above-knee amputee — para-sprinter     | 3 | **7.7** (7–9) | 8.3 (7–9) | 8.3 (8–9) | 8.0 | 6.3 (5–9) | 3/3✓ |
| Congenital limb difference — adaptive  | 3 | **6.0** (4–8) | 6.0 (3–9) | 7.0 (5–8) | 7.7 (7–8) | 4.7 (3–7) | 3/3✓ |
| Early-stage ALS — former competitive t | 3 | **7.0** | 7.0 | 8.0 | 8.0 | 6.7 (4–9) | 2/3✓ |
| Retired gymnastics coach — time travel | 3 | **7.0** | 7.3 (7–8) | 8.3 (8–9) | 8.0 | 5.3 (4–6) | 3/3✓ |
| Para-rower with SCI — time travel to 2 | 3 | **7.7** (6–9) | 7.0 (5–9) | 8.7 (8–9) | 8.3 (8–9) | 8.7 (8–9) | 3/3✓ |
| T4 paraplegic — wheelchair racer and b | 3 | **5.7** (4–7) | 4.3 (3–6) | 7.0 (5–8) | 8.0 | 7.3 (6–8) | 3/3✓ |
| Profoundly deaf — competitive 400m spr | 3 | **7.0** (6–8) | 7.3 (5–9) | 8.3 (7–9) | 7.7 (7–8) | 5.3 (4–7) | 3/3✓ |
| Competitive powerlifter — high BMI, el | 3 | **6.0** (4–7) | 6.7 (3–9) | 6.0 (4–8) | 7.0 (6–8) | 6.3 (4–9) | 3/3✓ |

### What's Working Well
- Excellent primary biometric matching and life-stage coherence, accurately framing physical profiles and time-travel scenarios (e.g., 02_tall_power_athlete, 05_youth_time_travel_2032, 12_para_rower_time_travel_2036).
- Deep personalization that seamlessly weaves exact interview quotes and psychological drivers into the scout verdicts (e.g., 04_veteran_endurance_runner, 14_deaf_sprinter).

### What Needs Improvement
- Secondary archetype matching frequently contradicts explicit user preferences, such as assigning endurance sports to explosive athletes or individual sports to team-focused athletes (e.g., 03_adaptive_visual_impairment, 09_congenital_limb_difference_swimmer, 13_wheelchair_racer_paraplegic).
- Consistent failure to adequately explore or differentiate adaptive pathways in the narrative, often ignoring them entirely (e.g., 03_adaptive_visual_impairment, 08_above_knee_amputee_sprinter, 15_powerlifter_high_bmi).
- Occasional severe biometric mismatches for secondary sports, such as recommending Basketball for a 142kg powerlifter (15_powerlifter_high_bmi).

### ⚠ Critical Issues
- 03_adaptive_visual_impairment: Compliance failure (adaptive pathways ignored) and Authenticity score of 3 (assigned solitary sports despite team dynamics choice).
- 10_early_stage_als: Compliance failure (incorrect Games formatting 'The 2030 Games').
- 04_veteran_endurance_runner: Authenticity score of 3 (assigned explosive Block Starter to 42yo endurance athlete).
- 09_congenital_limb_difference_swimmer: Authenticity score of 3 (assigned sprint/alpine skiing despite endurance preference).
- 13_wheelchair_racer_paraplegic: Authenticity score of 3 (assigned individual sports despite team dynamics choice).
- 15_powerlifter_high_bmi: Authenticity score of 3 (assigned Basketball to 142kg athlete).

### Suggested Improvements
**Archetype Matching Logic**: Implement a strict constraint checker that filters out archetypes directly contradicting the user's explicit choices (e.g., Team vs. Solo, Endurance vs. Explosive).

**Adaptive Pathway Narrative**: Enforce a prompt rule or structural template requiring at least one dedicated paragraph detailing the adaptive sport pathway and its specific mechanics.

**Biometric Guardrails**: Add hard BMI/weight limits for certain archetypes (e.g., Basketball) to prevent recommending high-mobility sports to super-heavyweight athletes.

**Compliance Formatting**: Add a post-processing regex check to ensure all Games references strictly follow the 'The [City] [Year] Games' format.

### Dimension Analysis
- **Authenticity**: Primary sport matches are generally highly realistic based on biometrics, but secondary recommendations frequently suffer from severe logical disconnects and biometric mismatches.
- **Personalization**: Exceptionally strong across the board, with the pipeline consistently weaving exact user quotes, psychological drivers, and physical traits into compelling narratives.
- **Interview Quality**: The dynamic interviewer performs very well, consistently offering distinct, meaningful forks that successfully probe the athlete's physical and psychological profile.
- **Pathway Distinctness**: While the two recommended sports are usually distinct from one another, the pipeline struggles to meaningfully differentiate the standing and adaptive narratives within those profiles.
