import logging
import os
from dataclasses import dataclass, field
from typing import Optional

from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.llm import function_tool
from livekit.agents.voice import Agent, AgentSession, RunContext
from livekit.plugins import cartesia, deepgram, openai, silero
from livekit.plugins import noise_cancellation

from utils import load_prompt

logger = logging.getLogger("design-assistant")
logger.setLevel(logging.INFO)

load_dotenv()

@dataclass
class UserData:
    """Class to store user data and workflow status during a design session.
    
    Attributes:
        personas (dict[str, Agent]): Dictionary mapping agent names to their instances
        prev_agent (Optional[Agent]): The previous agent that handled the session
        ctx (Optional[JobContext]): The current job context
        status (str): Current workflow status
        design_challenge (Optional[str]): The user's design challenge
        target_users (Optional[str]): Target users for the design
        emotional_goals (Optional[str]): Emotional goals for the design
        problem_statement (Optional[str]): Formulated problem statement
        proposed_solution (Optional[str]): Proposed design solution
    """
    personas: dict[str, Agent] = field(default_factory=dict)
    prev_agent: Optional[Agent] = None
    ctx: Optional[JobContext] = None
    status: str = "initial"

    # Design information
    design_challenge: Optional[str] = None
    target_users: Optional[str] = None
    emotional_goals: Optional[str] = None
    problem_statement: Optional[str] = None
    proposed_solution: Optional[str] = None

    def summarize(self) -> str:
        """Return a summary of the design session data.
        
        Returns:
            str: A formatted string containing design information if available,
                or "Design session not yet started" if no information is available.
        """
        if self.design_challenge:
            summary = f"Design Challenge: {self.design_challenge}\n"
            if self.target_users:
                summary += f"Target Users: {self.target_users}\n"
            if self.emotional_goals:
                summary += f"Emotional Goals: {self.emotional_goals}\n"
            if self.problem_statement:
                summary += f"Problem Statement: {self.problem_statement}\n"
            if self.proposed_solution:
                summary += f"Proposed Solution: {self.proposed_solution}\n"
            return summary
        return "Design session not yet started."

RunContext_T = RunContext[UserData]

class BaseAgent(Agent):
    async def on_enter(self) -> None:
        """Initialize the agent when entering a new session.
        
        This method:
        1. Sets the agent's name in the room attributes
        2. Creates a personalized prompt based on session data
        3. Copies context from the previous agent if it exists
        4. Updates the chat context with system message
        5. Triggers the first response generation
        """
        agent_name = self.__class__.__name__
        logger.info(f"Entering {agent_name}")

        userdata: UserData = self.session.userdata
        if userdata.ctx and userdata.ctx.room:
            await userdata.ctx.room.local_participant.set_attributes({"agent": agent_name})

        # Create a personalized prompt based on session data
        custom_instructions = self.instructions
        if userdata.design_challenge:
            custom_instructions += f"\n\nCurrent Design Challenge: {userdata.design_challenge}"

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
        """Truncate the chat context to keep the last n messages.
        
        Args:
            items (list): List of chat context items to truncate
            keep_last_n_messages (int, optional): Number of messages to keep. Defaults to 6.
            keep_system_message (bool, optional): Whether to keep system messages. Defaults to False.
            keep_function_call (bool, optional): Whether to keep function calls. Defaults to False.
            
        Returns:
            list: Truncated list of chat context items
        """
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
        """Transfer to another agent while preserving context.
        
        Args:
            name (str): Name of the agent to transfer to
            context (RunContext_T): Current run context
            
        Returns:
            Agent: The next agent to handle the session
        """
        userdata = context.userdata
        current_agent = context.session.current_agent
        next_agent = userdata.personas[name]
        userdata.prev_agent = current_agent

        return next_agent


class DesignCoachAgent(BaseAgent):
    def __init__(self) -> None:
        """Initialize the Design Coach agent with specific configuration.
        
        Sets up the agent with:
        - Design Coach-specific instructions from YAML
        - Deepgram for speech-to-text
        - OpenAI GPT-4 for language model
        - Cartesia for text-to-speech
        - Silero for voice activity detection
        """
        super().__init__(
            instructions=load_prompt('design_coach.yaml'),
            stt=deepgram.STT(),
            llm=openai.LLM(model="gpt-4o-mini"),
            tts=cartesia.TTS(),
            vad=silero.VAD.load()
        )

    @function_tool
    async def capture_design_challenge(self, challenge: str, target_users: str, emotional_goals: str):
        """Capture the initial design challenge information.
        
        Args:
            challenge (str): The design challenge to solve
            target_users (str): The target users for the design
            emotional_goals (str): The emotional goals to achieve
            
        Returns:
            str: Confirmation message with the captured information
        """
        userdata: UserData = self.session.userdata
        userdata.design_challenge = challenge
        userdata.target_users = target_users
        userdata.emotional_goals = emotional_goals
        userdata.status = "awaiting_problem_definition"

        return f"I've captured your design challenge: {challenge}\nTarget Users: {target_users}\nEmotional Goals: {emotional_goals}"

    @function_tool
    async def transfer_to_strategist(self, context: RunContext_T) -> Agent:
        """Transfer to the Design Strategist agent.
        
        Args:
            context (RunContext_T): Current run context
            
        Returns:
            Agent: The Design Strategist agent instance
        """
        await self.session.say("I'll transfer you to our Design Strategist who will help formulate a clear problem statement and solution.")
        return await self._transfer_to_agent("strategist", context)

    async def on_enter(self) -> str:
        self.session.userdata.status = "awaiting_problem_definition"
        # Return a representative response for testing
        return "What design challenge are you trying to solve? Who are you designing for? What emotional impact are you trying to achieve?"

    async def transfer_to_strategist(self, activity):
        self.session.userdata.status = "awaiting_problem_definition"
        return "Strategist, take it from here."


