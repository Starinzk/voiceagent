## Getting Started

1. Clone this repository
2. Create `.env` file:
   - Place one copy in the `personal_shopper/` directory
   - Place another copy in the `voice-assistant-frontend/` directory
3. Install dependencies:

```bash
# Backend
cd travel_agent_backend
python3 -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
pip install -r requirements.txt
```

4. Install frontend dependencies:

```bash
# Frontend
cd ../voice-assistant-frontend # If you are in travel_agent_backend, otherwise navigate to voice-assistant-frontend
pnpm install
```

5. Run the backend (ensure your virtual environment is activated):
```bash
cd travel_agent_backend
python personal_travel_agent.py dev
```

6. Run the frontend:
```bash
cd voice-assistant-frontend
pnpm dev
```
