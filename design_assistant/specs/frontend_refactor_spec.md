# Specification: Frontend UI/UX Refactor

## Frontend Refactor Specification

**Objective:** To refactor the frontend application to align with a simpler, single-page voice assistant design, as referenced by the user. The goal is to create a more immersive, full-screen conversation experience, moving away from the current multi-step dashboard and session flow.

### 1. Core UI and Layout

- **Single-Page Design:** The application will load directly into the voice assistant interface, removing the initial dashboard/start page.
- **Full-Screen Experience:** The conversation UI will occupy the majority of the viewport, creating an immersive feel.
- **Layout Structure:**
    - A large `AgentVisualizer` component will be the primary visual element at the top of the screen. This will display the agent's video or a bar visualizer for its audio.
    - A `TranscriptionView` component will be displayed prominently below the visualizer, occupying the remaining vertical space.
    - A minimalist `ControlBar` will be present at the bottom of the screen for essential actions like muting and disconnecting.

### 2. Component Behavior

- **`page.tsx`:** This will be the main entrypoint. It will be simplified to manage the `Room` connection and render the `SimpleVoiceAssistant` component directly. The multi-step logic involving `Dashboard` and `LiveSession` will be removed.
- **`AgentVisualizer`:** A new or refactored component that is much larger than the current `AgentOrb`. It will display the agent's video track if available, otherwise it will show a prominent `BarVisualizer`.
- **`TranscriptionView.tsx`:** This component will be refactored into a "smart" component.
    - It will be responsible for fetching its own data by using the `useChat` hook internally.
    - It will no longer receive `chatMessages` as a prop.
    - It will manage its own scroll behavior to automatically show the latest messages.
- **`SimpleVoiceAssistant`:** This will be the primary component rendered in `page.tsx`. It will orchestrate the display of the `AgentVisualizer`, `TranscriptionView`, and `ControlBar`.

### 3. User Flow

1.  **Initial Load:** The user opens the application and is immediately presented with a "Start a conversation" button.
2.  **Connection:** Upon clicking the button, the application connects to the LiveKit room.
3.  **Conversation View:** Once connected, the UI transitions to the main conversation view:
    - The large agent visualizer appears.
    - The transcription view is ready to display messages.
    - The control bar is visible.
4.  **Disconnection:** The user can end the session by clicking the disconnect button in the control bar, which will return them to the initial "Start a conversation" screen.

### 4. Out of Scope for this Refactor

-   Backend agent logic (which is now stable).
-   Changes to the existing `design-database` or other backend services.
-   The multi-agent persona logic (the UI will only reflect the currently speaking agent).

---

## 1. Vision: Voice-First Design Thinking Assistant

To build a sophisticated, production-ready web application that helps users transform vague ideas into structured, actionable insights through an AI-powered conversation. The application will embody a premium, Apple-level design aesthetic, providing a seamless and intuitive user experience.

---

## 2. Core Requirements & Features

### A. Voice-First Interface
-   **Real-time Speech Recognition:** Live transcription of user's voice.
-   **Dynamic Audio Visualization:** An audio waveform that visually responds to voice input.
-   **State Management:** Clear visual indicators for voice states (e.g., listening, processing, idle).

### B. AI Agent System
-   **Distinct Personas:**
    -   **Coach:** Empathetic guide (blue theme).
    -   **Strategist:** Systems thinker (green theme).
    -   **Evaluator:** Critical analyst (purple theme).
-   **Animated Agent Orbs:** Visual representation of agents that pulse and respond to audio levels.
-   **Intelligent Agent Switching:** The backend will continue to handle agent transitions, and the UI must reflect these changes smoothly.

### C. Session Management
-   **Full Lifecycle:** Clear flow from session start to a final summary and action items.
-   **Session History Dashboard:** A central place to view past sessions (both active and completed) with relevant statistics.
-   **Persistence:** The backend database will persist all session data.

### D. Clarity Capsules (Structured Summaries)
-   **Content:** Generate summaries including an executive summary, key insights, action items, and next steps.
-   **User Interaction:** Allow for adding personal notes, tagging, and bookmarking.
-   **Export:** Provide functionality to export summaries to Markdown or a Notion-ready format.

---

## 3. Design System & Aesthetics

### A. Visual Style
-   **Aesthetic:** Clean, editorial, inspired by Linear, Notion, and Apple Journal.
-   **Color:** Ambient color palette with gradient accents for different agents.
-   **Effects:** Use of glass morphism with a backdrop blur for a modern feel.
-   **Layout:** Mobile-first, responsive design.

### B. Typography & Layout
-   **Fonts:** System fonts with a clear hierarchy.
-   **Spacing:** Consistent 8px grid system.
-   **Style:** Rounded corners (12px-24px) and subtle shadows for depth.

### C. Animations & Micro-interactions
-   **Core Animations:** Floating agent orbs, pulsing effects during voice interaction, smooth page transitions, waveform visualizations, and fade-in/slide-up content reveals.
-   **Goal:** All animations should be smooth (60fps) and enhance the user experience.

---

## 4. Key Screens & User Flow

1.  **Dashboard:** The main entry point. Displays session history, key stats, and a prominent call-to-action to start a new session.
2.  **Live Session:** The core interactive screen. Features the real-time voice conversation, agent orb, and live transcription.
3.  **Summary / Clarity Capsule:** A view to generate, preview, and edit the structured summary post-conversation.
4.  **Post-Session / Action Center:** A dedicated view for a completed session's Clarity Capsule, allowing for export, sharing, and note-taking.

---

## 5. Quality Standards & Success Criteria

-   **Code Quality:** Production-ready, maintainable component architecture.
-   **Responsiveness:** The UI works flawlessly across all major device viewports (desktop, tablet, mobile).
-   **Performance:** All animations and interactions are fluid and performant.
-   **Accessibility:** Voice controls have clear visual feedback.
-   **Error Handling:** Gracefully handles potential issues, such as an unsupported browser. 