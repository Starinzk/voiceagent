"""
Design Evaluator Agent Module
"""

import json
from livekit.agents.llm import function_tool
from livekit.agents.voice import RunContext
from .base_agent import BaseAgent
from design_utils import load_prompt

# Define a generic type for the RunContext for cleaner type hinting
from livekit.agents.voice import RunContext as RunContext_T

# Import ClarityCapsule from the new user_data module
from user_data import ClarityCapsule

class DesignEvaluatorAgent(BaseAgent):
    '''
    An agent responsible for evaluating solutions and providing structured feedback.
    '''
    def __init__(self) -> None:
        super().__init__(
            instructions=load_prompt('design_evaluator.yaml'),
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
        """Provide feedback on the proposed solution."""
        self.user_data.feedback_history.append({"feedback": feedback})
        return "OK. I've noted that feedback. Please call request_next_step to conclude the session."

    @function_tool
    async def request_design_revision(self, context: RunContext_T, context_message: str):
        """
        Transfers control back to the Design Strategist to refine the solution
        based on new feedback or ideas from the user.
        """
        design_session = self.get_design_session()
        if design_session:
            return await design_session.handle_loop_back("DesignStrategistAgent", context_message)
        else:
            # Fallback if DesignSession is not available
            await self.speak("Sorry, I cannot process your revision request right now.")
            return self

    @function_tool
    async def generate_clarity_capsule(
        self,
        strengths: list[str],
        blind_spots: list[str],
        next_steps: list[str]
    ) -> str:
        """
        Generates and stores the final Clarity Capsule based on the entire session.
        This function synthesizes the key insights into a structured object.
        """
        capsule = ClarityCapsule(
            problem_statement=self.user_data.problem_statement,
            solution_concept=self.user_data.proposed_solution,
            strengths=strengths,
            blind_spots=blind_spots,
            next_steps=next_steps,
        )
        self.user_data.clarity_capsule = capsule
        self.user_data.status = "evaluation_complete"

        # Save the final state to the database
        self.user_data.save_state()

        # Send the capsule to the frontend
        capsule_data = {
            "type": "clarity_capsule",
            "problem_statement": capsule.problem_statement,
            "solution_concept": capsule.solution_concept,
            "strengths": capsule.strengths,
            "blind_spots": capsule.blind_spots,
            "next_steps": capsule.next_steps,
        }
        await self.user_data.ctx.room.local_participant.publish_data(
            json.dumps(capsule_data), topic="lk-chat-topic"
        )

        await self.speak("I've finished generating your Clarity Capsule. You should see it on your screen now. Thank you for using the Design Assistant!")

        return "Clarity Capsule generated and sent to frontend." 