import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from design_assistant import (
    UserData,
    DesignCoachAgent,
    DesignStrategistAgent,
    DesignEvaluatorAgent,
)

class TestMultiAgentWorkflow(unittest.TestCase):
    def setUp(self):
        """Set up test environment before each test."""
        self.userdata = UserData()
        self.userdata.personas = {
            "design_coach": DesignCoachAgent(),
            "design_strategist": DesignStrategistAgent(),
            "design_evaluator": DesignEvaluatorAgent(),
        }

    @patch('design_assistant.AgentSession')
    async def test_workflow_transitions(self, mock_session):
        """Test the complete workflow transition between agents."""
        # Mock the session
        mock_session.userdata = self.userdata
        
        # Test initial state
        self.assertEqual(self.userdata.status, "awaiting_intent")
        
        # Simulate Design Coach interaction
        coach = self.userdata.personas["design_coach"]
        await coach.on_enter()
        self.assertEqual(self.userdata.status, "awaiting_problem_definition")
        
        # Simulate Design Strategist interaction
        strategist = self.userdata.personas["design_strategist"]
        await strategist.on_enter()
        self.assertEqual(self.userdata.status, "ready_for_evaluation")
        
        # Simulate Design Evaluator interaction
        evaluator = self.userdata.personas["design_evaluator"]
        await evaluator.on_enter()
        self.assertEqual(self.userdata.status, "evaluation_complete")

    @patch('design_assistant.AgentSession')
    async def test_agent_handoffs(self, mock_session):
        """Test that agents can properly hand off to each other."""
        mock_session.userdata = self.userdata
        
        # Test Coach to Strategist handoff
        coach = self.userdata.personas["design_coach"]
        next_agent = await coach.transfer_to_design_strategist(mock_session)
        self.assertIsInstance(next_agent, DesignStrategistAgent)
        
        # Test Strategist to Evaluator handoff
        strategist = self.userdata.personas["design_strategist"]
        next_agent = await strategist.transfer_to_design_evaluator(mock_session)
        self.assertIsInstance(next_agent, DesignEvaluatorAgent)

    def test_userdata_persistence(self):
        """Test that UserData maintains state between agent transitions."""
        # Set initial state
        self.userdata.status = "awaiting_intent"
        self.assertEqual(self.userdata.status, "awaiting_intent")
        
        # Update state
        self.userdata.status = "awaiting_problem_definition"
        self.assertEqual(self.userdata.status, "awaiting_problem_definition")
        
        # Verify state persists
        self.userdata.status = "ready_for_evaluation"
        self.assertEqual(self.userdata.status, "ready_for_evaluation")

if __name__ == '__main__':
    unittest.main() 