# Livekit Design Agent

## 🎯 Application Overview

**Livekit Design Agent** is a sophisticated real-time voice-powered AI assistant that guides users through comprehensive design workflows using a multi-agent orchestration system. The application combines cutting-edge voice AI technology with human-centered design principles to provide an interactive, conversational design coaching experience.

### Key Features
- **Real-time Voice Interaction**: Seamless voice-to-voice conversations with low-latency audio processing
- **Multi-Agent Architecture**: Three specialized AI agents working in coordination
- **Session Persistence**: Maintains conversation context and design progress across sessions
- **Visual Feedback**: Real-time transcription, agent status, and workflow breadcrumbs
- **Loop Detection**: Intelligent workflow management with loop notifications
- **Responsive UI**: Modern, elegant interface optimized for voice interaction

### Architecture Philosophy
The system implements a **multi-agent orchestration pattern** where specialized AI agents hand off control based on workflow requirements, creating a natural conversational flow that mirrors human design consultation processes.

---

## 🛠️ Technology Stack

### Backend
- **Runtime**: Python 3.10+
- **AI Framework**: LiveKit Agents SDK
- **LLM Provider**: OpenAI GPT-4
- **Voice Processing**: 
  - Deepgram (Speech-to-Text)
  - Cartesia (Text-to-Speech)
  - Silero VAD (Voice Activity Detection)
- **Database**: Supabase (PostgreSQL)
- **Session Management**: Custom session handling with user data persistence

### Frontend
- **Framework**: Next.js 14 (React 18)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Real-time Communication**: LiveKit Client SDK
- **State Management**: React Hooks + Custom hooks
- **Package Manager**: pnpm

### Infrastructure & Integrations
- **Real-time Communication**: LiveKit Cloud
- **Database**: Supabase (PostgreSQL with real-time subscriptions)
- **AI Services**: OpenAI API
- **Voice Services**: Deepgram + Cartesia
- **Deployment**: Local development with cloud service integrations

---

## 🤖 Multi-Agent System

The application features three specialized AI agents that work together to provide comprehensive design guidance:

### 1. **Design Coach Agent** (`DesignCoachAgent`)
- **Role**: Initial user engagement and workflow orchestration
- **Responsibilities**: 
  - Welcomes users and establishes rapport
  - Clarifies emotional and strategic intent
  - Manages transitions between agents
  - Provides encouragement and motivation
- **Handoff Triggers**: User readiness for strategic planning

### 2. **Design Strategist Agent** (`DesignStrategistAgent`)
- **Role**: Strategic design planning and problem definition
- **Responsibilities**:
  - Conducts structured problem discovery
  - Guides users through solution ideation
  - Develops comprehensive problem statements
  - Creates actionable design proposals
- **Handoff Triggers**: Complete problem statement and proposed solution

### 3. **Design Evaluator Agent** (`DesignEvaluatorAgent`)
- **Role**: Critical analysis and design critique
- **Responsibilities**:
  - Evaluates problem statements and solutions
  - Provides structured feedback using HCD principles
  - Scores design proposals on multiple criteria
  - Suggests improvements and iterations
- **Handoff Triggers**: Evaluation complete or iteration needed

### Agent Coordination
- **Session Management**: Persistent user data across agent transitions
- **Context Preservation**: Full conversation history maintained
- **Workflow Intelligence**: Automatic loop detection and management
- **Seamless Handoffs**: Natural transitions between agents

---

## 📊 Data Flow & Session Management

### User Data Structure
```python
UserData:
  - user_id: str
  - current_agent: str
  - agent_history: List[str]
  - conversation_context: Dict
  - problem_statement: Optional[str]
  - proposed_solution: Optional[str]
  - evaluation_results: Optional[Dict]
  - session_metadata: Dict
```

### Session Persistence
- **Database Integration**: Supabase for persistent storage
- **Real-time Updates**: Live session state synchronization
- **Context Preservation**: Full conversation history and agent state
- **Cross-session Continuity**: Resume conversations from any point

---

## 🎨 User Interface Features

### Core Components
- **AgentOrb**: Visual representation of current active agent
- **AgentBreadcrumbs**: Shows agent transition history and workflow progress
- **TranscriptionView**: Real-time speech-to-text display
- **LoopNotice**: Intelligent workflow loop detection and notifications
- **ClarityCapsuleView**: Enhanced feedback display system
- **Waveform**: Audio visualization and voice activity indication

### Enhanced UX
- **Elegant Design**: Light, modern Enso-inspired theme
- **Responsive Layout**: Optimized for various screen sizes
- **Real-time Feedback**: Immediate visual responses to voice input
- **Accessibility**: Voice-first design with visual accessibility features

---

## 🔧 Development Architecture

### Backend Structure
```
design_assistant/
├── agents/                    # Multi-agent system
│   ├── base_agent.py         # Shared agent functionality
│   ├── coach_agent.py        # Design coaching agent
│   ├── strategist_agent.py   # Strategic planning agent
│   └── evaluator_agent.py    # Design evaluation agent
├── main.py                   # Application entry point
├── session.py                # Session management
├── user_data.py              # User data models
├── design_database.py        # Database integration
└── prompts/                  # Agent-specific prompts
```

### Frontend Structure
```
voice-assistant-frontend/
├── components/               # React components
│   ├── AgentOrb.tsx         # Agent visualization
│   ├── AgentBreadcrumbs.tsx # Workflow navigation
│   ├── Dashboard.tsx        # Main interface
│   ├── LiveSession.tsx      # Session management
│   └── LoopNotice.tsx       # Loop detection UI
├── hooks/                   # Custom React hooks
│   ├── useAgentState.ts     # Agent state management
│   ├── useDataChannel.ts    # Real-time communication
│   └── useCombinedTranscriptions.ts # Transcription handling
└── app/                     # Next.js app structure
```

---

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

1.  **Run the Backend Worker (from repo root):**
    *   Open a terminal at the repository root and run:
        ```bash
        design_assistant/venv/bin/python -m design_assistant.main
        ```
    *   This avoids Python package import issues.

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
