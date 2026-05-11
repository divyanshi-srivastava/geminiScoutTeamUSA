# v2 — SequentialAgent (Day 3)

## Design

Removed the Supervisor LLM entirely. Mode selection (which pipeline to run) moved to Python in `streamer.py`. Agent ordering moved to ADK's `SequentialAgent`, which uses a deterministic Python loop — no LLM routing, no AFC.

```
Python mode selection (streamer.py)
  ├── INTERVIEW:              SequentialAgent([narrator_agent, compliance_agent])
  ├── SCOUTING:               SequentialAgent([scout_agent, narrator_agent, compliance_agent])
  └── TIME_TRAVEL_INTERVIEW:  SequentialAgent([narrator_agent, compliance_agent])
```

Between agents, `output_key` on each `LlmAgent` writes its result to the ADK session state. The next agent reads it via `{output_key}` placeholders in its instruction template.

## What Improved

- SCOUTING pipeline now reliably executes all three agents in order, every time
- Removed one full LLM call per request (the supervisor), reducing latency
- Eliminated the session state accumulation bug (old supervisor replayed routing decisions from prior requests via `InMemorySessionService`; each request now runs a fresh session)
- Compliance correctly reviews the full narrated output, not raw scout JSON

## New Failure Modes Discovered (via benchmark)

With the pipeline now reliable, the first benchmark run (15 personas) revealed quality issues inside the agents themselves:

- **Gender hallucinations**: Scout was recommending "Men's +100kg Powerlifting" to 60kg female athletes. Root cause: `pathway_manifest.json` had gendered event examples hardcoded in the `adaptive` field; scout copied them verbatim.
- **Duplicate pathways**: Standing and adaptive results told the same story with different sport names. Root cause: no structural enforcement of dimension distinctness.
- **Thin adaptive narratives**: Some adaptive `scout_verdict` fields were 20 words vs 300-word standing verdicts. Root cause: compliance parity rule was advisory, not rewrite-on-violation.
- **Catch-all interview options**: Options like "balanced mix", "open to anything" produced interview data that couldn't meaningfully differentiate archetypes.
- **Archetype hallucinations**: Scout was inventing profile names not present in the manifest — outputting names like "Tactical Scholar", "The Strategist", and "Rising Star Analyst" when a clean biometric match was ambiguous. Root cause: no constraint requiring output to match manifest profile IDs and names exactly; the LLM interpolated plausible-sounding archetypes rather than selecting from the 14 available.
