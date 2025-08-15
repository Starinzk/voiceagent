"""
Design Coach Agent Module

This module contains the DesignCoachAgent class that helps users articulate 
their design challenge and captures initial requirements.

Extracted from design_assistant.py as part of the backend refactoring.
"""

import logging
from typing import Optional

from livekit.agents.llm import function_tool
from livekit.agents.voice import RunContext
from .base_agent import BaseAgent
from design_assistant.design_utils import load_prompt

# Define a generic type for the RunContext for cleaner type hinting
from livekit.agents.voice import RunContext as RunContext_T

logger = logging.getLogger(__name__)

class DesignCoachAgent(BaseAgent):
    '''An agent that helps users articulate their design challenge.'''
    def __init__(self) -> None:
        super().__init__(
            instructions=load_prompt('design_coach.yaml'),
        )
        self._set_agent_name("design_coach")

    async def on_enter(self) -> None:
        self.user_data.status = "awaiting_problem_definition"
        await super().on_enter()

    @function_tool
    async def identify_user(self, first_name: str, last_name: str) -> str:
        '''
        Identifies the user by their first and last name.
        This is the first step in the design process.
        '''
        userdata = self.user_data
        userdata.first_name = first_name
        userdata.last_name = last_name
        
        try:
            user_id, is_new = userdata.db.get_or_create_user(first_name, last_name)
            userdata.user_id = user_id
            
            # Now, check for past sessions
            past_sessions = userdata.db.get_user_sessions(user_id)
            
            if not is_new and past_sessions:
                # Returning user with past sessions
                session_list = "\n".join(
                    [
                        f"- Session ID: {s['id']}, Created: {s['created_at']}"
                        for s in past_sessions
                    ]
                )
                response = f"Welcome back, {first_name}. I found these past sessions:\n{session_list}\nWould you like to load one of these sessions, or start a new one?"
            else:
                # New user, or returning user with no past sessions
                response = f"Thank you, {first_name}. I've created a new profile for you. To get started, please describe your design challenge."

            await self.speak(response)
            return "User identified and greeted."

        except Exception as e:
            print(f"Database error in identify_user: {e}")
            response = f"I'm sorry, {first_name}. I encountered an error accessing my database. Let's proceed for now. Please describe your design challenge."
            await self.speak(response)
            return "Error identifying user, but proceeded with session."

    @function_tool
    async def select_session_to_load(self, session_id: str) -> str:
        """
        Informs the user that the selected session will be loaded. This function 
        confirms the user's choice before the actual loading process begins.
        The subsequent call to `load_selected_session` will perform the state change.
        """
        self.user_data.pending_session_id = session_id
        response = f"Great. I will load session {session_id} for you now. One moment."
        await self.speak(response)
        return "Informing user that session will be loaded."

    @function_tool
    async def load_selected_session(self, context: RunContext_T):
        """
        Loads a session that the user has previously selected with `select_session_to_load`.
        This function retrieves the session data from the database and transitions
        the user's state into that session. It will then transfer control to the
        next appropriate agent based on the loaded session's status.
        """
        userdata = self.user_data
        session_id = userdata.pending_session_id
        if not session_id:
            await self.speak("I'm sorry, I don't have a session ID to load. Please select one first.")
            return self

        await self.speak(f"Great. I will load session {session_id} for you now. One moment.")

        try:
            logger.info(f"Attempting to load state for session_id: {session_id}")
            userdata.load_state(session_id)
            logger.info(f"Successfully loaded state for session_id: {session_id}. User is now: {userdata.first_name}")

            # Greet the user by name and provide a summary
            await self.speak(f"Welcome back, {userdata.first_name}. I've loaded your session. Here's a quick summary:")
            await self.speak(userdata.summarize())

            # Handoff to the correct agent based on loaded state
            if userdata.status == "ready_for_evaluation":
                await self.speak("It looks like we were ready for feedback. I'll transfer you to the Design Evaluator.")
                return await self.request_next_step(context)
            else: # Default to strategist
                await self.speak("Let's continue refining your solution. I'll transfer you to the Design Strategist.")
                return await self.request_next_step(context)

        except ValueError as e:
            logger.error(f"ValueError loading session {session_id}: {e}", exc_info=True)
            await self.speak(f"I'm sorry, I couldn't load that session. Error: {e}")
            return self
        except Exception as e:
            logger.error(f"Unexpected error loading session {session_id}: {e}", exc_info=True)
            await self.speak("I encountered an unexpected error while loading your session. Let's start a new one.")
            userdata.reset() # Reset to a clean state
            return self

    @function_tool
    async def capture_design_challenge(
        self,
        design_challenge: str,
        target_users: Optional[list[str]] = None,
        emotional_goals: Optional[list[str]] = None,
    ) -> str:
        """Captures the user's design challenge details."""
        self.user_data.design_challenge = design_challenge
        self.user_data.target_users = target_users
        self.user_data.emotional_goals = emotional_goals
        self.user_data.save_state()
        
        response = "I've captured the details of your design challenge. To move forward, we can proceed to the next step in the design process. Please let me know when you're ready or if there's anything else you'd like to add or modify."
        await self.speak(response)
        
        return "The design challenge has been captured and the user has been prompted for the next step." 