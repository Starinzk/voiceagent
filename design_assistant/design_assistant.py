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

import logging
import os
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
import json
import asyncio
import sys

from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, WorkerType, cli, WorkerPermissions, JobRequest
from livekit.agents.llm import function_tool
from livekit.agents.voice import Agent, AgentSession, RunContext
from livekit.plugins import cartesia, deepgram, openai, silero

from design_assistant.design_utils import load_prompt
from design_assistant.design_database import DesignDatabase

logger = logging.getLogger("design-assistant")
logger.setLevel(logging.INFO)

load_dotenv()

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
        for field in self.__dataclass_fields__:
            if field not in ['db', 'personas', 'prev_agent', 'ctx']:
                setattr(self, field, getattr(loaded_data, field))

RunContext_T = RunContext[UserData]

class BaseAgent(Agent):
    '''
    Base class for all design agents, providing common functionality.

    This class handles agent initialization, context management, and chat history
    truncation. It ensures a smooth transition of context when switching between
    different agents in the design workflow.
    '''
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

    async def on_enter(self) -> None:
        '''
        Initialize the agent when entering a new session.
        
        Design Decisions:
        - Simple initialization
        - In-memory state only
        - No persistence
        
        Limitations:
        - No authentication
        - No session persistence
        
        Future Improvements:
        - Database persistence
        - Authentication
        - Session persistence
        '''
        agent_name = self.__class__.__name__
        logger.info(f"Entering {agent_name}")

        userdata: UserData = self.session.userdata
        if userdata.ctx and userdata.ctx.room:
            await userdata.ctx.room.local_participant.set_attributes({"agent": agent_name})

        # Create a personalized prompt based on user identification
        custom_instructions = self.instructions
        if userdata.is_identified():
            custom_instructions += f"\n\nYou are speaking with {userdata.first_name} {userdata.last_name}."
        
        self.llm.instructions = custom_instructions

        chat_ctx = self.chat_ctx.copy()

        # Copy context from previous agent if it exists
        if userdata.prev_agent:
            items_copy = self._truncate_chat_ctx(
                userdata.prev_agent.chat_ctx.items, keep_function_call=True
            )
            existing_ids = {item.id for item in chat_ctx.items}
            items_copy = [item for item in items_copy if item.id not in existing_ids]
            chat_ctx.items.extend(items_copy)

        chat_ctx.add_message(
            role="system",
            content=f"You are the {agent_name}. {userdata.summarize()}"
        )
        await self.update_chat_ctx(chat_ctx)

        logger.info(f"ON_ENTER: Generating reply for {agent_name} with instructions: {self.llm.instructions[:100]}...")
        for i, item in enumerate(self.chat_ctx.items):
            if hasattr(item, 'role'):
                logger.info(f"  - Chat history[{i}]: {item.role} - {item.content[:100]}...")
            else:
                logger.info(f"  - Chat history[{i}]: {type(item)}")

        self.session.generate_reply()

    def _truncate_chat_ctx(
        self,
        items: list,
        keep_last_n_messages: int = 6,
        keep_system_message: bool = False,
        keep_function_call: bool = False,
    ) -> list:
        '''
        Truncate the chat context to keep the last n messages.
        
        Design Decisions:
        - Simple truncation
        - In-memory only
        - No persistence
        
        Limitations:
        - No context persistence
        - No context sharing
        
        Future Improvements:
        - Database persistence
        - Context sharing
        '''
        def _valid_item(item) -> bool:
            if not keep_system_message and item.type == "message" and item.role == "system":
                return False
            if not keep_function_call and item.type in ["function_call", "function_call_output"]:
                return False
            return True

        new_items = []
        for item in reversed(items):
            if _valid_item(item):
                new_items.append(item)
            if len(new_items) >= keep_last_n_messages:
                break
        new_items = new_items[::-1]

        while new_items and new_items[0].type in ["function_call", "function_call_output"]:
            new_items.pop(0)

        return new_items

    async def _transfer_to_agent(self, name: str, context: RunContext_T) -> Agent:
        '''
        Transfer to another agent while preserving context.
        
        Design Decisions:
        - Simple transfer mechanism
        - In-memory context preservation
        - No persistence
        
        Limitations:
        - No session persistence
        - No multi-agent coordination
        
        Future Improvements:
        - Database persistence
        - Multi-agent coordination
        - Session persistence
        '''
        userdata = context.userdata
        current_agent = context.session.current_agent
        next_agent = userdata.personas[name]
        userdata.prev_agent = current_agent

        return next_agent


