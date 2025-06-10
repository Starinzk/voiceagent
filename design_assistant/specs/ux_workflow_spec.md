# UX & Workflow Specification

## 1. Project Goal

To define and implement a clear, intuitive, and persistent user experience by specifying the frontend UI, refining the backend agent logic for seamless state transitions, and creating the necessary API endpoints to support a fully interactive and stateful design session.

---

## 2. Target Audience & Core Problem

*This section will formalize who this application is for and the specific problem it solves.*

- **Target Audience:** Product Managers, UX/UI Designers, Entrepreneurs, and anyone in the early stages of creative development.
- **Core Problem:** To overcome the "blank page" problem and the loss of creative history by providing a structured, persistent, and collaborative partner for the design ideation process.

---

## 3. Core User Flow

*This section details the step-by-step journey a user takes through the application, including frontend and backend interactions.*

1.  **Onboarding & Session Initiation:**
    - **User Action:** Connects to the application.
    - **Frontend:** Displays a welcome screen with a "Begin Session" button.
    - **Backend:** The `DesignCoachAgent` is active and waiting.
    - **User Action:** Clicks "Begin" and, when prompted, states their name ("My name is Jane Doe").
    - **Backend:** The `identify_user` tool is called. The `db.get_or_create_user` method finds or creates a user record. If the user is returning, the agent could offer to load a previous session.
    - **Agent Dialogue (Coach):** "Thanks, Jane. Great to have you. Now, what's the big idea? Tell me about the design challenge you want to tackle."

2.  **Problem Definition & Refinement:**
    - **User Action:** Describes their high-level design challenge (e.g., "An app for community gardening").
    - **Agent Dialogue (Coach):** "That sounds interesting. To help us get focused, who are the primary users you're designing for?"
    - **User Action:** Describes the target users.
    - **Agent Dialogue (Coach):** "And when they use it, what key emotions do you want them to feel?"
    - **User Action:** Describes the emotional goals.
    - **Backend:** The `capture_design_challenge` tool is called. It populates `design_challenge`, `target_users`, and `emotional_goals` in the `UserData` object. `userdata.save_state()` is called, creating a new record in the `design_sessions` table.
    - **Agent Dialogue (Coach):** "Excellent. I've captured the core of your challenge. I'm now handing you over to our Design Strategist, who will help you refine this into a clear problem statement."
    - **Frontend:** Shows a clear visual transition, e.g., the agent's avatar, name, and color theme change from "Design Coach" to "Design Strategist".

3.  **Ideation & Iteration:**
    - **Agent Dialogue (Strategist):** "Hello, I'm the Design Strategist. Let's frame this as a 'How might we...' question. How would you state the core problem you're trying to solve?"
    - **User Action:** Collaborates with the agent to create a problem statement.
    - **Backend:** The `refine_problem_statement` tool is called. `userdata.save_state()` updates the `problem_statement` in the current design session.
    - **Agent Dialogue (Strategist):** "That's a strong problem statement. Now, let's brainstorm a potential solution. What's one approach we could take?"
    - **User Action:** Proposes a solution.
    - **Backend:** The `propose_solution` tool is called. A new record is created in the `design_iterations` table, linked to the current session. `userdata.save_state()` is called.
    - **Frontend:** The new iteration instantly appears in the "History View" panel.

4.  **Evaluation & Feedback (Future Scope):**
    - The `Design Strategist` hands off to the `Design Evaluator`.
    - The `Design Evaluator` provides structured feedback on proposed solutions, which is saved in the `feedback_history` table.

---

## 4. Frontend UX/UI Requirements

*This section defines the specific visual components of the frontend experience.*

- **Initial State:** A minimal welcome screen with a single, prominent "Begin Session" button. A small, secondary link "View Past Sessions" can be included.
- **Onboarding View:** A clean, modern chat interface. The agent's name (`Design Coach`) and avatar are clearly displayed. A microphone button provides visual feedback (e.g., pulsing) when listening.
- **Session View:** A persistent sidebar or header that is always visible after the session starts. It displays the key, static session data: **Design Challenge**, **Target Users**, and **Emotional Goals**.
- **Agent Transition View:** When an agent handoff occurs, there should be a clear and explicit visual event. The agent name, avatar, and possibly a background color or accent theme should change to reflect the new agent.
- **History View:** A scrollable side panel that displays a list of all `design_iterations` for the current session. Each item should be a card showing the `problem_statement`. Clicking a card should expand it to reveal the corresponding `solution` details.
- **Real-time Feedback:**
    - **Listening:** The microphone icon pulses or a waveform is displayed.
    - **Thinking:** A subtle animation (e.g., a "typing" indicator or a soft spinner) appears next to the agent's avatar to manage user expectations during LLM latency.
    - **Speaking:** The agent's avatar is highlighted, and the live transcript of their speech is displayed word-by-word.

---

## 5. Backend API & Agent Logic Requirements

*This section details the necessary backend changes to support the frontend experience and improve robustness.*

- **Agent Handoff Logic:**
    - The agent transition logic must be refactored to be deterministic and state-driven, eliminating loops.
    - Transitions should be strictly controlled by the `UserData.status` field.
    - **Example:** The `DesignCoach` can only hand off when `status` is `awaiting_problem_statement`. After the handoff, the `DesignStrategist` sets the status to `ready_for_evaluation`.
- **Real-time State Synchronization:**
    - The backend must proactively push state changes to the frontend.
    - This will be implemented using LiveKit's data channels. After every call to `userdata.save_state()`, the backend will serialize the relevant parts of the `UserData` object and broadcast it to the frontend.
    - The frontend will have a listener on the data channel to receive these updates and re-render the UI (e.g., the Session View and History View) as needed.
- **Session History API:**
    - A new method, `get_all_user_sessions(user_id: str)`, will be added to `design_database.py`. This method will return a list of all past design sessions for a given user.
    - A corresponding agent tool, `list_past_sessions`, will be created for the `DesignCoach` to use during onboarding.

---

## 6. Out of Scope for this Phase

*What we are explicitly NOT doing right now.*

-   User authentication (we will continue with simple name-based identification).
-   Full implementation of the `Design Evaluator`'s feedback and scoring logic.
-   Multi-user collaboration or session sharing. 