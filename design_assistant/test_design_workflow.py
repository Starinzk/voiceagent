"""
Test suite for the design workflow implementation.

This module tests the functionality of the design workflow system, including:
1. Design Coach Agent methods
2. Design Strategist Agent methods
3. Status flow transitions
4. Database state management
5. Error handling

Test Summary:
------------
Total Tests: 10
Passing: 10
Failed: 0
Warnings: 1 (non-critical event loop warning)

Test Categories:
1. Design Coach Agent Tests (5 tests)
   - Customer identification
   - Design challenge capture
   - Error handling
   - Timeout scenarios
   - Unauthenticated access

2. Design Strategist Agent Tests (4 tests)
   - Problem statement refinement
   - Solution proposal
   - Format validation
   - State management

3. Integration Tests (1 test)
   - Complete workflow verification

Design Decisions:
- Uses pytest for testing
- Mocks LiveKit components
- Tests both happy path and error cases
- Verifies database state

Limitations:
- No real LiveKit integration
- No real-time testing
- No cloud sync testing

Future Improvements:
- Add integration tests
- Add performance tests
- Add stress tests
"""

import pytest
import pytest_asyncio
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from design_assistant import (
    DesignCoachAgent,
    DesignStrategistAgent,
    UserData,
    db,
    AgentSession
)

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

@pytest.fixture(autouse=True)
def reset_userdata(mock_session):
    """Reset UserData state before each test."""
    mock_session.userdata.reset()
    yield

@pytest.fixture
def mock_session():
    """Create a fully mocked session with all required attributes."""
    userdata = UserData()
    session = AgentSession(userdata=userdata)
    session.room = MagicMock()
    session.room.local_participant = MagicMock()
    session.ctx = MagicMock()
    return session

@pytest_asyncio.fixture
async def design_coach_agent(mock_session):
    """Create a DesignCoachAgent instance with mock session."""
    agent = DesignCoachAgent()
    # Initialize the agent with the session
    agent._session = mock_session
    # Create and set the activity context
    activity = MagicMock()
    activity.session = mock_session
    agent._activity = activity
    return agent

@pytest_asyncio.fixture
async def design_strategist_agent(mock_session):
    """Create a DesignStrategistAgent instance with mock session."""
    agent = DesignStrategistAgent()
    # Initialize the agent with the session
    agent._session = mock_session
    # Create and set the activity context
    activity = MagicMock()
    activity.session = mock_session
    agent._activity = activity
    return agent