class DesignCoachAgent(BaseAgent):
    '''
    The first agent that the user interacts with. Its goal is to
    identify the user and understand their design challenge.
    '''
    def __init__(self) -> None:
        super().__init__(
            instructions=load_prompt('design_coach.yaml'),
            stt=deepgram.STT(),
            llm=openai.LLM(model="gpt-4-turbo", timeout=30.0),
            tts=cartesia.TTS(),
            vad=silero.VAD.load(min_silence_duration=0.8),
        )
        self._set_agent_name("design_coach")

    async def on_enter(self) -> None:
        self.session.userdata.status = "awaiting_user_identification"
        await super().on_enter()

    @function_tool
    async def identify_user(self, first_name: str, last_name: str) -> str:
        """
        Identifies the user by their first and last name.
        """
        userdata: UserData = self.session.userdata
        userdata.first_name = first_name
        userdata.last_name = last_name
        userdata.user_id = userdata.db.get_or_create_user(first_name, last_name)
        userdata.status = "awaiting_design_challenge"
        
        response_message = f"Thank you, {first_name}. Now, please describe your design challenge, your target users, and your emotional goals."
        await self.session.say(response_message)
        return f"User {first_name} {last_name} identified. The conversation can now proceed to the design challenge."

    @function_tool
    async def capture_design_challenge(self, design_challenge: str, target_users: list[str], emotional_goals: list[str]) -> str:
        '''
        Capture the core components of a new design challenge.
        '''
        userdata: UserData = self.session.userdata
        
        userdata.design_challenge = design_challenge
        userdata.target_users = target_users
        userdata.emotional_goals = emotional_goals
        userdata.status = "problem_defined" 
        userdata.save_state()

        response_message = "Thank you. I've captured your design challenge. I'll now transfer you to our Design Strategist. Please say 'continue' or 'proceed'."
        await self.session.say(response_message)
        return "Design challenge captured. Ready to transfer to the strategist."

    @function_tool
    async def transfer_to_strategist(self, context: RunContext_T) -> Agent:
        '''
        Transfers the user to the Design Strategist agent.
        '''
        await self.session.say("Handing you over to our Design Strategist.")
        return await self._transfer_to_agent("design_strategist", context)


