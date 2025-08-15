"""
Agents Module

This module contains all the design workflow agents extracted from the monolithic
design_assistant.py file as part of the backend refactoring.

The agents are:
- BaseAgent: Foundation class with common functionality
- DesignCoachAgent: Helps users articulate their design challenge
- DesignStrategistAgent: Refines problem statements and proposes solutions  
- DesignEvaluatorAgent: Evaluates solutions and provides structured feedback
"""

from .base_agent import BaseAgent
from .coach_agent import DesignCoachAgent
from .strategist_agent import DesignStrategistAgent
from .evaluator_agent import DesignEvaluatorAgent

__all__ = [
    "BaseAgent",
    "DesignCoachAgent", 
    "DesignStrategistAgent",
    "DesignEvaluatorAgent"
] 