# 🏁 Team USA x Google Cloud Hackathon: Submission Checklist & Judging Guide

This document serves as the final checklist and judging reference for the **Gemini Scout** project. It has been distilled from the official rules to ensure 100% compliance.

---

## ⚖️ Judging Criteria (Weighted)

### 1. Impact (40%)
*   **Fan-Centric:** Does it solve a real question for Team USA fans?
*   **Visionary:** Is the solution inspiring and potentially impactful?
*   **Parity:** Does it demonstrate strong Paralympic representation alongside Olympic data?

### 2. Technical Depth & Execution (30%)
*   **Functionality:** Does the app work consistently as described?
*   **Gemini Integration:** How effectively are Gemini’s multimodality, reasoning, and context utilized?
*   **Google Cloud:** Is it well-engineered and deployed using Google Cloud services (Cloud Run, etc.)?
*   **Innovation:** Are Gemini and Google Cloud used in novel or creative ways?

### 3. Presentation Quality (30%)
*   **Storytelling:** Does the demo video tell a powerful, engaging story?
*   **UX/UI:** Does it showcase a premium user experience?
*   **Compliance:** Does the presentation strictly follow all content and NIL restrictions?

---

## ✅ Submission Checklist

### 🏗️ Technical Requirements
- [x] **Core AI:** Must use Gemini API (Vertex AI or Google AI Studio) for core logic.
- [x] **Deployment:** Must be hosted on a Google Cloud service (e.g., Cloud Run).
- [x] **Public Repo:** Code must be in a public repository (GitHub, GitLab, etc.).
- [x] **License:** Must include the **Apache License 2.0** (clearly visible in the repo).

### 📝 Submission Deliverables
- [x] **Hosted URL:** A link to the live, working application.
- [ ] **Text Description:** Features, functionality, tech stack, data sources, and findings.
- [ ] **Video Demo:** Max 3 minutes, YouTube **Unlisted**.
    - [ ] Show live app functionality.
    - [ ] Show behind-the-scenes (GCP Console, AI Studio, or Code).
    - [ ] English language (or English subtitles).

### 🛑 Compliance & Restrictions (CRITICAL)
- [x] **No NIL:** Absolutely no individual athlete names, images, or likenesses.
- [x] **Animations Only:** Any AI-generated media must be animations; no real human likeness.
- [x] **No IOC Branding:** No Olympic Rings, No Torch, No official IOC/USOPC logos.
- [x] **Data Integrity:** No finish times or specific scoring (Placement and Medals only).
- [x] **Terminology:**
    - [x] Avoid "Olympic Games" in the app title (Use "Team USA x Google Cloud Hackathon" branding).
    - [x] Never use "Former" or "Past" Olympian/Paralympian.
    - [x] Refer to LA28 as "LA28 Games" or "LA28 Olympic and Paralympic Games".
- [x] **Parity:** Ensure Olympic and Paralympic athletes are treated with equal prominence.
- [x] **Privacy:** Do not collect or store PII (Personally Identifiable Information).

---

## 🔎 Rule Audit Results (Internal Review)

| Rule | Status | Notes |
| :--- | :--- | :--- |
| **Data Filter** | ✅ PASS | Using US-only Kaggle datasets. |
| **No Scoring** | ✅ PASS | Using Archetypes and placements, no finish times. |
| **Branding** | ✅ PASS | No rings or torch logos; custom SVG icons used. |
| **NIL** | ✅ PASS | Archetype-based results; no individual athlete profiles. |
| **Terminology** | ✅ PASS | All 'Olympic' references removed in favor of generic terms like 'The Games' or 'Historical Archives'. |
| **Deployment** | ✅ PASS | Prepared for Google Cloud Run deployment. |
| **Parity** | ✅ PASS | Data model and UI treat both cohorts with equal prominence. |

---
*Last updated: May 2026*