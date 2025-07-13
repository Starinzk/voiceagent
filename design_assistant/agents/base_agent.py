"""
Base Agent Module

This module contains the BaseAgent class that serves as the foundation for all 
design workflow agents. It provides common functionality like speaking, transcript
handling, and context management.

Extracted from design_assistant.py as part of the backend refactoring.
"""

import json
import asyncio
from datetime import datetime
from typing import Optional, AsyncIterable

from livekit.agents.llm import ChatContext, function_tool, ChatMessage
from livekit.agents.voice import Agent, RunContext
from design_assistant.design_utils import load_prompt

# Define a generic type for the RunContext for cleaner type hinting
from livekit.agents.voice import RunContext as RunContext_T

class BaseAgent(Agent):
    '''Base class for all agents in the design workflow.'''
    def __init__(
        self,
        *,
        instructions: str,
    ):
        super().__init__(instructions=instructions)
        self._agent_name: str = self.__class__.__name__

    def _set_agent_name(self, name: str):
        self._agent_name = name

    async def _llm_stream_to_str_stream(self, stream: AsyncIterable) -> AsyncIterable[str]:
        """Converts a stream of LLM ChatChunk objects to a stream of strings."""
        async for chunk in stream:
            if hasattr(chunk, 'delta') and hasattr(chunk.delta, 'content') and chunk.delta.content:
                yield chunk.delta.content

    async def on_enter(self) -> None:
        """Generic entry logic for agents."""
        if self.user_data.is_identified():
            return
        
        # This is the introductory message for new, unidentified users
        await self.speak("Welcome to the Design Assistant. I am your Design Coach. To begin, please tell me your first and last name.")

    async def on_user_turn_completed(self, turn_ctx, new_message: ChatMessage) -> None:
        """
        This hook is called whenever the user finishes speaking.
        We use it to capture the user's transcript and send it over the data
        channel with the correct identity. This is the single source of truth
        for the user's side of the conversation.
        """
        if new_message.content:
            # The content can be a list of parts, we want to join them into a single string
            transcript = "".join(str(part) for part in new_message.content)
            await self.send_user_transcript(transcript, is_final=True)

    async def speak(self, text_or_stream: str | AsyncIterable[str]):
        """
        Speak the provided text via TTS and send the transcript over the data channel.
        This function handles both simple strings and asynchronous streams of text.
        """
        if isinstance(text_or_stream, str):
            # Simple case: just a string
            await self._send_agent_transcript(text_or_stream, is_final=True)
            await self.user_data.agent_session.say(text_or_stream)
        else:
            # Complex case: a stream of text chunks
            async def transcript_stream_iterator():
                async for chunk in self._llm_stream_to_str_stream(text_or_stream):
                    await self._send_agent_transcript(chunk, is_final=False)
                    yield chunk
                # Send a final empty message to signal the end of the transcript
                await self._send_agent_transcript("", is_final=True)

            await self.user_data.agent_session.say(transcript_stream_iterator())

    async def _send_agent_transcript(self, text: str, is_final: bool):
        """Sends the agent's speech over the data channel."""
        if not self.user_data.ctx or not self.user_data.ctx.room:
            print("Warning: Agent has no active session or room, cannot send data.")
            return

        chat_message = {
            "message": text,
            "is_final": is_final,
            "from": {
                "identity": self._agent_name or "design_agent",
                "name": self._agent_name or "Design Agent",
            },
            "timestamp": int(datetime.now().timestamp() * 1000),
        }
        json_message = json.dumps(chat_message)
        
        print(f"DEBUG: Sending agent transcript: {json_message}")
        await self.user_data.ctx.room.local_participant.publish_data(
            json_message, topic="lk-chat-topic"
        )

    def _truncate_chat_ctx(
        self,
        items: list,
        keep_last_n_messages: int = 6,
        keep_system_message: bool = False,
        keep_function_call: bool = False,
    ) -> list:
        if not items:
            return []

        def _is_valid_message(item) -> bool:
            return isinstance(item, ChatMessage) and item.content

        # Separate system message if it exists
        system_message = None
        if keep_system_message and items and _is_valid_message(items[0]) and items[0].role == 'system':
            system_message = items.pop(0)

        # Filter for valid ChatMessage objects
        messages = [item for item in items if _is_valid_message(item)]

        # Get the last N messages
        last_n_messages = messages[-keep_last_n_messages:]

        # Re-add the system message at the beginning
        if system_message:
            last_n_messages.insert(0, system_message)
        
        return last_n_messages

    async def _send_agent_state(self):
        """Send the current agent orchestration state to the frontend."""
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

    def get_design_session(self):
        """
        Get the DesignSession instance for workflow management.
        This replaces the old _transfer_to_agent and request_next_step methods.
        """
        # The DesignSession should be accessible through the user_data
        # This is set up during session initialization
        if hasattr(self.user_data, 'design_session'):
            return self.user_data.design_session
        return None

    @function_tool
    async def request_next_step(self, context: RunContext_T):
        """
        Request transition to the next agent in the workflow.
        This now delegates to the DesignSession for workflow management.
        """
        design_session = self.get_design_session()
        if design_session:
            return await design_session.handle_agent_transition(context)
        else:
            # Fallback if DesignSession is not available
            await self.speak("Sorry, I cannot proceed to the next step right now.")
            return self

    def _get_llm_context(self) -> "ChatContext":
        """
        Get the LLM context from the current agent.

        Design Decisions:
        - Prioritize `chat_history` over `chat_ctx` for robust context management
        - Create a new `ChatContext` if none exists to prevent errors

        Returns:
            ChatContext: The active chat context for the LLM
        """
        if hasattr(self.llm, 'chat_history'):
            return self.llm.chat_history
        elif hasattr(self.llm, 'chat_ctx'):
            return self.llm.chat_ctx
        return ChatContext()

    async def send_user_transcript(self, text: str, is_final: bool):
        """
        Send the user's transcribed text to all other participants in the room
        """
        if not self.user_data or not self.user_data.ctx or not self.user_data.ctx.room:
            print("Warning: Cannot send user transcript, room not available.")
            return

        # Find the human participant by looking for a participant that is not an agent.
        # This is more robust than assuming the user is always remote.
        user_participant = None
        all_participants = list(self.user_data.ctx.room.remote_participants.values()) + [self.user_data.ctx.room.local_participant]
        
        agent_identities = set(self.user_data.personas.keys())
        agent_identities.add(self._agent_name)  # Add current agent's name for good measure

        print(f"DEBUG: All participants in room: {[p.identity for p in all_participants]}")
        print(f"DEBUG: Known agent identities: {agent_identities}")

        for p in all_participants:
            if p.identity not in agent_identities:
                user_participant = p
                break
        
        if not user_participant:
            print("FATAL: Could not find a human participant in the room to attribute transcript to.")
            # As a last resort, use a generic identity, but this indicates a problem.
            from_info = {"identity": "user", "name": "User"}
        else:
            from_info = {
                "identity": user_participant.identity,
                "name": user_participant.name or self.user_data.first_name or "User",
            }

        chat_message = {
            "message": text,
            "is_final": is_final,
            "from": from_info,
            "timestamp": int(datetime.now().timestamp() * 1000),
        }
        json_message = json.dumps(chat_message)
        
        print(f"DEBUG: Sending user transcript: {json_message}")

        # The agent (local participant) publishes the data for everyone to see.
        await self.user_data.ctx.room.local_participant.publish_data(
            json_message, topic="lk-chat-topic"
        )

    @property
    def user_data(self):
        """
        Get the user data from the agent session context.
        """
        if not hasattr(self, 'session') or not hasattr(self.session, '_userdata'):
            # This can happen early in initialization.
            # We should decide on a more robust way to handle this, but for now,
            # returning None and ensuring callers handle it is a safe-ish bet.
            # A better solution might be to ensure user_data is not accessed
            # before the session is fully initialized.
            return None
        return self.session._userdata 