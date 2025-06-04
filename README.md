# Design Assistant

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

## Usage

1. **Install dependencies:**
   ```sh
   pip install -r design_assistant/requirements.txt
   ```

2. **Set up your environment variables:**
   - Copy `.env.example` to `.env` and fill in your Supabase credentials and other settings.

3. **Run the main application:**
   ```sh
   python3 design_assistant/design_assistant.py
   ```

4. **Run tests:**
   ```sh
   python3 design_assistant/test_design_supabase.py
   ```

---

## Migration Note

This project was refactored from the original "Personal Shopper" codebase.  
All agent logic, prompts, and data handling have been updated for the design-focused workflow.

---

## Contributing

- Please reference the [multi-agent workflow spec](design_assistant/specs/multi_agent_workflow_spec.md) before making changes to agent logic or workflow.
- Open issues or pull requests for discussion and review.
