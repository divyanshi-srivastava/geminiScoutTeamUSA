# 🏟️ Gemini Scout: The Living Legacy Vision

## **The Core Philosophy**
Gemini Scout is not a calculator; it is a **Time-Traveling Talent Scout**. It doesn't just categorize an athlete—it discovers a legacy. By blending high-fidelity logic with a conversational, personalized narrative, we bridge the gap between "what you are" and "who you can become" within the Team USA ecosystem.

---

## **The User Experience: "The Great Interview"**

### **1. The Narrator-Led Onboarding**
Instead of a cold form, the user meets the **Narrator Agent**. This is a dynamic, conversational interface where the Narrator controls the flow:
* **Intelligent Q&A:** The Narrator asks targeted questions (e.g., "Do you play sports currently?", "How often do you train?") using a mix of engaging **multiple-choice chips** and **free-text inputs**.
* **Empathetic Feedback:** The agent provides real-time encouragement, reacting to user inputs (e.g., *"Training twice a week? That's a solid foundation—we can work with that!"*).
* **The Transition:** Once the Narrator has gathered enough context, it asks the final permission: *"Are you ready to see your archetype, or is there anything else you want me to know?"*

### **2. The "Mission Control" Scouting Phase**
As the backend agents process the "Athlete Combine Data," the user remains engaged with the Narrator while the **Logger Agent** provides a separate "Judge's View":
* **Audit Trace:** A real-time terminal window showing the technical "thoughts" of the agents, providing total transparency into the AI's reasoning.
* **The Fact Spinner:** Historical Team USA trivia keeps the user immersed in the legacy while the agents finalize the mapping.

### **3. The Multi-Dimensional Result**
The user receives their **Archetype Match** (e.g., *The Leverage Grappler*), but the journey doesn't end there:
* **Personalized Narrative:** The Narrator Agent crafts a story justifying the match, specifically referencing the user's conversation.
* **The Legacy Timeline:** A navigation bar appears at the top. Users can "Time Travel" by clicking different ages or stages on the bar. 
* **Temporal Evolution:** As the user moves through the timeline, the Narrator explains how their archetype progresses over time (e.g., *"At 30, your grounded leverage shifts into strategic coaching potential..."*).

---

## **The Multi-Agent Orchestration (The Hub-and-Spoke)**

The system operates through five specialized agents managed by a **Supervisor**:

| Agent | Responsibility |
| :--- | :--- |
| **Supervisor** | The Director. Manages state transitions and orchestrates agent hand-offs. |
| **Narrator** | **The Face.** Controls the Q&A, personalizes the story, and handles "Time Travel" shifts. |
| **Scout** | **The Logic.** Performs the heavy lifting of mapping physical metrics to the athletic manifest. |
| **Compliance** | **The Guard.** Enforces hackathon standards (e.g., naming conventions). |
| **Logger** | **The Reporter.** Translates technical steps into "vocal" logs for the Audit Trace. |

---

## **Technical Innovation**
* **Contextual Memory:** The Narrator remembers the user’s answers from the initial Q&A to influence the "Time Travel" descriptions.
* **Hybrid Streaming:** The UI consumes an SSE (Server-Sent Events) stream that delivers both "Trace Logs" for the judges and "Narrative Content" for the user simultaneously.
* **Modular Extensibility:** The separation of Logic (Scout) and Voice (Narrator) allows for independent updates to the "vibe" without breaking the "math."