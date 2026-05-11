# Supervisor Agent — Decision Log & Postmortem

## What It Was Supposed to Do

The Supervisor Agent was designed as the central orchestrator of the Gemini Scout multi-agent pipeline. Its role was to:

- Read a `[SYSTEM: MODE]` header (INTERVIEW / SCOUTING / TIME_TRAVEL_INTERVIEW) from every incoming request
- Route to the correct sub-agents in the correct order
- Forward biometric data, conversation history, and mode directives to each sub-agent verbatim
- Pass each agent's output to the next as input
- Return the final compliance-reviewed JSON to the streamer

The intended pipelines were:
- **INTERVIEW**: narrator → compliance
- **SCOUTING**: scout → narrator → compliance
- **TIME_TRAVEL_INTERVIEW**: narrator → compliance (with era context)

The supervisor was built using Google ADK's `Agent` class with `sub_agents=[scout_agent, narrator_agent, compliance_agent]`, which exposed a `transfer_to_agent(agent_name: str)` tool for routing.

---

## The Core Problem

In SCOUTING mode, the supervisor consistently stopped after calling the first agent. The event sequence always looked like:

```
supervisor_agent → supervisor_agent → scout_agent
```

Narrator was never called. The frontend received scout's raw JSON as the final result — unnarrated, unreviewed.

INTERVIEW mode worked because it only required **one hop** (narrator). SCOUTING required **three sequential hops** (scout → narrator → compliance), which never worked reliably.

---

## Root Cause (Confirmed)

Google ADK exposes `transfer_to_agent` as a **FunctionDeclaration** (schema-only), not a Python callable. When the supervisor tried to use it, the Google GenAI SDK's **Automatic Function Calling (AFC)** loop was disabled because AFC requires Python callables to execute.

With AFC disabled:
- The supervisor made one `transfer_to_agent` call
- The sub-agent ran and returned output
- The ADK runner treated the sub-agent's output as the **final answer** and terminated
- The supervisor never received the sub-agent's result to make the next call

INTERVIEW worked coincidentally because `narrator → compliance` was two hops, but compliance was being called via the streamer's synthetic trace mechanism (post-loop), not by the supervisor. The supervisor was effectively only making one real hop even in INTERVIEW.

---

## Everything That Was Tried

### 1. Prompt Engineering (`supervisor.md`)
Created a dedicated `supervisor.md` instruction file to replace the inline string. Wrote explicit step-by-step instructions with ordering rules including:
- `⚠ CRITICAL ORDERING RULE: scout_agent MUST be the FIRST agent you call`
- Explicit warnings not to call narrator before scout
- Verbatim forwarding rules for all system headers
- Failure path definitions

**Result**: No effect. The supervisor's thinking tokens showed it understood the instructions correctly — it just couldn't execute multi-hop routing due to the AFC limitation.

### 2. Gap Review and Fixes
Reviewed `supervisor.md` for all instruction gaps (found 10), including missing biometric forwarding, missing `ready_to_proceed` preservation, missing TIME_TRAVEL header forwarding. Fixed all gaps.

**Result**: Improved INTERVIEW quality. No effect on SCOUTING ordering.

### 3. Thinking Tokens (8192 budget)
Added `thinking_config=types.ThinkingConfig(include_thoughts=True, thinking_budget=8192)` to the supervisor. This revealed the supervisor's full reasoning in the backend logs. The thoughts confirmed the supervisor correctly identified the right order but still failed to execute it.

Notable finding: the supervisor's thinking showed it understood the `transfer_to_agent` limitation — it knew it couldn't explicitly forward headers via the tool signature and was trusting ADK to pass context implicitly.

**Result**: Valuable for diagnosis. No effect on routing.

### 4. Model Selection
The supervisor was initially configured with an unspecified model, later locked to `gemini-3.1-flash-lite` (the same lite tier all in-pipeline agents settled on).

**Result**: No meaningful difference in routing reliability observed across model variants tested.

### 5. Session Isolation (Fresh Session Per Request)
Discovered that `InMemorySessionService` was accumulating the full conversation history including function calls. On subsequent requests, ADK replayed prior routing decisions from session history — the supervisor was being bypassed entirely after the first request. Switched to `uuid.uuid4()` session ID per request to force a clean slate each time.

**Result**: Fixed INTERVIEW (supervisor now re-routes correctly on every turn). SCOUTING still stopped after scout — the AFC limitation was independent of session history.

### 6. Removing `google_search` from `scout_agent`
Scout had `tools=[google_search]` attached. The hypothesis was that `google_search` as a FunctionDeclaration in the sub-agents list was causing AFC to be disabled for the supervisor. Removed the tool entirely (scout doesn't need web search — the manifest is embedded in its instruction).

**Result**: The AFC disabled warning persisted. Pipeline still stopped after scout.

### 7. SequentialAgent Evaluation
Researched ADK's `SequentialAgent` as the correct primitive for guaranteed sequential pipelines. Confirmed it exists in ADK 0.1.0+ (project is on 1.32.0), uses a deterministic Python loop, and solves the AFC problem entirely — no LLM routing, no `transfer_to_agent`, no AFC.

Key finding: `output_key` on `LlmAgent` + `{placeholder}` in downstream instructions is the mechanism for passing outputs between sequential agents.

**Result**: Would solve ordering. But requires separate pipelines per mode and removes the need for a supervisor LLM entirely. If SequentialAgent handles ordering, and mode selection is done in Python (which the streamer already does), the supervisor has no remaining function.

### 8. Google Agent Consultation
Shared the problem with a Google model for an independent diagnosis. It confirmed:
- The "single-hop termination" hypothesis is correct
- The chain approach (each agent calls the next) is viable but makes agents topology-aware
- `SequentialAgent` is the proper ADK solution

---

## Why the Supervisor Was Removed

After exhausting ADK-level solutions, the conclusion was:

1. **The routing logic doesn't require an LLM.** The MODE is explicitly set in Python in the streamer before any agent is called. An LLM reading a string we wrote is not intelligence — it's overhead.

2. **The supervisor added latency and cost with no reliability gain.** Every request consumed one full LLM call (with 8192 thinking tokens) before any real work started. That call was the source of every pipeline bug in the system.

3. **SequentialAgent makes the supervisor redundant.** If SequentialAgent handles ordering and Python handles mode selection, the supervisor's job is reduced to a three-line `if/elif`. There is no justification for an LLM to do that.

4. **The system is stable and the modes are well-defined.** The supervisor design made sense at the start when routing complexity was unknown. With three fixed modes and a known pipeline per mode, the routing is a solved problem in code.

The decision: remove the supervisor agent and replace with Python mode selection + SequentialAgent pipelines (or direct Python sequencing in the streamer).

---

## What Was Learned

- `transfer_to_agent` in ADK is designed for **handoff**, not **orchestration**. It transfers control permanently and does not return a result to the caller for chaining.
- AFC requires Python callables. FunctionDeclarations (schema-only tools) disable AFC, breaking multi-hop loops.
- LLM-based routing for deterministic pipelines is the wrong tool. When you know the order at design time, enforce it in code.
- Session state in `InMemorySessionService` accumulates function calls and can replay routing decisions, bypassing the LLM entirely on subsequent requests.
- `SequentialAgent` + `output_key` is the correct ADK primitive for guaranteed sequential pipelines.