class DesignStrategistAgent(BaseAgent):
    '''
    An agent responsible for refining problem statements and proposing solutions.
    
    The Design Strategist takes the initial design challenge from the Coach
    and helps the user refine it into a structured "How might we..." problem
    statement. It then guides the user in proposing a solution to that
    problem. All progress is persisted to the database.
    
    Out of Scope:
    - Technical implementation details
    - User research
    - Final design evaluation
    '''
    def __init__(self) -> None:
        '''
        Initialize the Design Strategist agent with specific configuration.
        
        Design Decisions:
        - Uses GPT-4 for strategic thinking
        - Deepgram for accurate speech recognition
        - Cartesia for natural-sounding voice
        - Silero for reliable voice detection
        
        Example Configuration:
        ```python
        agent = DesignStrategistAgent()
        # Agent will use:
        # - GPT-4 for strategic analysis
        # - Deepgram for converting speech to text
        # - Cartesia for converting text to speech
        # - Silero for detecting when user is speaking
        ```
        '''
        super().__init__(
            instructions=load_prompt('design_strategist.yaml'),
            stt=deepgram.STT(),
            llm=openai.LLM(model="gpt-4-turbo", timeout=30.0),
            tts=cartesia.TTS(),
            vad=silero.VAD.load(min_silence_duration=0.8)
        )

    async def on_enter(self) -> None:
        '''
        Set initial status when agent enters.
        '''
        self.session.userdata.status = "awaiting_problem_statement"
        await super().on_enter()

    @function_tool
    async def refine_problem_statement(self, problem_statement: str) -> str:
        '''
        Refine the problem statement into a "How might we..." question.
        
        Design Decisions:
        - Simple text-based refinement
        - In-memory state only
        - Must use "How might we..." format
        
        Example Usage:
        ```python
        # Refine problem statement
        await agent.refine_problem_statement(
            "How might we create a mobile app that helps busy professionals track their fitness goals while maintaining motivation?"
        )
        # Updates in-memory user data
        # Returns: "I've refined your problem statement. Let's work on proposing solutions."
        ```
        
        Limitations:
        - No persistence between sessions
        - No input validation
        
        Future Improvements:
        - Database persistence
        - Input validation
        '''
        userdata: UserData = self.session.userdata
        if not userdata.is_identified():
            return "Please identify yourself first using the identify_user function."
            
        if not userdata.design_challenge:
            return "Please capture the design challenge first using the Design Coach agent."

        # Check for "How might we..." format
        if not problem_statement.lower().startswith("how might we"):
            return "Problem statement must start with 'How might we...' to follow design thinking best practices."

        # Update user data
        userdata.problem_statement = problem_statement
        userdata.status = "ready_for_evaluation"

        # Persist the updated state to the database
        userdata.save_state()

        return "I've refined your problem statement. Let's work on proposing solutions."

    @function_tool
    async def propose_solution(self, solution_description: str, key_features: list[str], context: RunContext_T) -> Agent:
        '''
        Propose a detailed solution with specific features.
        
        Args:
            solution_description (str): A clear, concise description of the proposed solution.
            key_features (list[str]): A list of specific, key features of the solution.
        '''
        userdata: UserData = self.session.userdata
        if not userdata.is_identified():
            return "Please identify yourself first using the identify_user function."
            
        if not userdata.problem_statement:
            return "Please refine the problem statement first using the refine_problem_statement function."

        # Update user data
        userdata.proposed_solution = solution_description
        userdata.status = "evaluation_complete" # Ready for the evaluator
        
        # Track this iteration
        iteration = {
            'problem_statement': userdata.problem_statement,
            'solution': solution_description,
            'key_features': key_features,
            'timestamp': datetime.now().isoformat()
        }
        userdata.design_iterations.append(iteration)

        # Persist the updated state to the database
        userdata.save_state()

        await self.session.say(f"Solution captured. Transferring to the Design Evaluator for feedback.")
        return await self._transfer_to_agent("design_evaluator", context)

    @function_tool
    async def transfer_to_design_coach(self, context: RunContext_T) -> Agent:
        '''
        Transfer the user back to the Design Coach agent.
        
        Design Decisions:
        - Preserves conversation context
        - Provides personalized message
        - Smooth transition between agents
        
        Example Usage:
        ```python
        # When user needs to clarify design challenge
        await agent.transfer_to_design_coach(context)
        # Transfers to coach with context
        # Returns: Design Coach agent instance
        ```
        
        Limitations:
        - No real-time updates
        - No multi-agent coordination
        - No session persistence
        
        Future Improvements:
        - Real-time updates
        - Multi-agent coordination
        - Session persistence
        '''
        userdata: UserData = self.session.userdata
        if userdata.is_identified():
            message = f"Thank you, {userdata.first_name}. I'll transfer you back to our Design Coach who can help you further clarify your intent."
        else:
            message = "I'll transfer you back to our Design Coach who can help you further clarify your intent."
        await self.session.say(message)
        return await self._transfer_to_agent("design_coach", context)

    @function_tool
    async def transfer_to_design_evaluator(self, context: RunContext_T) -> Agent:
        '''
        Transfer the user to the Design Evaluator agent.
        '''
        userdata: UserData = self.session.userdata
        if userdata.is_identified():
            message = f"Thank you, {userdata.first_name}. I'll transfer you to our Design Evaluator for structured feedback."
        else:
            message = "I'll transfer you to our Design Evaluator for structured feedback."
        await self.session.say(message)
        return await self._transfer_to_agent("design_evaluator", context)


