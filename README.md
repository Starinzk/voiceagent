
## Overview

**Design Assistant** is a multi-agent conversational system that guides users through the creative process, from clarifying intent to structured critique.  
This project replaces the original "Personal Shopper" with a design-focused, human-centered workflow.

---

## Multi-Agent Workflow

The system uses three coordinated AI agents:

1. **Design Coach**  
   - Welcomes the user and clarifies emotional/strategic intent.
   - Hands off to the Strategist when ready.

2. **Design Strategist**  
   - Asks one question at a time to help the user define a Problem Statement and Proposed Solution.
   - Returns this package to the Coach for evaluation handoff.

3. **Design Evaluator**  
   - Scores and critiques the Problem Statement and Proposed Solution.
   - Provides structured feedback using HCD and design principles.

For full workflow details, see the [Multi-Agent Workflow Spec](design_assistant/specs/multi_agent_workflow_spec.md).

---

## Directory Structure

```
design_assistant/
├── design_assistant.py           # Main application entrypoint
├── design_database.py            # Supabase integration and data handling
├── design_utils.py               # Utility functions (e.g., prompt loading)
├── test_design_supabase.py       # Supabase integration tests
├── prompts/
│   ├── design_coach.yaml         # Design Coach agent persona
│   ├── design_strategist.yaml    # Design Strategist agent persona
│   └── design_evaluator.yaml     # Design Evaluator agent persona
├── specs/
│   └── multi_agent_workflow_spec.md # Workflow specification
└── requirements.txt
```

---

## Getting Started

Follow these instructions to get the project up and running on your local machine.

### 1. Prerequisites

*   **Node.js and npm:** Required for the frontend. `pnpm` is used for package management; if you don't have it, install it globally: `npm install -g pnpm`
*   **Python 3.10+:** Required for the backend.
*   **Git:** For cloning the repository.
*   **API Keys:** You will need accounts and API keys for the following services:
    *   OpenAI
    *   LiveKit (Cloud project)
    *   Supabase (Database project)
    *   Deepgram (for Speech-to-Text)
    *   Cartesia (for Text-to-Speech)

### 2. Clone the Repository

```bash
git clone https://github.com/Starinzk/voiceagent.git
cd voiceagent
```

### 3. Backend Setup (`design_assistant/`)

1.  **Navigate to the backend directory:**
    ```bash
    cd design_assistant
    ```

2.  **Create and activate a Python virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On macOS/Linux
    # venv\\Scripts\\activate    # On Windows
    ```
    
    To deactivate the virtual environment when you're done:
    ```bash
    deactivate
    ```

3.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Create and populate the backend environment file:**
    Create a file named `.env` in the `design_assistant/` directory and add the following, replacing `<YOUR_..._KEY>` placeholders with your actual credentials:

    ```env
    # OpenAI
    OPENAI_API_KEY=<YOUR_OPENAI_API_KEY>

    # LiveKit (ensure these match your LiveKit project)
    LIVEKIT_URL=wss://<YOUR_LIVEKIT_PROJECT_SUBDOMAIN>.livekit.cloud
    LIVEKIT_API_KEY=<YOUR_LIVEKIT_API_KEY>
    LIVEKIT_API_SECRET=<YOUR_LIVEKIT_API_SECRET>

    # Supabase
    SUPABASE_URL=https://<YOUR_SUPABASE_PROJECT_ID>.supabase.co
    SUPABASE_KEY=<YOUR_SUPABASE_SERVICE_ROLE_KEY> # Important: Use the SERVICE ROLE key

    # Deepgram (for Speech-to-Text)
    DEEPGRAM_API_KEY=<YOUR_DEEPGRAM_API_KEY>

    # Cartesia (for Text-to-Speech)
    CARTESIA_API_KEY=<YOUR_CARTESIA_API_KEY>

    # API for LiveKit connection details (usually can be left as is)
    NEXT_PUBLIC_CONN_DETAILS_ENDPOINT=/api/connection-details
    ```

### 4. Frontend Setup (`voice-assistant-frontend/`)

1.  **Navigate to the frontend directory:**
    From the project root:
    ```bash
    cd voice-assistant-frontend
    ```
    Or from `design_assistant/`:
    ```bash
    cd ../voice-assistant-frontend
    ```

2.  **Install frontend dependencies:**
    (Ensure `pnpm` is installed: `npm install -g pnpm`)
    ```bash
    pnpm install
    ```

3.  **Create and populate the frontend environment file:**
    Create a file named `.env.local` in the `voice-assistant-frontend/` directory and add the following, replacing placeholders:

    ```env
    # LiveKit (ensure these match your LiveKit project and backend .env)
    LIVEKIT_URL=wss://<YOUR_LIVEKIT_PROJECT_SUBDOMAIN>.livekit.cloud
    LIVEKIT_API_KEY=<YOUR_LIVEKIT_API_KEY>
    LIVEKIT_API_SECRET=<YOUR_LIVEKIT_API_SECRET>

    # Supabase (use the public anonymous key for the frontend)
    NEXT_PUBLIC_SUPABASE_URL=https://<YOUR_SUPABASE_PROJECT_ID>.supabase.co
    NEXT_PUBLIC_SUPABASE_ANON_KEY=<YOUR_SUPABASE_ANON_KEY>

    # API for LiveKit connection details (usually can be left as is)
    NEXT_PUBLIC_CONN_DETAILS_ENDPOINT=/api/connection-details

    # OpenAI (only needed if your frontend makes OpenAI API calls directly)
    OPENAI_API_KEY=<YOUR_OPENAI_API_KEY>
    ```
    *Note the `NEXT_PUBLIC_` prefix for variables exposed to the browser.*

### 5. Running the Application

You need to run both the backend and frontend servers simultaneously in separate terminal windows.

1.  **Run the Backend Server:**
    *   Open a terminal.
    *   Navigate to `design_assistant/`.
    *   Ensure your virtual environment is activated (`source venv/bin/activate`).
    *   Run:
        ```bash
        python3 design_assistant.py dev
        ```
    *   Keep this terminal window running.

2.  **Run the Frontend Server:**
    *   Open a *new* terminal window.
    *   Navigate to `voice-assistant-frontend/`.
    *   Run:
        ```bash
        pnpm dev
        ```
    *   Keep this terminal window running.

3.  **Access the Application:**
    Open your web browser and go to:
    [http://localhost:3000](http://localhost:3000)

---

## Migration Note

This project was refactored from the original "Personal Shopper" codebase.  
All agent logic, prompts, and data handling have been updated for the design-focused workflow.

---

## Contributing

- Please reference the [multi-agent workflow spec](design_assistant/specs/multi_agent_workflow_spec.md) before making changes to agent logic or workflow.
- Open issues or pull requests for discussion and review.