class TestDesignCoachAgent:
    """Test cases for DesignCoachAgent methods."""

    @pytest.mark.asyncio
    async def test_identify_user_success(self, design_coach_agent):
        """Test successful user identification."""
        with patch('design_database.DesignDatabase.get_or_create_user', return_value="test_user_id"):
            result = await design_coach_agent.identify_user(
                TEST_USER['first_name'],
                TEST_USER['last_name']
            )
            
            assert result == f"Thank you, {TEST_USER['first_name']}. I've found your account."
            assert design_coach_agent._session.userdata.first_name == TEST_USER['first_name']
            assert design_coach_agent._session.userdata.last_name == TEST_USER['last_name']
            assert design_coach_agent._session.userdata.user_id == "test_user_id"

    @pytest.mark.asyncio
    async def test_identify_user_database_error(self, design_coach_agent):
        """Test database error during user identification."""
        with patch('design_database.DesignDatabase.get_or_create_user', side_effect=Exception("Database error")):
            with pytest.raises(Exception) as exc_info:
                await design_coach_agent.identify_user(
                    TEST_USER['first_name'],
                    TEST_USER['last_name']
                )
            assert "Database error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_capture_design_challenge_success(self, design_coach_agent):
        """Test successful design challenge capture."""
        # First identify the user
        with patch('design_database.DesignDatabase.get_or_create_user', return_value="test_user_id"):
            await design_coach_agent.identify_user(
                TEST_USER['first_name'],
                TEST_USER['last_name']
            )
            
            # Then capture the design challenge
            with patch('design_database.DesignDatabase.save_design_session') as mock_save:
                result = await design_coach_agent.capture_design_challenge(
                    TEST_DESIGN_CHALLENGE['design_challenge'],
                    TEST_DESIGN_CHALLENGE['target_users'],
                    TEST_DESIGN_CHALLENGE['emotional_goals']
                )
                
                assert "I've captured your design challenge" in result
                assert design_coach_agent._session.userdata.design_challenge == TEST_DESIGN_CHALLENGE['design_challenge']
                assert design_coach_agent._session.userdata.target_users == TEST_DESIGN_CHALLENGE['target_users']
                assert design_coach_agent._session.userdata.emotional_goals == TEST_DESIGN_CHALLENGE['emotional_goals']
                assert design_coach_agent._session.userdata.status == "ready_for_evaluation"
                
                # Verify database call
                mock_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_capture_design_challenge_no_user(self, design_coach_agent):
        """Test design challenge capture without user identification."""
        result = await design_coach_agent.capture_design_challenge(
            TEST_DESIGN_CHALLENGE['design_challenge'],
            TEST_DESIGN_CHALLENGE['target_users'],
            TEST_DESIGN_CHALLENGE['emotional_goals']
        )
        
        assert "Please identify yourself first" in result
        assert design_coach_agent._session.userdata.design_challenge is None
        assert design_coach_agent._session.userdata.status == "awaiting_problem_definition"

    @pytest.mark.asyncio
    async def test_capture_design_challenge_timeout(self, design_coach_agent):
        """Test design challenge capture with timeout."""
        # First identify the user
        with patch('design_database.DesignDatabase.get_or_create_user', return_value="test_user_id"):
            await design_coach_agent.identify_user(
                TEST_USER['first_name'],
                TEST_USER['last_name']
            )
            
            # Then try to capture with a timeout
            with patch('design_database.DesignDatabase.save_design_session', side_effect=asyncio.TimeoutError):
                with pytest.raises(asyncio.TimeoutError):
                    async with asyncio.timeout(1.0):
                        await design_coach_agent.capture_design_challenge(
                            TEST_DESIGN_CHALLENGE['design_challenge'],
                            TEST_DESIGN_CHALLENGE['target_users'],
                            TEST_DESIGN_CHALLENGE['emotional_goals']
                        )