class DesignEvaluatorAgent(BaseAgent):
    '''
    An agent responsible for evaluating solutions and providing structured feedback.

    The Design Evaluator is intended to provide structured, objective feedback on a
    proposed solution.
    
    Out of Scope:
    - Solution generation
    - User research
    - Technical implementation
    '''
    def __init__(self) -> None:
        '''
        Initialize the Design Evaluator agent with specific configuration.
        
        Design Decisions:
        - Uses GPT-4 for comprehensive analysis
        - Deepgram for accurate speech recognition
        - Cartesia for natural-sounding voice
        - Silero for reliable voice detection
        '''
        super().__init__(
            instructions=load_prompt('design_evaluator.yaml'),
            stt=deepgram.STT(),
            llm=openai.LLM(model="gpt-4-turbo", timeout=30.0),
            tts=cartesia.TTS(),
            vad=silero.VAD.load(min_silence_duration=0.8)
        )

    async def on_enter(self) -> None:
        '''
        Set initial status and provide context to the LLM when the agent enters.
        '''
        self.session.userdata.status = "evaluation_complete"
        userdata: UserData = self.session.userdata

        # Create a new system message with the problem statement and proposed solution.
        # This will be added to the chat history for the LLM to use as context.
        contextual_message = (
            "The user has provided the following context for evaluation:\n\n"
            f"**Problem Statement:**\n{userdata.problem_statement}\n\n"
            f"**Proposed Solution:**\n{userdata.proposed_solution}\n\n"
            "Please begin by acknowledging that you have received this context, "
            "then proceed with your evaluation."
        )
        
        # Add the context to the chat history.
        new_chat_ctx = self.chat_ctx.copy()
        new_chat_ctx.add_message(role="system", content=contextual_message)
        await self.update_chat_ctx(new_chat_ctx)

        await super().on_enter()

    @function_tool
    async def provide_feedback(self, feedback: str) -> str:
        '''
        Provide feedback on the proposed solution.
        
        Design Decisions:
        - Simple text-based feedback
        - In-memory state only
        
        Limitations:
        - No persistence between sessions
        - No input validation
        
        Future Improvements:
        - Database persistence
        - Input validation
        '''
        userdata: UserData = self.session.userdata
        if not userdata.is_identified():
            return "Please identify yourself first using the identify_user function."
            
        if not userdata.problem_statement:
            return "Please refine the problem statement first using the refine_problem_statement function."

        # Update user data
        userdata.feedback_history.append(feedback)
        userdata.save_state()

        return "Thank you for your feedback. I've recorded it in the session."

    @function_tool
    async def transfer_to_design_strategist(self, context: RunContext_T) -> Agent:
        '''
        Transfer the user to the Design Strategist agent.
        '''
        userdata: UserData = self.session.userdata
        if userdata.is_identified():
            message = f"Thank you, {userdata.first_name}. I'll transfer you to our Design Strategist for further refinement."
        else:
            message = "I'll transfer you to our Design Strategist for further refinement."
        await self.session.say(message)
        return await self._transfer_to_agent("design_strategist", context)


async def spawn_worker(room_name: str):
    """This function will be called to spawn a new agent in a specific room."""
    print(f"Spawning a new worker for room: {room_name}")
    
    worker_opts = WorkerOptions(
        entrypoint_fnc=entrypoint,
        worker_type=WorkerType.PUBLISHER,
        agent_name="design_assistant_worker", # Use a different name for spawned workers
        ws_url=os.getenv('LIVEKIT_URL'),
        api_key=os.getenv('LIVEKIT_API_KEY'),
        api_secret=os.getenv('LIVEKIT_API_SECRET'),
        room_name=room_name, # Assign the specific room
    )
    # This starts a new agent process
    process = await cli.run_app(worker_opts)
    print(f"Worker process for room {room_name} started: {process}")


async def manager_entrypoint(ctx: JobContext):
    """The entrypoint for the main manager agent."""
    print(f"Manager agent connected to room: {ctx.room.name}")

    async def handle_data(data: str, participant, room):
        try:
            payload = json.loads(data)
            if payload.get('type') == 'AGENT_REQUEST':
                user_room = payload.get('userRoomName')
                if user_room:
                    print(f"Received agent request for room: {user_room}")
                    # Use asyncio.create_task to spawn the worker without blocking
                    asyncio.create_task(spawn_worker(user_room))
        except Exception as e:
            print(f"Error handling agent request: {e}")

    ctx.room.on('data_received', handle_data)
    print("Manager is listening for agent requests...")

# This is the entrypoint for the worker agents
async def entrypoint(ctx: JobContext):
    """Initialize and start the design assistant application in a worker."""
    print(f"\n=== WORKER AGENT JOB RECEIVED ===")
    print(f"Joining room: {ctx.room.name}")
    
    userdata = UserData(ctx=ctx, db=db)
    
    # Initialize all agents and store them in the userdata
    userdata.personas["design_coach"] = DesignCoachAgent()
    userdata.personas["design_strategist"] = DesignStrategistAgent()
    userdata.personas["design_evaluator"] = DesignEvaluatorAgent()

    session = AgentSession[UserData](userdata=userdata)
    
    # The first agent to be used in the session
    initial_agent = userdata.personas["design_coach"]
    
    await session.start(agent=initial_agent, room=ctx.room)

async def request_fnc(req: JobRequest):
    print("Received job request", req)
    await req.accept()

if __name__ == "__main__":
    print("\n=== STARTING AGENT WORKER ===")
    
    worker_opts = WorkerOptions(
        request_fnc=request_fnc,
        entrypoint_fnc=entrypoint # Add the default entrypoint
    )
    
    # Add 'start' to the command-line arguments if no command is provided
    if len(sys.argv) < 2 or sys.argv[1] not in ['connect', 'console', 'dev', 'download-files', 'start']:
        sys.argv.insert(1, 'start')

    cli.run_app(worker_opts)
