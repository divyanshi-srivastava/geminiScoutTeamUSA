# v1 — Supervisor Agent (Days 1–2)

## Design

A single "Supervisor" LLM agent was the central orchestrator. It held all mode logic and called sub-agents via ADK's `transfer_to_agent` tool.

```
Request
  └── supervisor_agent
        ├── transfer_to_agent("narrator_agent")
        ├── transfer_to_agent("compliance_agent")
        └── [for SCOUTING]: transfer_to_agent("scout_agent")
                             transfer_to_agent("narrator_agent")
                             transfer_to_agent("compliance_agent")
```

## What Broke

SCOUTING required three sequential hops (scout → narrator → compliance). The pipeline always terminated after the first hop. The event trace always looked like:

```
supervisor → supervisor → scout_agent  [STOPPED]
```

Narrator was never called. The user received raw scout JSON with no narrative.

**Root cause:** ADK's `transfer_to_agent` is a `FunctionDeclaration` (schema-only), not a Python callable. Google ADK's Automatic Function Calling (AFC) loop requires Python callables to execute. With a schema-only tool, AFC was disabled — the supervisor made one transfer, the sub-agent ran and returned, and ADK treated that return as the final answer.

INTERVIEW worked coincidentally because it only required one real hop (narrator). Compliance was being called by the streamer as a post-loop synthetic step, not by the supervisor.

## What Was Tried

Eight approaches were exhausted before reaching this diagnosis. Full decision log: [supervisor-agent-postmortem.md](../supervisor-agent-postmortem.md).

The key insight: `transfer_to_agent` is designed for *handoff* (permanent transfer of control), not *orchestration* (return result to caller, chain next step).