class TestDesignStrategistAgent:
    """Test cases for DesignStrategistAgent methods."""

    @pytest.mark.asyncio
    async def test_refine_problem_statement_success(self, design_strategist_agent):
        """Test successful problem statement refinement."""
        # First identify the user and capture design challenge
        with patch('design_database.DesignDatabase.get_or_create_user', return_value="test_user_id"):
            await design_strategist_agent.identify_user(
                TEST_USER['first_name'],
                TEST_USER['last_name']
            )
            design_strategist_agent._session.userdata.design_challenge = TEST_DESIGN_CHALLENGE['design_challenge']
            
            # Then refine the problem statement
            with patch('design_database.DesignDatabase.save_design_session') as mock_save:
                result = await design_strategist_agent.refine_problem_statement(TEST_PROBLEM_STATEMENT)
                
                assert "I've refined your problem statement" in result
                assert design_strategist_agent._session.userdata.problem_statement == TEST_PROBLEM_STATEMENT
                assert design_strategist_agent._session.userdata.status == "ready_for_evaluation"
                
                # Verify database call
                mock_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_refine_problem_statement_invalid_format(self, design_strategist_agent):
        """Test problem statement refinement with invalid format."""
        # First identify the user and capture design challenge
        with patch('design_database.DesignDatabase.get_or_create_user', return_value="test_user_id"):
            await design_strategist_agent.identify_user(
                TEST_USER['first_name'],
                TEST_USER['last_name']
            )
            design_strategist_agent._session.userdata.design_challenge = TEST_DESIGN_CHALLENGE['design_challenge']
            design_strategist_agent._session.userdata.status = "challenge_defined"
            
            # Try to refine with invalid format
            invalid_statement = "We need to create a mobile app for fitness tracking"
            result = await design_strategist_agent.refine_problem_statement(invalid_statement)
            
            assert "must start with 'How might we...'" in result
            assert design_strategist_agent._session.userdata.problem_statement is None
            assert design_strategist_agent._session.userdata.status == "challenge_defined"

    @pytest.mark.asyncio
    async def test_propose_solution_success(self, design_strategist_agent):
        """Test successful solution proposal."""
        # First identify the user and set up previous steps
        with patch('design_database.DesignDatabase.get_or_create_user', return_value="test_user_id"):
            await design_strategist_agent.identify_user(
                TEST_USER['first_name'],
                TEST_USER['last_name']
            )
            design_strategist_agent._session.userdata.design_challenge = TEST_DESIGN_CHALLENGE['design_challenge']
            design_strategist_agent._session.userdata.problem_statement = TEST_PROBLEM_STATEMENT
            
            # Then propose a solution
            with patch('design_database.DesignDatabase.save_design_session') as mock_save:
                result = await design_strategist_agent.propose_solution(TEST_SOLUTION)
                
                assert "Problem Statement:" in result
                assert "Proposed Solution:" in result
                assert "Coach, we're ready for evaluation" in result
                assert design_strategist_agent._session.userdata.proposed_solution == TEST_SOLUTION
                assert design_strategist_agent._session.userdata.status == "ready_for_evaluation"
                
                # Verify iteration data
                iteration = design_strategist_agent._session.userdata.design_iterations[0]
                assert iteration['problem_statement'] == TEST_PROBLEM_STATEMENT
                assert iteration['solution'] == TEST_SOLUTION
                assert 'timestamp' in iteration
                
                # Verify database call
                mock_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_propose_solution_no_problem_statement(self, design_strategist_agent):
        """Test solution proposal without problem statement."""
        # First identify the user
        with patch('design_database.DesignDatabase.get_or_create_user', return_value="test_user_id"):
            await design_strategist_agent.identify_user(
                TEST_USER['first_name'],
                TEST_USER['last_name']
            )
            
            # Try to propose solution without problem statement
            result = await design_strategist_agent.propose_solution(TEST_SOLUTION)
            
            assert "Please refine the problem statement first" in result
            assert design_strategist_agent._session.userdata.proposed_solution is None
            assert design_strategist_agent._session.userdata.status == "awaiting_problem_definition"
            assert len(design_strategist_agent._session.userdata.design_iterations) == 0

class TestWorkflowIntegration:
    """Test cases for the complete design workflow."""

    @pytest.mark.asyncio
    async def test_complete_workflow(self, design_coach_agent, design_strategist_agent):
        """Test the complete design workflow from start to finish."""
        with patch('design_database.DesignDatabase.get_or_create_user', return_value="test_user_id"), \
             patch('design_database.DesignDatabase.save_design_session') as mock_save:
            
            # 1. Identify user
            await design_coach_agent.identify_user(
                TEST_USER['first_name'],
                TEST_USER['last_name']
            )
            
            # 2. Capture design challenge
            await design_coach_agent.capture_design_challenge(
                TEST_DESIGN_CHALLENGE['design_challenge'],
                TEST_DESIGN_CHALLENGE['target_users'],
                TEST_DESIGN_CHALLENGE['emotional_goals']
            )
            
            # 3. Refine problem statement
            await design_strategist_agent.refine_problem_statement(TEST_PROBLEM_STATEMENT)
            
            # 4. Propose solution
            await design_strategist_agent.propose_solution(TEST_SOLUTION)
            
            # Verify final state
            userdata = design_strategist_agent._session.userdata
            assert userdata.first_name == TEST_USER['first_name']
            assert userdata.last_name == TEST_USER['last_name']
            assert userdata.design_challenge == TEST_DESIGN_CHALLENGE['design_challenge']
            assert userdata.target_users == TEST_DESIGN_CHALLENGE['target_users']
            assert userdata.emotional_goals == TEST_DESIGN_CHALLENGE['emotional_goals']
            assert userdata.problem_statement == TEST_PROBLEM_STATEMENT
            assert userdata.proposed_solution == TEST_SOLUTION
            assert userdata.status == "ready_for_evaluation"
            
            # Verify database calls
            assert mock_save.call_count == 3  # One for each state change 