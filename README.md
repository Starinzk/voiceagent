# LiveKit Personal Shopper Voice Agent

This project is a voice-enabled personal shopping assistant powered by LiveKit, with a Python backend for agent logic and a Next.js frontend for the user interface.

## Getting Started

Follow these instructions to get the project up and running on your local machine.

### 1. Prerequisites

*   **Node.js and npm:** Required for the frontend. `pnpm` is used for package management; if you don\'t have it, install it globally: `npm install -g pnpm`
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

### 3. Backend Setup (`personal_shopper/`)

1.  **Navigate to the backend directory:**
    ```bash
    cd personal_shopper
    ```

2.  **Create and activate a Python virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On macOS/Linux
    # venv\\Scripts\\activate    # On Windows
    ```

3.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Create and populate the backend environment file:**
    Create a file named `.env` in the `personal_shopper/` directory and add the following, replacing `<YOUR_..._KEY>` placeholders with your actual credentials:

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
    Or from `personal_shopper/`:
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
    *   Navigate to `personal_shopper/`.
    *   Ensure your virtual environment is activated (`source venv/bin/activate`).
    *   Run:
        ```bash
        python personal_shopper.py dev
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

## Project Structure

*   `personal_shopper/`: Python backend with LiveKit agents, business logic, and database interactions.
*   `voice-assistant-frontend/`: Next.js frontend for user interaction and voice input/output.

## Development Branches

*   `main`: The primary stable branch.
*   `dev`: Development branch for new features and fixes.
