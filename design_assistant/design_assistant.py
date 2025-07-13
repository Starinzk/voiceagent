"""
Design Assistant Application (Legacy)

This module provides backwards compatibility for imports from the old monolithic structure.
All functionality has been moved to the new modular architecture:

- User state management: user_data.py
- Workflow orchestration: session.py  
- Individual agents: agents/
- Main entrypoint: main.py

For new code, please import directly from the specific modules.
"""

# Re-export all components for backwards compatibility
from design_assistant.user_data import UserData, ClarityCapsule
from design_assistant.session import DesignSession
from design_assistant.design_database import DesignDatabase
from design_assistant.agents import (
    BaseAgent,
    DesignCoachAgent,
    DesignStrategistAgent, 
    DesignEvaluatorAgent
)
from design_assistant.main import main, entrypoint, request_fnc

# Legacy compatibility - maintain old import patterns
__all__ = [
    # Core data structures
    'UserData',
    'ClarityCapsule',
    
    # Session management
    'DesignSession',
    'DesignDatabase',
    
    # Agents
    'BaseAgent',
    'DesignCoachAgent',
    'DesignStrategistAgent',
    'DesignEvaluatorAgent',
    
    # Main functions
    'main',
    'entrypoint', 
    'request_fnc',
]

# Note: This file can be deprecated once all imports are updated to use the new modular structure
