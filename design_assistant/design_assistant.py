"""
Design Assistant Application

This module implements a design workflow system with three agents:
1. Design Coach - Initial agent that helps users articulate their design challenge
2. Design Strategist - Refines problem statements and proposes solutions
3. Design Evaluator - Evaluates solutions and provides structured feedback

Key Features:
- Multi-agent design workflow (Coach, Strategist, Evaluator)
- Supabase integration for user and session data persistence
- Dynamic context passing between agents
- Voice-enabled interaction using LiveKit, Deepgram, and Cartesia

Design Decisions:
- UserData class for centralized state management
- Modular agent design for clear separation of concerns
- Database persistence for all session-related data
- Simple user identification via name (no authentication)

Out of Scope:
- Database persistence (future feature)
- User authentication
- Cloud storage
- Real-time collaboration
- Analytics and reporting

Future Considerations:
- Database integration
- User authentication system
- Cloud storage integration
- Real-time updates
- Usage analytics
"""

import os
from dataclasses import dataclass, field
from typing import Optional, AsyncIterable
from datetime import datetime
import json
import asyncio
import sys

from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, WorkerType, cli, WorkerPermissions, JobRequest
from livekit.agents.llm import ChatContext, function_tool, ChatMessage
from livekit.agents.voice import Agent, AgentSession, RunContext, room_io
from livekit.agents import stt
from livekit.rtc import ConnectionState
from livekit.plugins import cartesia, deepgram, openai, silero

from design_assistant.design_utils import load_prompt
from design_assistant.design_database import DesignDatabase


load_dotenv()

# --- Environment Variable Check ---
REQUIRED_ENV_VARS = [
    "SUPABASE_URL",
    "SUPABASE_KEY",
    "OPENAI_API_KEY",
    "DEEPGRAM_API_KEY",
    "CARTESIA_API_KEY",
    "LIVEKIT_URL",
    "LIVEKIT_API_KEY",
    "LIVEKIT_API_SECRET",
]

missing_vars = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
if missing_vars:
    print("FATAL ERROR: The following required environment variables are not set:")
    for var in missing_vars:
        print(f"- {var}")
    print("\nPlease set them in your .env file before running the application.")
    sys.exit(1)
# --- End of Environment Variable Check ---


# Initialize the design database
print("--- DATABASE: Initializing DesignDatabase at module level ---")
db = DesignDatabase()
print("--- DATABASE: DesignDatabase initialized ---")

# Define the manager room name
MANAGER_ROOM = "agent-manager-room"

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

    # Design History
    design_iterations: list[dict] = field(default_factory=list)
    feedback_history: list[dict] = field(default_factory=list)

    # Database Integration
    db: Optional[DesignDatabase] = field(default=None, repr=False, metadata={
        'doc': 'Database connection for state persistence. Set during initialization.'
    })

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
            if field_name not in ['db', 'personas', 'prev_agent', 'ctx']:
                setattr(self, field_name, getattr(loaded_data, field_name))

# Define a generic type for the RunContext for cleaner type hinting
from livekit.agents.voice import RunContext as RunContext_T

