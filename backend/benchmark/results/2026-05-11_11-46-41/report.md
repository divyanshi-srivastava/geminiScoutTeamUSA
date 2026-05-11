# PIPELINE BENCHMARK — 2026-05-11_11-46-41

## Overall Pipeline Score: 7.4 / 10

> The pipeline demonstrates strong compliance and excellent biometric integration, but struggles occasionally with negative constraints and accurate adaptive sport classifications.

### Dimension Averages
```
  Authenticity             ████████░░  7.7
  Personalization          ████████░░  8.1
  Interview Quality        ████████░░  7.5
  Pathway Distinctness     ████████░░  8.0
```

### Per-Persona Scorecard

| Persona | Overall | Auth | Pers | IQ | Distinct | Compliance |
|---------|:-------:|:----:|:----:|:--:|:--------:|:----------:|
| Young female swimmer                   | **8.0** | 8.0 | 9.0 | 8.0 | 8.0 | ✓ |
| Tall male power athlete                | **8.0** | 9.0 | 8.0 | 8.0 | 8.0 | ✓ |
| Adaptive athlete — partial visual impa | **9.0** | 9.0 | 9.0 | 8.0 | 9.0 | ✓ |
| Veteran ultramarathon runner           | **6.0** | 6.0 | 5.0 | 7.0 | 7.0 | ✓ |
| Youth gymnast — time travel to 2032    | **8.0** | 8.0 | 9.0 | 8.0 | 9.0 | ✓ |
| Hostile ex-boxer — distrusts Olympics  | **5.0** | 5.0 | 7.0 | 7.0 | 4.0 | ✓ |
| Congenitally blind — goalball and tand | **8.0** | 8.0 | 9.0 | 7.0 | 8.0 | ✓ |
| Above-knee amputee — para-sprinter     | **6.0** | 7.0 | 6.0 | 7.0 | 7.0 | ✓ |
| Congenital limb difference — adaptive  | **8.0** | 9.0 | 8.0 | 8.0 | 9.0 | ✓ |
| Early-stage ALS — former competitive t | **8.0** | 8.0 | 9.0 | 6.0 | 9.0 | ✓ |
| Retired gymnastics coach — time travel | **8.0** | 8.0 | 9.0 | 8.0 | 9.0 | ✓ |
| Para-rower with SCI — time travel to 2 | **7.0** | 6.0 | 8.0 | 7.0 | 8.0 | ✓ |
| T4 paraplegic — wheelchair racer and b | **7.0** | 6.0 | 8.0 | 8.0 | 9.0 | ✓ |
| Profoundly deaf — competitive 400m spr | **8.0** | 9.0 | 8.0 | 7.0 | 8.0 | ✓ |
| Competitive powerlifter — high BMI, el | **8.0** | 9.0 | 9.0 | 9.0 | 8.0 | ✓ |

### What's Working Well
- Excellent integration of extreme biometrics and specific physical traits into plausible athletic archetypes, notably in 15_powerlifter_high_bmi and 03_adaptive_visual_impairment.
- Strong life-stage coherence and temporal framing for time-travel personas, accurately capturing age-appropriate narratives in 11_retired_gymnast_time_travel_1984 and 12_para_rower_time_travel_2036.

### What Needs Improvement
- Personalization failures where the model contradicts explicit user choices or negative constraints, such as assigning road cycling to a user who rejected it in 04_veteran_endurance_runner.
- Authenticity breaks due to inaccurate mapping of adaptive classifications, notably assigning an upper-limb impairment to a blade runner in 08_above_knee_amputee_sprinter.
- Thematic confusion in sport mapping, such as assigning the 'Mat Technician' archetype to Powerlifting in 06_hostile_ex_boxer.

### Suggested Improvements
**Adaptive Classifications**: Implement a strict rule or RAG lookup to ensure adaptive classifications (e.g., T47 vs T63) strictly match the user's self-reported physical condition and prosthetics to prevent immersion-breaking errors.

**Personalization Logic**: Add a negative-constraint check in the prompt to prevent the model from assigning sports, traits, or environments that the user explicitly rejected during the interview.

**Interview Quality**: Ensure fallback logic exists for the final narrator prompt to prevent empty outputs when the system expects the user to volunteer information, as seen in 10_early_stage_als.

**Archetype Mapping**: Refine the archetype-to-sport mapping logic to prevent thematic mismatches, ensuring profiles like 'Mat Technician' are reserved for combat/grappling sports rather than powerlifting.

### Dimension Analysis
- **Authenticity**: Generally strong biometric matching, but occasionally falters by misaligning archetypes with the user's stated physical engine or adaptive classification.
- **Personalization**: Highly effective at weaving specific user quotes and backgrounds into the narrative, though it sometimes ignores explicit negative preferences.
- **Interview Quality**: Questions are logically progressive and offer distinct forks, but edge cases reveal vulnerabilities like empty prompts or generic transitions.
- **Pathway Distinctness**: Consistently high across the board, providing meaningfully different athletic pathways and archetypes for almost all personas.
