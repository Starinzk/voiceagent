"""
Design Strategist Agent Module
"""

from livekit.agents.llm import function_tool, ChatContext, ChatMessage
from livekit.agents.voice import RunContext
from .base_agent import BaseAgent
from design_assistant.design_utils import load_prompt

# Define a generic type for the RunContext for cleaner type hinting
from livekit.agents.voice import RunContext as RunContext_T

class DesignStrategistAgent(BaseAgent):
    '''
    An agent that refines problem statements and proposes initial solutions.
    '''
    def __init__(self) -> None:
        super().__init__(
            instructions=load_prompt('design_strategist.yaml'),
        )
        self._set_agent_name("design_strategist")

    async def on_enter(self) -> None:
        """
        Provide a greeting and instructions upon entry.
        """
        # Truncate context before the LLM call
        messages = []
        if hasattr(self.llm, 'chat_history') and hasattr(self.llm.chat_history, 'messages'):
            messages = self.llm.chat_history.messages

        truncated_messages = self._truncate_chat_ctx(
            messages,
            keep_last_n_messages=4,
            keep_system_message=True,
        )

        # Create a temporary context for the introductory message that includes history
        intro_prompt = ChatMessage(
            role="user", 
            content=["Based on the context, what should you say to the user right now? If there's a problem statement, ask if they want to refine it or propose a solution. If not, ask them to create one."]
        )
        
        temp_ctx = ChatContext(truncated_messages + [intro_prompt])

        # Generate the introductory message
        # Access the llm via the agent_session on user_data
        stream = self.user_data.agent_session.llm.chat(chat_ctx=temp_ctx)
        await self.speak(stream)

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
        chat_ctx = ChatContext([
            ChatMessage(role="system", content=self.instructions),
            ChatMessage(role="user", content=f"The user has provided the following problem statement: '{problem_statement}'. What is a good follow-up question to ask them?")
        ])
        
        # Generate the follow-up question
        try:
            stream = await self.user_data.agent_session.llm.chat(chat_ctx=chat_ctx)
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
    async def propose_solution(self, solution_description: str, key_features: list[str], context: RunContext_T):
        """Propose a solution to the user's design problem."""
        self.user_data.proposed_solution = solution_description
        self.user_data.design_iterations.append(
            {"solution": solution_description, "features": key_features}
        )
        await self.speak("That's a great starting point. I've noted that down.")
        return await self.request_next_step(context) 