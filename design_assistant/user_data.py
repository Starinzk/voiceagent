"""
User Data Module

This module contains the UserData and ClarityCapsule classes that manage 
the state of a user's design session and store the final structured output.

Extracted from design_assistant.py as part of the backend refactoring.
"""

from dataclasses import dataclass, field
from typing import Optional

from livekit.agents import JobContext
from livekit.agents.voice import Agent, AgentSession

# Forward declaration for type hints - will need to import DesignDatabase
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from design_assistant.design_database import DesignDatabase

@dataclass
class ClarityCapsule:
    '''A structured summary of the design session's outcome.'''
    problem_statement: str
    solution_concept: str
    strengths: list[str]
    blind_spots: list[str]
    next_steps: list[str]

@dataclass
class UserData:
    '''
    Manages the state for a user's design session, including all data,
    history, and agent interactions. This class is central to the application's
    state management and orchestrates database persistence.

    Attributes:
        personas (dict[str, Agent]): Holds all agent instances for the session.
        prev_agent (Optional[Agent]): The previously active agent, used for context transfer.
        ctx (Optional[JobContext]): The LiveKit job context.
        agent_session (Optional[AgentSession]): The active agent session.

        first_name (Optional[str]): The user's first name.
        last_name (Optional[str]): The user's last name.
        user_id (Optional[str]): The user's unique ID from the database.

        design_challenge (Optional[str]): The initial design challenge.
        target_users (Optional[list[str]]): The target audience for the design.
        emotional_goals (Optional[list[str]]): The desired emotional outcomes.
        problem_statement (Optional[str]): The refined "How might we..." statement.
        proposed_solution (Optional[str]): The description of the proposed solution.

        status (str): The current state of the design workflow.
        design_iterations (list[dict]): A history of design iterations.
        feedback_history (list[dict]): A history of feedback received.
        pending_session_id (Optional[str]): The ID of the pending session.
        clarity_capsule (Optional[ClarityCapsule]): A structured summary of the design session's outcome.

        db (Optional[DesignDatabase]): The database client instance, used for all
                                      persistence operations.
    '''
    # Agent Management
    personas: dict[str, Agent] = field(default_factory=dict)
    prev_agent: Optional[Agent] = None
    ctx: Optional[JobContext] = None

    # User Identification
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    user_id: Optional[str] = None

    # Design Session Data
    design_challenge: Optional[str] = None
    target_users: Optional[list[str]] = None
    emotional_goals: Optional[list[str]] = None
    problem_statement: Optional[str] = None
    proposed_solution: Optional[str] = None

    # Session State
    status: str = "awaiting_problem_definition"  # Flow: awaiting_problem_definition -> ready_for_evaluation -> evaluation_complete
    pending_session_id: Optional[str] = None
    clarity_capsule: Optional[ClarityCapsule] = None

    # --- Orchestration State ---
    # These fields manage the agent flow, including loops and history for the UI.
    current_agent_name: str = "DesignCoachAgent"
    agent_sequence: list[str] = field(default_factory=list)
    loop_reason: Optional[str] = None
    loop_counts: dict[str, int] = field(default_factory=dict)

    # Design History
    design_iterations: list[dict] = field(default_factory=list)
    feedback_history: list[dict] = field(default_factory=list)

    # Database Integration
    db: Optional["DesignDatabase"] = field(default=None, repr=False, metadata={
        'doc': 'Database connection for state persistence. Set during initialization.'
    })
    agent_session: Optional[AgentSession] = None

    def is_identified(self) -> bool:
        '''
        Check if the user has been identified, either in memory or in the database.
        
        This method first checks for a first and last name in the current session's
        memory. If not found, it will check if a user_id exists and is valid in the
        database. This allows for identifying returning users who have persisted sessions.
        
        Returns:
            bool: True if the user is identified, False otherwise.
        '''
        if self.first_name and self.last_name:
            return True
        if self.user_id and self.db:
            try:
                self.db.get_session_details(self.user_id)
                return True
            except ValueError:
                return False
        return False

    def reset(self) -> None:
        '''
        Reset all user information.
        
        Design Decisions:
        - Simple in-memory reset
        - No persistence
        - Preserves database connection
        
        Limitations:
        - No data backup
        - No history preservation
        
        Future Improvements:
        - Database persistence
        - History preservation
        
        Note:
            This will only reset in-memory state.
            To delete database state, use the database directly.
        '''
        self.first_name = None
        self.last_name = None
        self.user_id = None
        self.design_challenge = None
        self.target_users = None
        self.emotional_goals = None
        self.problem_statement = None
        self.proposed_solution = None
        self.status = "awaiting_problem_definition"
        self.design_iterations = []
        self.feedback_history = []
        self.clarity_capsule = None

        # Reset orchestration state
        self.current_agent_name = "DesignCoachAgent"
        self.agent_sequence = []
        self.loop_reason = None
        self.loop_counts = {}

    def summarize(self) -> str:
        '''
        Return a summary of the user data.
        
        Design Decisions:
        - Simple text-based summary
        - In-memory data only
        
        Limitations:
        - No rich formatting
        - No customization options
        
        Future Improvements:
        - Rich formatting
        - Customization options
        '''
        summary_parts = []
        if self.is_identified():
            summary_parts.append(f"User: {self.first_name} {self.last_name} (ID: {self.user_id})")
        else:
            summary_parts.append("User not yet identified.")

        if self.design_challenge:
            summary_parts.append(f"Design Challenge: {self.design_challenge}")
        if self.target_users:
            summary_parts.append(f"Target Users: {', '.join(self.target_users)}")
        if self.emotional_goals:
            summary_parts.append(f"Emotional Goals: {', '.join(self.emotional_goals)}")
        if self.problem_statement:
            summary_parts.append(f"Problem Statement: {self.problem_statement}")
        if self.proposed_solution:
            summary_parts.append(f"Proposed Solution: {self.proposed_solution}")
        
        return "\n".join(summary_parts)

    def save_state(self) -> str:
        '''
        Save the current state to the database.
        
        Design Decisions:
        - Uses DesignDatabase for persistence
        - Preserves all user data and session state
        - Maintains design history and feedback
        
        Returns:
            str: The session ID that can be used to load this state later
            
        Raises:
            ValueError: If no database is configured
            
        Example:
            ```python
            session_id = user_data.save_state()
            # Later...
            user_data.load_state(session_id)
            ```
            
        Note:
            This method will:
            1. Save user information
            2. Save current session state
            3. Save all design iterations
            4. Save all feedback history
        '''
        if not self.db:
            raise ValueError("No database configured. Set UserData.db before saving.")
        return self.db.save_user_data(self)

    def load_state(self, session_id: str) -> None:
        '''
        Load state from the database.
        
        Design Decisions:
        - Uses DesignDatabase for state recovery
        - Preserves agent-related fields
        - Maintains database connection
        
        Args:
            session_id (str): The ID of the session to load
            
        Raises:
            ValueError: If no database is configured or session not found
            
        Example:
            ```python
            user_data.load_state("123")
            # All fields are now populated from the database
            ```
            
        Note:
            This method will:
            1. Load user information
            2. Load session state
            3. Load all design iterations
            4. Load all feedback history
            5. Preserve agent-related fields (personas, prev_agent, ctx)
        '''
        if not self.db:
            raise ValueError("No database configured. Set UserData.db before loading.")
        
        # Load state from database
        loaded_data = self.db.load_user_data(session_id)
        
        # Update all fields except db and agent-related fields
        for field_info in self.__dataclass_fields__:
            field_name = field_info.name
            if field_name not in ['db', 'personas', 'prev_agent', 'ctx', 'agent_session']:
                setattr(self, field_name, getattr(loaded_data, field_name)) 