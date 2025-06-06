"""
Design Assistant Application

This module implements a design workflow system with three agents:
1. Design Coach - Initial agent that helps users articulate their design challenge
2. Design Strategist - Refines problem statements and proposes solutions
3. Design Evaluator - Evaluates solutions and provides structured feedback

Design Decisions:
- In-memory state management for user data and session state
- Simple user identification via name
- No authentication required
- No persistence between sessions

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

from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.llm import function_tool
from livekit.agents.voice import Agent, AgentSession, RunContext
from livekit.plugins import cartesia, deepgram, openai, silero
from livekit.plugins import noise_cancellation

from design_utils import load_prompt
from design_database import CustomerDatabase

logger = logging.getLogger("design-assistant")
logger.setLevel(logging.INFO)

load_dotenv()

# Initialize the design database
db = CustomerDatabase()

@dataclass
class UserData:
    '''
    Class to store user data and agents during a design session.
    
    Design Decisions:
    - In-memory state management
    - Simple user identification via name
    - No authentication required
    - No persistence between sessions
    
    Out of Scope:
    - User authentication
    - Data persistence
    - Real-time collaboration
    - Analytics
    
    Future Considerations:
    - Database persistence
    - User authentication
    - Real-time updates
    - Analytics tracking
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

    # Design History
    design_iterations: list[dict] = field(default_factory=list)
    feedback_history: list[dict] = field(default_factory=list)

    def is_identified(self) -> bool:
        '''
        Check if the user is identified.
        
        Design Decisions:
        - Simple name-based identification
        - No authentication required
        - In-memory state only
        
        Limitations:
        - No persistence between sessions
        - No duplicate prevention
        
        Future Improvements:
        - Database persistence
        - User authentication
        - Duplicate prevention
        '''
        return self.first_name is not None and self.last_name is not None

    def reset(self) -> None:
        '''
        Reset all user information.
        
        Design Decisions:
        - Simple in-memory reset
        - No persistence
        
        Limitations:
        - No data backup
        - No history preservation
        
        Future Improvements:
        - Database persistence
        - History preservation
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
        if self.is_identified():
            return f"User: {self.first_name} {self.last_name} (ID: {self.user_id})"
        return "User not yet identified."

RunContext_T = RunContext[UserData]

class BaseAgent(Agent):
    '''
    Base class for all design agents.
    
    Design Decisions:
    - Common functionality for all agents
    - In-memory context management
    - No persistence between sessions
    
    Out of Scope:
    - Real-time collaboration
    - Multi-agent coordination
    - Analytics tracking
    
    Future Considerations:
    - Database persistence
    - Real-time updates
    - Multi-agent coordination
    - Analytics tracking
    '''

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
    Initial agent that helps users articulate their design challenge.
    
    Design Decisions:
    - First point of contact for users
    - Focuses on understanding user needs and challenges
    - Uses GPT-4 for high-quality responses
    - Maintains conversation context in memory
    
    Out of Scope:
    - Solution generation
    - Technical implementation
    - Design evaluation
    - Data persistence
    
    Future Considerations:
    - Multi-modal input (images, sketches)
    - Design pattern suggestions
    - Integration with design tools
    - Database persistence
    '''
    def __init__(self) -> None:
        '''
        Initialize the Design Coach agent with specific configuration.
        
        Design Decisions:
        - Uses GPT-4 for high-quality responses
        - Deepgram for accurate speech recognition
        - Cartesia for natural-sounding voice
        - Silero for reliable voice detection
        
        Example Configuration:
        ```python
        agent = DesignCoachAgent()
        # Agent will use:
        # - GPT-4 for understanding and responding
        # - Deepgram for converting speech to text
        # - Cartesia for converting text to speech
        # - Silero for detecting when user is speaking
        ```
        '''
        super().__init__(
            instructions=load_prompt('design_coach.yaml'),
            stt=deepgram.STT(),
            llm=openai.LLM(model="gpt-4o-mini"),
            tts=cartesia.TTS(),
            vad=silero.VAD.load()
        )

    @function_tool
    async def identify_user(self, first_name: str, last_name: str):
        '''
        Identify a user by their first and last name.
        
        Design Decisions:
        - Simple name-based identification
        - In-memory state only
        - No authentication required
        
        Example Usage:
        ```python
        # User provides their name
        await agent.identify_user("John", "Doe")
        # Creates in-memory user record
        # Returns: "Thank you, John. I've found your account."
        ```
        
        Limitations:
        - No persistence between sessions
        - No duplicate prevention
        - No user verification
        
        Future Improvements:
        - Database persistence
        - User authentication
        - Duplicate prevention
        '''
        userdata: UserData = self.session.userdata
        userdata.first_name = first_name
        userdata.last_name = last_name
        # TODO: Future feature - Implement database persistence
        # userdata.user_id = db.get_or_create_user(first_name, last_name)
        userdata.user_id = f"{first_name}_{last_name}"  # Temporary in-memory ID

        return f"Thank you, {first_name}. I've found your account."

    @function_tool
    async def capture_design_challenge(self, design_challenge: str, target_users: list[str], emotional_goals: list[str]):
        '''
        Capture the initial design challenge, target users, and emotional goals.
        
        Design Decisions:
        - Simple text-based capture
        - In-memory state only
        - No validation rules
        
        Example Usage:
        ```python
        # Capture initial design information
        await agent.capture_design_challenge(
            design_challenge="Design a mobile app for fitness tracking",
            target_users=["Fitness enthusiasts", "Busy professionals"],
            emotional_goals=["Feel motivated", "Stay committed"]
        )
        # Updates in-memory user data
        # Returns: "I've captured your design challenge and goals."
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

        # Update user data
        userdata.design_challenge = design_challenge
        userdata.target_users = target_users
        userdata.emotional_goals = emotional_goals
        userdata.status = "ready_for_evaluation"

        # TODO: Future feature - Implement database persistence
        # session_data = {
        #     'design_challenge': design_challenge,
        #     'target_users': target_users,
        #     'emotional_goals': emotional_goals,
        #     'status': userdata.status
        # }
        # db.save_design_session(userdata.user_id, session_data)

        return "I've captured your design challenge and goals. Let's work on refining the problem statement."

    @function_tool
    async def transfer_to_design_strategist(self, context: RunContext_T) -> Agent:
        '''
        Transfer the user to the Design Strategist agent.
        
        Design Decisions:
        - Preserves conversation context
        - Provides personalized message
        - Smooth transition between agents
        
        Example Usage:
        ```python
        # When user is ready for strategy
        await agent.transfer_to_design_strategist(context)
        # Transfers to strategist with context
        # Returns: Design Strategist agent instance
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
            message = f"Thank you, {userdata.first_name}. Strategist, take it from here."
        else:
            message = "Strategist, take it from here."

        await self.session.say(message)
        return await self._transfer_to_agent("design_strategist", context)

    @function_tool
    async def transfer_to_design_evaluator(self, context: RunContext_T) -> Agent:
        '''
        Transfer the user to the Design Evaluator agent.
        
        Design Decisions:
        - Preserves conversation context
        - Provides personalized message
        - Smooth transition between agents
        
        Example Usage:
        ```python
        # When user is ready for evaluation
        await agent.transfer_to_design_evaluator(context)
        # Transfers to evaluator with context
        # Returns: Design Evaluator agent instance
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
            message = f"Thank you, {userdata.first_name}. I'll transfer you to our Design Evaluator who can provide feedback on your design."
        else:
            message = "I'll transfer you to our Design Evaluator who can provide feedback on your design."

        await self.session.say(message)
        return await self._transfer_to_agent("design_evaluator", context)


class DesignStrategistAgent(BaseAgent):
    '''
    Agent responsible for refining problem statements and proposing solutions.
    
    Design Decisions:
    - Focuses on problem analysis and solution design
    - Uses GPT-4 for strategic thinking
    - Maintains design context in memory
    - Provides structured problem statements
    
    Out of Scope:
    - Technical implementation details
    - User research
    - Final design evaluation
    - Data persistence
    
    Future Considerations:
    - Design pattern library integration
    - Solution templates
    - Design system integration
    - Database persistence
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
            llm=openai.LLM(model="gpt-4o-mini"),
            tts=cartesia.TTS(),
            vad=silero.VAD.load()
        )

    async def on_enter(self) -> None:
        '''
        Set initial status when agent enters.
        
        Design Decisions:
        - Updates session status
        - Preserves conversation context
        - Maintains design state
        
        Example Usage:
        ```python
        # When agent starts
        await agent.on_enter()
        # Updates status to "ready_for_evaluation"
        # Preserves conversation context
        ```
        
        Limitations:
        - No real-time status updates
        - No multi-agent coordination
        - No session persistence
        
        Future Improvements:
        - Real-time status updates
        - Multi-agent coordination
        - Session persistence
        '''
        self.session.userdata.status = "ready_for_evaluation"
        await super().on_enter()

    @function_tool
    async def identify_user(self, first_name: str, last_name: str):
        '''
        Identify a user by their first and last name.
        '''
        userdata: UserData = self.session.userdata
        userdata.first_name = first_name
        userdata.last_name = last_name
        # TODO: Future feature - Implement database persistence
        # userdata.user_id = db.get_or_create_user(first_name, last_name)
        userdata.user_id = f"{first_name}_{last_name}"  # Temporary in-memory ID

        return f"Thank you, {first_name}. I've found your account."

    @function_tool
    async def refine_problem_statement(self, problem_statement: str):
        '''
        Refine the problem statement based on the design challenge and goals.
        
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

        # TODO: Future feature - Implement database persistence
        # session_data = {
        #     'problem_statement': problem_statement,
        #     'status': userdata.status
        # }
        # db.save_design_session(userdata.user_id, session_data)

        return "I've refined your problem statement. Let's work on proposing solutions."

    @function_tool
    async def propose_solution(self, solution: str):
        '''
        Propose a solution based on the refined problem statement.
        
        Design Decisions:
        - Simple text-based solution
        - In-memory state only
        - Tracks design iterations in memory
        
        Example Usage:
        ```python
        # Propose a solution
        await agent.propose_solution(
            "A mobile app with gamified fitness tracking, social features, and personalized goals to keep users motivated."
        )
        # Updates in-memory user data
        # Returns: "I've recorded your solution. Let's evaluate it."
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
            
        if not userdata.problem_statement:
            return "Please refine the problem statement first using the refine_problem_statement function."

        # Update user data
        userdata.proposed_solution = solution
        userdata.status = "ready_for_evaluation"
        
        # Track this iteration
        iteration = {
            'problem_statement': userdata.problem_statement,
            'solution': solution,
            'timestamp': datetime.now().isoformat()
        }
        userdata.design_iterations.append(iteration)

        # TODO: Future feature - Implement database persistence
        # session_data = {
        #     'proposed_solution': solution,
        #     'status': userdata.status,
        #     'design_iterations': userdata.design_iterations
        # }
        # db.save_design_session(userdata.user_id, session_data)

        return f"Problem Statement: {userdata.problem_statement}\nProposed Solution: {solution}\nCoach, we're ready for evaluation."

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
        
        Design Decisions:
        - Preserves conversation context
        - Provides personalized message
        - Smooth transition between agents
        
        Example Usage:
        ```python
        # When solution is ready for evaluation
        await agent.transfer_to_design_evaluator(context)
        # Transfers to evaluator with context
        # Returns: Design Evaluator agent instance
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
            message = f"Thank you, {userdata.first_name}. I'll transfer you to our Design Evaluator for structured feedback."
        else:
            message = "I'll transfer you to our Design Evaluator for structured feedback."
        await self.session.say(message)
        return await self._transfer_to_agent("design_evaluator", context)


class DesignEvaluatorAgent(BaseAgent):
    '''
    Agent responsible for evaluating solutions and providing structured feedback.
    
    Design Decisions:
    - Focuses on solution evaluation
    - Uses GPT-4 for comprehensive analysis
    - Provides structured feedback
    - Maintains evaluation history in memory
    
    Out of Scope:
    - Solution generation
    - User research
    - Technical implementation
    - Data persistence
    
    Future Considerations:
    - Evaluation templates
    - Metrics tracking
    - A/B testing support
    - Database persistence
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
            llm=openai.LLM(model="gpt-4o-mini"),
            tts=cartesia.TTS(),
            vad=silero.VAD.load()
        )

    async def on_enter(self) -> None:
        '''
        Set initial status when agent enters.
        '''
        self.session.userdata.status = "evaluation_complete"
        await super().on_enter()

    @function_tool
    async def identify_user(self, first_name: str, last_name: str):
        '''
        Identify a user by their first and last name.
        '''
        userdata: UserData = self.session.userdata
        userdata.first_name = first_name
        userdata.last_name = last_name
        # TODO: Future feature - Implement database persistence
        # userdata.user_id = db.get_or_create_user(first_name, last_name)
        userdata.user_id = f"{first_name}_{last_name}"  # Temporary in-memory ID

        return f"Thank you, {first_name}. I've found your account."

    @function_tool
    async def transfer_to_design_strategist(self, context: RunContext_T) -> Agent:
        '''
        Transfer the user to the Design Strategist agent.
        '''
        userdata: UserData = self.session.userdata
        if userdata.is_identified():
            message = f"Thank you, {userdata.first_name}. I'll transfer you to our Design Strategist who can help you refine your design."
        else:
            message = "I'll transfer you to our Design Strategist who can help you refine your design."

        await self.session.say(message)
        return await self._transfer_to_agent("design_strategist", context)


async def entrypoint(ctx: JobContext):
    """Initialize and start the design assistant application.
    
    Args:
        ctx (JobContext): The job context containing room and connection information
        
    This function:
    1. Connects to the LiveKit server
    2. Initializes user data
    3. Creates agent instances (Design Coach, Design Strategist, Design Evaluator)
    4. Registers agents in userdata
    5. Creates and starts a session with the Design Coach agent
    """
    await ctx.connect()

    # Initialize user data with context
    userdata = UserData(ctx=ctx)

    # Create agent instances
    design_coach_agent = DesignCoachAgent()
    design_strategist_agent = DesignStrategistAgent()
    design_evaluator_agent = DesignEvaluatorAgent()

    # Register all agents in the userdata
    userdata.personas.update({
        "design_coach": design_coach_agent,
        "design_strategist": design_strategist_agent,
        "design_evaluator": design_evaluator_agent
    })

    # Create session with userdata
    session = AgentSession[UserData](userdata=userdata)

    await session.start(
        agent=design_coach_agent,  # Start with the Design Coach agent
        room=ctx.room
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
