"""
Simplified Test Suite for Refactored Design Workflow

This test suite validates the new modular architecture after the backend refactoring.
It focuses on testing the core functionality without complex mocking.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from design_assistant.agents import DesignCoachAgent, DesignStrategistAgent, DesignEvaluatorAgent
from design_assistant.user_data import UserData, ClarityCapsule
from design_assistant.session import DesignSession
from design_assistant.design_database import DesignDatabase

# Test Data
TEST_USER = {
    'first_name': 'John',
    'last_name': 'Doe'
}

TEST_DESIGN_CHALLENGE = {
    'design_challenge': 'Design a mobile app for fitness tracking',
    'target_users': ['Fitness enthusiasts', 'Busy professionals'],
    'emotional_goals': ['Feel motivated', 'Stay committed']
}

TEST_PROBLEM_STATEMENT = "How might we create a mobile app that helps busy professionals track their fitness goals while maintaining motivation?"
TEST_SOLUTION = "A mobile app with gamified fitness tracking, social features, and personalized goals to keep users motivated."

class TestModularArchitecture:
    """Test the new modular architecture components."""

    def test_user_data_creation(self):
        """Test UserData can be created and basic methods work."""
        user_data = UserData()
        assert user_data.status == "awaiting_problem_definition"
        assert user_data.current_agent_name == "DesignCoachAgent"
        assert not user_data.is_identified()
        
        # Test setting user info
        user_data.first_name = TEST_USER['first_name']
        user_data.last_name = TEST_USER['last_name']
        assert user_data.is_identified()

    def test_clarity_capsule_creation(self):
        """Test ClarityCapsule can be created."""
        capsule = ClarityCapsule(
            problem_statement=TEST_PROBLEM_STATEMENT,
            solution_concept=TEST_SOLUTION,
            strengths=["Clear goals", "User-friendly"],
            blind_spots=["Privacy concerns", "Battery usage"],
            next_steps=["User testing", "MVP development"]
        )
        assert capsule.problem_statement == TEST_PROBLEM_STATEMENT
        assert len(capsule.strengths) == 2

    def test_agents_creation(self):
        """Test all agents can be instantiated."""
        coach = DesignCoachAgent()
        strategist = DesignStrategistAgent()
        evaluator = DesignEvaluatorAgent()
        
        assert coach._agent_name == "design_coach"
        assert strategist._agent_name == "design_strategist"
        assert evaluator._agent_name == "design_evaluator"

    def test_design_session_creation(self):
        """Test DesignSession can be created and initialized."""
        # Mock the database
        mock_db = MagicMock()
        user_data = UserData(db=mock_db)
        
        session = DesignSession(user_data)
        assert session.user_data == user_data
        
        # Test that session stores itself in user_data during init simulation
        session.user_data.design_session = session
        assert user_data.design_session == session

class TestAgentFunctionality:
    """Test core agent functionality by testing the business logic directly."""

    def test_user_data_with_database(self):
        """Test UserData works with a mocked database."""
        mock_db = MagicMock()
        mock_db.get_or_create_user.return_value = ("test_user_id", False)
        mock_db.save_user_data.return_value = "test_session_id"
        
        user_data = UserData(db=mock_db)
        
        # Test user identification
        user_data.first_name = TEST_USER['first_name']
        user_data.last_name = TEST_USER['last_name']
        user_data.user_id = "test_user_id"
        
        assert user_data.is_identified()
        
        # Test design challenge capture
        user_data.design_challenge = TEST_DESIGN_CHALLENGE['design_challenge']
        user_data.target_users = TEST_DESIGN_CHALLENGE['target_users']
        user_data.emotional_goals = TEST_DESIGN_CHALLENGE['emotional_goals']
        
        # Test save state
        session_id = user_data.save_state()
        assert session_id == "test_session_id"
        mock_db.save_user_data.assert_called_once_with(user_data)

    def test_agent_workflow_delegation(self):
        """Test that agents can delegate to DesignSession for workflow management."""
        # Create mock components
        mock_db = MagicMock()
        user_data = UserData(db=mock_db)
        
        # Create DesignSession
        session = DesignSession(user_data)
        user_data.design_session = session
        
        # Create agent
        agent = DesignCoachAgent()
        
        # Test that agent can get the design session
        # We'll mock the user_data property to return our test data
        def mock_user_data_property():
            return user_data
        
        # Temporarily replace the property
        original_user_data = type(agent).user_data
        type(agent).user_data = property(lambda self: user_data)
        
        try:
            design_session = agent.get_design_session()
            assert design_session == session
        finally:
            # Restore original property
            type(agent).user_data = original_user_data

class TestWorkflowIntegration:
    """Test the complete workflow integration."""

    def test_design_session_workflow(self):
        """Test the DesignSession manages workflow correctly."""
        # Create mock database
        mock_db = MagicMock()
        user_data = UserData(db=mock_db)
        
        # Create session
        session = DesignSession(user_data)
        
        # Test agent flow determination
        next_agent, context = session.determine_next_agent("DesignCoachAgent")
        assert next_agent == "DesignStrategistAgent"
        
        next_agent, context = session.determine_next_agent("DesignStrategistAgent")
        assert next_agent == "DesignEvaluatorAgent"
        
        # Test end of flow
        next_agent, context = session.determine_next_agent("DesignEvaluatorAgent")
        assert next_agent == "DesignEvaluatorAgent"  # Stays on same agent

    def test_import_compatibility(self):
        """Test that imports work from the old monolithic structure."""
        # Test backwards compatibility imports
        from design_assistant import UserData as LegacyUserData
        from design_assistant import DesignCoachAgent as LegacyCoachAgent
        
        # Should be the same classes
        assert LegacyUserData == UserData
        assert LegacyCoachAgent == DesignCoachAgent

if __name__ == "__main__":
    # Run with: python -m pytest test_design_workflow_simple.py -v
    pytest.main([__file__, "-v"]) 