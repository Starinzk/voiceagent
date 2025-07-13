"""
Design Assistant Package

This package implements a multi-agent design workflow system with voice interaction capabilities.
"""

# Core components
from .user_data import UserData, ClarityCapsule
from .session import DesignSession  
from .design_database import DesignDatabase

# Agents
from .agents import (
    BaseAgent,
    DesignCoachAgent, 
    DesignStrategistAgent,
    DesignEvaluatorAgent
)

# Main entrypoint
from .main import main, entrypoint

__all__ = [
    # Core components
    'UserData',
    'ClarityCapsule', 
    'DesignSession',
    'DesignDatabase',
    
    # Agents  
    'BaseAgent',
    'DesignCoachAgent',
    'DesignStrategistAgent', 
    'DesignEvaluatorAgent',
    
    # Main entrypoint
    'main',
    'entrypoint',
] 