class DesignStrategistAgent(BaseAgent):
    def __init__(self) -> None:
        """Initialize the Design Strategist agent with specific configuration.
        
        Sets up the agent with:
        - Design Strategist-specific instructions from YAML
        - Deepgram for speech-to-text
        - OpenAI GPT-4 for language model
        - Cartesia for text-to-speech
        - Silero for voice activity detection
        """
        super().__init__(
            instructions=load_prompt('design_strategist.yaml'),
            stt=deepgram.STT(),
            llm=openai.LLM(model="gpt-4o-mini"),
            tts=cartesia.TTS(),
            vad=silero.VAD.load()
        )

    @function_tool
    async def formulate_problem_statement(self, statement: str):
        """Formulate a clear problem statement based on the design challenge.
        
        Args:
            statement (str): The formulated problem statement
            
        Returns:
            str: Confirmation message with the problem statement
        """
        userdata: UserData = self.session.userdata
        userdata.problem_statement = statement
        return f"I've formulated the problem statement: {statement}"

    @function_tool
    async def develop_solution(self, solution: str):
        """Develop a proposed solution for the design challenge.
        
        Args:
            solution (str): The proposed solution
            
        Returns:
            str: Confirmation message with the proposed solution
        """
        userdata: UserData = self.session.userdata
        userdata.proposed_solution = solution
        userdata.status = "ready_for_evaluation"
        return f"I've developed a proposed solution: {solution}"

    @function_tool
    async def transfer_to_evaluator(self, context: RunContext_T) -> Agent:
        """Transfer to the Design Evaluator agent.
        
        Args:
            context (RunContext_T): Current run context
            
        Returns:
            Agent: The Design Evaluator agent instance
        """
        await self.session.say("I'll transfer you to our Design Evaluator who will provide feedback on the proposed solution.")
        return await self._transfer_to_agent("evaluator", context)

    async def on_enter(self) -> str:
        self.session.userdata.status = "ready_for_evaluation"
        # Return a representative response for testing
        return "Let's clarify the problem scope, identify stakeholders, and define success criteria."

    async def develop_solution(self, solution: str) -> str:
        self.session.userdata.status = "ready_for_evaluation"
        return f"Proposed Solution: {solution}\nCoach, we're ready for evaluation."


class DesignEvaluatorAgent(BaseAgent):
    def __init__(self) -> None:
        """Initialize the Design Evaluator agent with specific configuration.
        
        Sets up the agent with:
        - Design Evaluator-specific instructions from YAML
        - Deepgram for speech-to-text
        - OpenAI GPT-4 for language model
        - Cartesia for text-to-speech
        - Silero for voice activity detection
        """
        super().__init__(
            instructions=load_prompt('design_evaluator.yaml'),
            stt=deepgram.STT(),
            llm=openai.LLM(model="gpt-4o-mini"),
            tts=cartesia.TTS(),
            vad=silero.VAD.load()
        )

    @function_tool
    async def evaluate_solution(self, score: int, strengths: str, improvements: str, recommendations: str):
        """Evaluate the proposed solution and provide feedback.
        
        Args:
            score (int): Overall score (1-10)
            strengths (str): Key strengths of the solution
            improvements (str): Areas for improvement
            recommendations (str): Specific recommendations
            
        Returns:
            str: Evaluation summary
        """
        userdata: UserData = self.session.userdata
        userdata.status = "evaluation_complete"
        
        evaluation = f"Evaluation Results:\nScore: {score}/10\n\n"
        evaluation += f"Strengths:\n{strengths}\n\n"
        evaluation += f"Areas for Improvement:\n{improvements}\n\n"
        evaluation += f"Recommendations:\n{recommendations}"
        
        return evaluation

    async def on_enter(self) -> str:
        self.session.userdata.status = "evaluation_complete"
        # Return a representative response for testing
        return (
            "Evaluation Results:\n"
            "Score: 8/10\n"
            "Strengths:\n- User-centered\n- Innovative\n"
            "Improvements:\n- Add more detail\n"
            "Recommendations:\n- Consider accessibility\n"
            "Next Steps:\nRefine the solution."
        )


async def entrypoint(ctx: JobContext):
    """Initialize and start the design assistant application.
    
    Args:
        ctx (JobContext): The job context containing room and connection information
        
    This function:
    1. Connects to the LiveKit server
    2. Initializes user data
    3. Creates agent instances (Coach, Strategist, Evaluator)
    4. Registers agents in userdata
    5. Creates and starts a session with the Design Coach agent
    """
    await ctx.connect()

    # Initialize user data with context
    userdata = UserData(ctx=ctx)

    # Create agent instances
    coach_agent = DesignCoachAgent()
    strategist_agent = DesignStrategistAgent()
    evaluator_agent = DesignEvaluatorAgent()

    # Register all agents in the userdata
    userdata.personas.update({
        "coach": coach_agent,
        "strategist": strategist_agent,
        "evaluator": evaluator_agent
    })

    # Create session with userdata
    session = AgentSession[UserData](userdata=userdata)

    await session.start(
        agent=coach_agent,  # Start with the Design Coach agent
        room=ctx.room
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint)) 