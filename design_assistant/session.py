"""
Design Session Module

This module contains the DesignSession class that manages the agent workflow, 
transitions, and loop logic. It wraps the LiveKit AgentSession and adds 
design-specific orchestration.

Extracted from design_assistant.py as part of the backend refactoring.
"""

import asyncio
from typing import Optional

from livekit.agents.voice import AgentSession, Agent, RunContext
from livekit.agents.llm import ChatMessage
from livekit.plugins import deepgram, openai, silero

from user_data import UserData
from agents import (
    DesignCoachAgent,
    DesignStrategistAgent, 
    DesignEvaluatorAgent
)

class DesignSession:
    """
    Manages the design workflow session, including agent transitions and loop logic.
    
    This class wraps LiveKit's AgentSession and adds design-specific orchestration:
    - Agent creation and management
    - Workflow transitions between Coach → Strategist → Evaluator
    - Loop detection and management
    - Context passing between agents
    
    The session manages the high-level flow while individual agents focus on 
    their specific domain expertise.
    """
    
    def __init__(self, user_data: UserData):
        self.user_data = user_data
        self.livekit_session: Optional[AgentSession] = None
        self._agents: dict[str, Agent] = {}
        self._current_agent: Optional[Agent] = None
        
    async def initialize(self):
        """
        Initialize the session with all required components.
        This creates the LiveKit session and instantiates all agents.
        """
        # Asynchronously initialize all plugins to avoid blocking the event loop
        stt, llm, tts, vad = await asyncio.gather(
            asyncio.to_thread(deepgram.STT),
            asyncio.to_thread(openai.LLM),
            asyncio.to_thread(lambda: openai.TTS(voice="alloy")),
            asyncio.to_thread(silero.VAD.load, min_silence_duration=1.2),
        )

        # Create the LiveKit AgentSession
        self.livekit_session = AgentSession(
            userdata=self.user_data,
            stt=stt,
            llm=llm,
            tts=tts,
            vad=vad,
        )
        
        # Set the session reference in user_data
        self.user_data.agent_session = self.livekit_session
        
        # Store reference to this DesignSession in user_data for agent access
        self.user_data.design_session = self
        
        # Initialize all agents
        self._agents = {
            "DesignCoachAgent": DesignCoachAgent(),
            "DesignStrategistAgent": DesignStrategistAgent(),
            "DesignEvaluatorAgent": DesignEvaluatorAgent()
        }
        
        # Store agents in user_data for backward compatibility
        self.user_data.personas = self._agents
        
        # Set initial agent
        self._current_agent = self._agents["DesignCoachAgent"]
        
    async def start(self, room):
        """Start the session with the initial agent."""
        if not self.livekit_session:
            raise RuntimeError("Session not initialized. Call initialize() first.")
            
        await self.livekit_session.start(agent=self._current_agent, room=room)
        
    def determine_next_agent(self, current_agent_name: str, context: Optional[str] = None) -> tuple[str, Optional[str]]:
        """
        Determines the next agent based on the current workflow state.
        
        Returns:
            tuple: (next_agent_name, context_message)
        """
        context_message = None
        
        # Linear workflow logic
        if current_agent_name == "DesignCoachAgent":
            next_agent_name = "DesignStrategistAgent"
            challenge = self.user_data.design_challenge
            if challenge:
                context_message = f"The user has defined their design challenge as: '{challenge}'. Your task is to help them refine this into a 'How might we...' statement and then propose a solution."
                
        elif current_agent_name == "DesignStrategistAgent":
            next_agent_name = "DesignEvaluatorAgent"
            solution = self.user_data.proposed_solution
            if solution:
                context_message = f"The user has proposed the following solution: {solution}. Your task is to evaluate it."
                
        else:
            # End of flow case - stay on current agent
            return current_agent_name, "There are no further steps in this design flow."
            
        return next_agent_name, context_message
        
    async def transition_to_agent(self, agent_name: str, context_message: Optional[str] = None) -> Agent:
        """
        Transition to a specific agent with optional context.
        
        This method handles:
        - Agent lookup and validation
        - Context message injection
        - Orchestration state updates
        - Frontend state notifications
        """
        # Get the target agent
        next_agent = self._agents.get(agent_name)
        if not next_agent:
            # Fallback - return current agent
            if self._current_agent:
                await self._current_agent.speak(f"Sorry, I could not find the {agent_name} agent.")
            return self._current_agent or self._agents["DesignCoachAgent"]
        
        # Store previous agent for context
        self.user_data.prev_agent = self._current_agent
        
        # Inject context message if provided
        if context_message and self.livekit_session:
            sys_msg = ChatMessage(
                role="system",
                content=[context_message],
            )
            if hasattr(self.livekit_session.llm, 'chat_history'):
                self.livekit_session.llm.chat_history.messages.append(sys_msg)
        
        # Update orchestration state
        self.user_data.current_agent_name = agent_name
        self.user_data.agent_sequence.append(agent_name)
        
        # Update current agent
        self._current_agent = next_agent
        
        # Send updated state to frontend
        await self._send_agent_state()
        
        return next_agent
        
    async def handle_agent_transition(self, context: RunContext) -> Agent:
        """
        Handle a request for agent transition using workflow logic.
        
        This replaces the old request_next_step function that was embedded in agents.
        """
        current_agent_name = self.user_data.current_agent_name
        next_agent_name, context_message = self.determine_next_agent(current_agent_name)
        
        if next_agent_name == current_agent_name:
            # End of flow - stay on current agent
            if self._current_agent:
                await self._current_agent.speak(context_message or "There are no further steps in this design flow.")
            return self._current_agent or self._agents["DesignCoachAgent"]
            
        return await self.transition_to_agent(next_agent_name, context_message)
        
    async def handle_loop_back(self, target_agent_name: str, reason: str) -> Agent:
        """
        Handle looping back to a previous agent with tracking.
        
        This manages the loop detection and counting that was previously 
        scattered throughout the agent code.
        """
        self.user_data.loop_reason = reason
        loop_counts = self.user_data.loop_counts
        loop_counts[target_agent_name] = loop_counts.get(target_agent_name, 0) + 1
        
        context_message = f"The user wants to revise the design. Here is their feedback: {reason}"
        return await self.transition_to_agent(target_agent_name, context_message)
        
    async def _send_agent_state(self):
        """Send the current agent orchestration state to the frontend."""
        if not self.user_data.ctx or not self.user_data.ctx.room:
            return
            
        import json
        state_payload = {
            "type": "agent_state",
            "current_agent_name": self.user_data.current_agent_name,
            "agent_sequence": self.user_data.agent_sequence,
            "loop_reason": self.user_data.loop_reason,
            "loop_counts": self.user_data.loop_counts,
        }
        await self.user_data.ctx.room.local_participant.publish_data(
            json.dumps(state_payload), topic="lk-chat-topic"
        )
        
    @property
    def current_agent(self) -> Optional[Agent]:
        """Get the currently active agent."""
        return self._current_agent
        
    @property
    def agents(self) -> dict[str, Agent]:
        """Get all available agents."""
        return self._agents.copy() 