# Spec Plan: Multi-Agent Workflow (First Pass)

## Goal
Implement the multi-agent workflow (Coach → Strategist → Evaluator) with clear agent transitions and workflow state, without connecting to backend data or persistent storage.

---

## Scope (First Pass)
- Implement three agents: **Design Coach**, **Design Strategist**, **Design Evaluator**.
- Agents should:
  - Greet and interact with the user according to their role.
  - Pass control to the next agent at the appropriate trigger.
  - Maintain and update a simple in-memory workflow status (e.g., `status` field).
- No backend data storage or retrieval in this phase.

---

## Workflow Steps
1. **Design Coach (Triage)**
   - Greets the user.
   - Clarifies emotional/strategic intent.
   - When ready, outputs:  
     `Strategist, take it from here.`  
     and sets `status = "awaiting_problem_definition"`

2. **Design Strategist**
   - Asks one question at a time.
   - Helps user define Problem Statement and Proposed Solution.
   - When user provides both, outputs:  
     ```
     Problem Statement: ...
     Proposed Solution: ...
     Coach, we're ready for evaluation.
     ```
     and sets `status = "ready_for_evaluation"`

3. **Design Coach (handoff)**
   - Detects readiness for evaluation.
   - Passes control to Evaluator.

4. **Design Evaluator**
   - Receives Problem Statement and Proposed Solution.
   - Returns structured feedback (score, strengths, improvements, focus).
   - Sets `status = "evaluation_complete"`

---

## Agent Communication
- Use a shared in-memory object (e.g., `UserData` with a `status` field) to track workflow state and agent transitions.
- Each agent checks the `status` to determine when to act or hand off.

---

## Out of Scope (for First Pass)
- No database or persistent storage.
- No customer/order data integration.
- No frontend/backend API changes.

---

## Success Criteria
- Agents transition smoothly through the workflow in memory.
- Each agent performs its role and hands off at the correct trigger.
- The workflow can be simulated end-to-end without backend data. 