class BaseAgent(Agent):
    '''Base class for all agents in the design workflow.'''
    def __init__(
        self,
        *,
        instructions: str,
        stt: "STT",
        llm: "LLM",
        tts: "TTS",
        vad: Optional["VAD"] = None,
    ):
        super().__init__(instructions=instructions, stt=stt, llm=llm, tts=tts, vad=vad)
        self.agent_name: Optional[str] = None

    def _set_agent_name(self, name: str):
        self.agent_name = name

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
        This function now separates the TTS action from the transcript sending action.
        """
        if isinstance(text_or_stream, str):
            # If it's a string, speak it and send the transcript
            await self._send_agent_transcript(text_or_stream, is_final=True)
            await self.session.say(text_or_stream)
        else:
            # If it's a stream, we need to collect it first to send the full
            # transcript, while still streaming the audio output.
            collected_chunks = []
            async def text_iterator():
                nonlocal collected_chunks
                async for chunk in text_or_stream:
                    collected_chunks.append(chunk)
                    await self._send_agent_transcript(chunk, is_final=False)
                    yield chunk

            # Speak the stream
            await self.session.say(text_iterator())

            # Once the stream is finished, send the full transcript
            full_text = "".join(collected_chunks)
            await self._send_agent_transcript(full_text, is_final=True)

    async def _send_agent_transcript(self, text: str, is_final: bool):
        """Sends the agent's speech over the data channel."""
        if not self.user_data.ctx or not self.user_data.ctx.room:
            print("Warning: Agent has no active session or room, cannot send data.")
            return

        chat_message = {
            "message": text,
            "is_final": is_final,
            "from": {
                "identity": self.agent_name or "design_agent",
                "name": self.agent_name or "Design Agent",
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

    async def _transfer_to_agent(self, name: str, context: RunContext_T) -> Agent:
        '''
        Transfer control to another agent.
        This is a common utility function that should be on the base agent.
        '''
        userdata: UserData = self.user_data
        
        # Set previous agent for context handoff
        userdata.prev_agent = self
        
        # Get the next agent from the shared personas dictionary
        next_agent = userdata.personas.get(name)
        if not next_agent:
            # Fallback or error handling
            await self.speak(f"Sorry, I could not find the {name} agent.")
            return self

        # Update the LLM context for the next agent
        if hasattr(self.llm, 'chat_history'):
            next_agent.llm.chat_history = self.llm.chat_history

        # Update context for the next agent
        if context:
            # Add a system message to the next agent's context
            sys_msg = ChatMessage(
                role=ChatMessage.ChatRole.SYSTEM,
                content=context,
            )
            next_agent.llm.chat_history.messages.append(sys_msg)

        return next_agent

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
        if not self.user_data.ctx or not self.user_data.ctx.room:
            print("Warning: Cannot send user transcript, room not available.")
            return

        # Find the human participant by looking for a participant that is not an agent.
        # This is more robust than assuming the user is always remote.
        user_participant = None
        all_participants = list(self.user_data.ctx.room.remote_participants.values()) + [self.user_data.ctx.room.local_participant]
        
        agent_identities = set(self.user_data.personas.keys())
        agent_identities.add(self.agent_name)  # Add current agent's name for good measure

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
    def user_data(self) -> "UserData":
        '''Convenience property to access UserData from the session.'''
        return self.session.userdata


class DesignCoachAgent(BaseAgent):
    '''An agent that helps users articulate their design challenge.'''
    def __init__(self) -> None:
        super().__init__(
            instructions=load_prompt('design_coach.yaml'),
            stt=deepgram.STT(),
            llm=openai.LLM(model="gpt-4-turbo", timeout=120.0),
            tts=openai.TTS(),
            vad=silero.VAD.load(min_silence_duration=1.2)
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
        response = f"Great. I will load session {session_id} for you now. One moment."
        await self.speak(response)
        return "Informing user that session will be loaded."

    @function_tool
    async def load_selected_session(self, context: RunContext_T) -> Agent:
        '''
        Loads a previously selected design session from the database.
        This function is called after the user confirms which session to load
        using `select_session_to_load`.
        '''
        userdata = self.user_data
        
        if not userdata.pending_session_id:
            # This should not happen if the flow is correct
            await self.speak("I'm sorry, I don't have a session selected to load.")
            return self

        try:
            # Load the state from the selected session ID
            userdata.load_state(userdata.pending_session_id)
            
            # Speak a confirmation message with loaded data
            summary = userdata.summarize()
            await self.speak(f"Session loaded successfully. Here is a summary of our progress:\n{summary}")
            
            # Decide which agent to transfer to based on loaded state
            if userdata.status == "ready_for_evaluation":
                await self.speak("It looks like we were ready for feedback. I'll transfer you to the Design Evaluator.")
                return await self._transfer_to_agent("design_evaluator", context)
            else: # Default to strategist
                await self.speak("Let's continue refining your solution. I'll transfer you to the Design Strategist.")
                return await self._transfer_to_agent("design_strategist", context)

        except ValueError as e:
            await self.speak(f"I'm sorry, I couldn't load that session. Error: {e}")
            return self
        except Exception as e:
            print(f"Error loading session: {e}")
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
        '''
        Captures the core components of the user's design challenge.
        '''
        userdata = self.user_data
        if not userdata.is_identified():
            await self.speak("Please identify yourself first using the identify_user function.")
            return "User not identified."
        
        userdata.design_challenge = design_challenge
        userdata.target_users = target_users
        userdata.emotional_goals = emotional_goals
        
        response = "Thank you. I have recorded your design challenge. Now, I will transfer you to our Design Strategist to help refine this into a problem statement."
        await self.speak(response)
        
        userdata.save_state()

        return "Design challenge captured."

    @function_tool
    async def transfer_to_strategist(self, context: RunContext_T) -> Agent:
        '''
        Transfer the user to the Design Strategist agent.
        '''
        await self.speak("Transferring you to the Design Strategist.")
        return await self._transfer_to_agent("design_strategist", context)


class DesignStrategistAgent(BaseAgent):
    '''
    An agent that refines problem statements and proposes initial solutions.
    '''
    def __init__(self) -> None:
        super().__init__(
            instructions=load_prompt('design_strategist.yaml'),
            stt=deepgram.STT(),
            llm=openai.LLM(model="gpt-4-turbo", timeout=120.0),
            tts=openai.TTS(),
            vad=silero.VAD.load(min_silence_duration=1.2)
        )
        self._set_agent_name("design_strategist")

    async def on_enter(self) -> None:
        """
        Provide a greeting and instructions upon entry.
        """
        # Truncate context before the LLM call
        chat_ctx = self.llm.chat_history if hasattr(self.llm, 'chat_history') else ChatContext()
        
        truncated_messages = self._truncate_chat_ctx(
            chat_ctx.messages,
            keep_last_n_messages=4,
            keep_system_message=True,
        )
        chat_ctx.messages = truncated_messages

        # Create a new context for the introductory message
        intro_ctx = ChatContext(messages=[
            ChatMessage(role="system", content=self.instructions),
            ChatMessage(role="user", content="Based on the context, what should you say to the user right now? If there's a problem statement, ask if they want to refine it or propose a solution. If not, ask them to create one."),
        ])
        
        # Generate the introductory message
        stream = await self.llm.chat(chat_ctx=intro_ctx)
        str_stream = self._llm_stream_to_str_stream(stream)
        
        # Speak the introduction
        await self.speak(str_stream)

    @function_tool
    async def refine_problem_statement(self, problem_statement: str) -> str:
        '''
        Refines the user's design challenge into a formal "How might we..."
        problem statement.
        '''
        userdata = self.user_data
        if not userdata.is_identified():
            await self.speak("Please identify yourself first using the identify_user function.")
            return "User not identified."
            
        if not userdata.design_challenge:
            await self.speak("Please provide a design challenge first using the capture_design_challenge function.")
            return "Design challenge not provided."

        # Update user data
        userdata.problem_statement = problem_statement
        userdata.save_state()

        # Prepare context for the LLM
        chat_ctx = ChatContext(messages=[
            ChatMessage(role="system", content=self.instructions),
            ChatMessage(role="user", content=f"The user has provided the following problem statement: '{problem_statement}'. What is a good follow-up question to ask them?")
        ])
        
        # Generate the follow-up question
        try:
            stream = await self.llm.chat(chat_ctx=chat_ctx)
            str_stream = self._llm_stream_to_str_stream(stream)
            response_text = ""
            async for chunk in str_stream:
                response_text += chunk

            await self.speak(f"Problem statement updated. {response_text}")
            return "Problem statement refined and follow-up question asked."
        except Exception as e:
            print(f"LLM Error in refine_problem_statement: {e}")
            await self.speak("Problem statement updated. Now, what's the first step we should take to solve this?")
            return "Problem statement refined."

    @function_tool
    async def propose_solution(self, solution_description: str, key_features: list[str], context: RunContext_T) -> Agent:
        '''
        Proposes a solution to the refined problem statement and transfers
        to the evaluator.
        '''
        userdata = self.user_data
        if not userdata.is_identified():
            await self.speak("Please identify yourself first using the identify_user function.")
            return self
            
        if not userdata.problem_statement:
            await self.speak("Please refine the problem statement first using the refine_problem_statement function.")
            return self

        # Update user data
        userdata.proposed_solution = solution_description
        userdata.design_iterations.append({
            "solution": solution_description,
            "features": key_features,
            "timestamp": datetime.now().isoformat()
        })
        userdata.status = "ready_for_evaluation"
        userdata.save_state()

        await self.speak("Thank you. I have recorded your proposed solution. Now, I will transfer you to our Design Evaluator for feedback.")
        return await self._transfer_to_agent("design_evaluator", context)

    @function_tool
    async def transfer_to_design_coach(self, context: RunContext_T) -> Agent:
        '''
        Transfer the user back to the Design Coach for clarification.
        
        This is useful when the conversation has lost direction and needs to
        be re-centered on the user's primary goals.
        '''
        userdata = self.user_data
        if userdata.is_identified():
            message = f"Thank you, {userdata.first_name}. I'll transfer you back to our Design Coach who can help you further clarify your intent."
        else:
            message = "I'll transfer you back to our Design Coach who can help you further clarify your intent."
        await self.speak(message)
        return await self._transfer_to_agent("design_coach", context)

    @function_tool
    async def transfer_to_design_evaluator(self, context: RunContext_T) -> Agent:
        '''
        Transfer the user to the Design Evaluator agent.
        '''
        userdata: UserData = self.user_data
        if userdata.is_identified():
            message = f"Thank you, {userdata.first_name}. I'll transfer you to our Design Evaluator for structured feedback."
        else:
            message = "I'll transfer you to our Design Evaluator for structured feedback."
        await self.speak(message)
        return await self._transfer_to_agent("design_evaluator", context)


class DesignEvaluatorAgent(BaseAgent):
    '''
    An agent responsible for evaluating solutions and providing structured feedback.
    '''
    def __init__(self) -> None:
        super().__init__(
            instructions=load_prompt('design_evaluator.yaml'),
            stt=deepgram.STT(),
            llm=openai.LLM(model="gpt-4-turbo", timeout=120.0),
            tts=openai.TTS(),
            vad=silero.VAD.load(min_silence_duration=1.2)
        )
        self._set_agent_name("design_evaluator")

    async def on_enter(self) -> None:
        """
        Set initial status when agent enters.
        """
        if not self.user_data.proposed_solution:
            self.user_data.status = "ready_for_evaluation"
        await super().on_enter()

    @function_tool
    async def provide_feedback(self, feedback: str) -> str:
        '''
        Provide feedback on the proposed solution.
        '''
        userdata = self.user_data
        if not userdata.is_identified():
            await self.speak("Please identify yourself first using the identify_user function.")
            return "User not identified."
            
        if not userdata.problem_statement:
            await self.speak("Please refine the problem statement first using the refine_problem_statement function.")
            return "Problem statement not refined."

        userdata.feedback_history.append({"feedback": feedback, "timestamp": datetime.now().isoformat()})
        userdata.status = "evaluation_complete"
        userdata.save_state()

        response = "Thank you for your feedback. I've recorded it. I am now transferring you back to the Design Strategist to iterate on the solution."
        await self.speak(response)
        return "Feedback recorded."

    @function_tool
    async def transfer_to_design_strategist(self, context: RunContext_T) -> Agent:
        '''
        Transfer the user to the Design Strategist agent.
        '''
        userdata: UserData = self.user_data
        if userdata.is_identified():
            message = f"Thank you, {userdata.first_name}. I'll transfer you to our Design Strategist for further refinement."
        else:
            message = "I'll transfer you to our Design Strategist for further refinement."
        await self.speak(message)
        return await self._transfer_to_agent("design_strategist", context)


async def entrypoint(ctx: JobContext):
    """Initialize and start the design assistant application in a worker."""
    print(f"\n=== WORKER AGENT JOB RECEIVED ===")
    print(f"Joining room: {ctx.room.name}")
    
    # It is critical to connect to the room before starting the agent session
    await ctx.connect()
    print(f"Successfully connected to room: {ctx.room.name}")
    
    userdata = UserData(ctx=ctx, db=db)
    
    userdata.personas["design_coach"] = DesignCoachAgent()
    userdata.personas["design_strategist"] = DesignStrategistAgent()
    userdata.personas["design_evaluator"] = DesignEvaluatorAgent()

    session = AgentSession[UserData](userdata=userdata)
    
    initial_agent = userdata.personas["design_coach"]
    
    output_options = room_io.RoomOutputOptions(transcription_enabled=True)
    await session.start(agent=initial_agent, room=ctx.room, room_output_options=output_options)

async def request_fnc(req: JobRequest):
    print("Received job request", req)
    await req.accept(
        identity="design_coach",
        metadata=json.dumps({"is_agent": "true"})
    )

if __name__ == "__main__":
    print("\n=== STARTING AGENT WORKER ===")

    permissions = WorkerPermissions(
        can_publish=True,
        can_publish_data=True,
        can_subscribe=True,
        hidden=False,
    )

    worker_opts = WorkerOptions(
        request_fnc=request_fnc,
        entrypoint_fnc=entrypoint,
        permissions=permissions,
    )

    # Add 'start' to the command-line arguments if no command is provided
    if len(sys.argv) < 2 or sys.argv[1] not in [
        "connect",
        "console",
        "dev",
        "download-files",
        "start",
    ]:
        sys.argv.insert(1, "start")

    cli.run_app(worker_opts)
