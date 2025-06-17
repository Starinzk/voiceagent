# Specification: Session Loading Feature

## 1. Goal

To implement a robust feature that allows returning users to load and continue a previous design session. This will be achieved using a **State-Driven Transition** model to avoid the framework conflicts encountered previously.

---

## 2. Core Architecture: State-Driven Transitions

The central principle is to decouple state manipulation from agent control flow. Agent tools will primarily be responsible for updating a central `UserData` state object. The decision to transfer agents will be based on this state, handled by dedicated tools.

---

## 3. Implementation Plan

### Step 1: `UserData` State Enhancement

The `UserData` dataclass in `design_assistant.py` will be updated to support the session loading flow.

-   **Add `pending_session_id`:**
    -   A new field, `pending_session_id: Optional[str] = None`, will be added.
    -   This field will temporarily store the ID of a session that a user has agreed to load, bridging the gap between the user's confirmation and the actual loading action.

### Step 2: `DesignCoachAgent` Tool Refactoring

The tools on the `DesignCoachAgent` will be modified to follow the state-driven model.

1.  **Modify `identify_user` Tool:**
    -   **No longer returns `Agent`**. It will return a `str`.
    -   Upon identifying a user, it will call `db.get_user_sessions(user_id)`.
    -   If sessions exist, it will ask the user if they want to load one and list the available sessions (e.g., by `design_challenge` and `created_at`).
    -   The LLM will then use this information to interact with the user.

2.  **Add `select_session_to_load` Tool:**
    -   **Returns a `str`**.
    -   This new tool will take a `session_id` as an argument.
    -   It will set the `UserData.pending_session_id` with the provided `session_id`.
    -   It will confirm to the user that the session is ready to be loaded and instruct them to say "continue" or "proceed".

3.  **Add `load_selected_session` Tool:**
    -   **Returns `Agent`**. This tool will be an `async generator` and will be responsible for the agent transfer.
    -   It will have no arguments.
    -   It reads the `session_id` from `UserData.pending_session_id`.
    -   It calls `userdata.load_state(session_id)` to populate the `UserData` object with the session's data.
    -   Crucially, it will inspect the `status` of the loaded `UserData` and transfer the user to the appropriate agent (`DesignStrategist` or `DesignEvaluator`).
    -   This isolates the agent transfer logic into a single, dedicated tool, preventing framework conflicts.

### Step 3: `design_coach.yaml` Prompt Updates

The instructions for the `DesignCoachAgent` will be updated to guide the LLM through the new, more nuanced workflow:

-   **Step 1:** Call `identify_user`.
-   **Step 2:** Based on the tool's output, if the user has previous sessions, present them as options.
-   **Step 3:** If the user chooses a session, call `select_session_to_load` with the corresponding `session_id`.
-   **Step 4:** When the user gives the final confirmation to proceed, call `load_selected_session`.
-   **Alternative Path:** If the user is new or wants to start a new project, the prompt will guide the LLM to use the existing `capture_design_challenge` and `transfer_to_strategist` flow.

---

## 4. Success Criteria

-   A returning user is successfully identified and prompted with a list of their previous sessions.
-   The user can select a session, which is then loaded correctly into the `UserData` state.
-   The user is seamlessly transferred to the correct agent based on the loaded session's status.
-   The system remains stable, with no `TypeError` or `AttributeError` issues related to mixed tool return types. 