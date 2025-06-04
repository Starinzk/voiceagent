import pytest
from unittest.mock import Mock, AsyncMock
from design_assistant.design_assistant import (
    DesignCoachAgent,
    DesignStrategistAgent,
    DesignEvaluatorAgent,
    UserData
)

class MockSession:
    def __init__(self, userdata):
        self.userdata = userdata
        self.current_agent = None
        self.say = AsyncMock()
    def generate_reply(self):
        pass

class MockActivity:
    def __init__(self):
        self.update_chat_ctx = AsyncMock()
        # self.session will be set externally in the fixture

@pytest.fixture
def mock_session():
    userdata = UserData()
    session = MockSession(userdata)
    return session

@pytest.fixture
def mock_activity(mock_session):
    activity = MockActivity()
    activity.session = mock_session
    return activity

@pytest.mark.asyncio
async def test_design_coach_prompt(mock_session, mock_activity):
    """Test Design Coach's initial interaction and transition to Strategist."""
    coach = DesignCoachAgent()
    coach._activity = mock_activity
    
    # Test initial greeting and intent clarification
    response = await coach.on_enter()
    assert "design challenge" in response.lower() or "designing for" in response.lower()
    
    # Test transition to Strategist
    response = await coach.transfer_to_strategist(mock_activity)
    assert "strategist" in response.lower()
    assert mock_session.userdata.status == "awaiting_problem_definition"

@pytest.mark.asyncio
async def test_design_strategist_prompt(mock_session, mock_activity):
    """Test Design Strategist's problem definition and solution development."""
    strategist = DesignStrategistAgent()
    strategist._activity = mock_activity
    
    # Test problem definition process
    response = await strategist.on_enter()
    assert "problem scope" in response.lower() or "stakeholders" in response.lower()
    
    # Test solution development
    response = await strategist.develop_solution("Test solution")
    assert "proposed solution" in response.lower()
    assert mock_session.userdata.status == "ready_for_evaluation"

@pytest.mark.asyncio
async def test_design_evaluator_prompt(mock_session, mock_activity):
    """Test Design Evaluator's feedback and scoring."""
    evaluator = DesignEvaluatorAgent()
    evaluator._activity = mock_activity
    
    # Test evaluation process
    response = await evaluator.on_enter()
    assert "evaluation results" in response.lower()
    assert "score" in response.lower()
    assert "strengths" in response.lower()
    assert "improvements" in response.lower()
    assert mock_session.userdata.status == "evaluation_complete"

@pytest.mark.asyncio
async def test_workflow_transitions(mock_session, mock_activity):
    """Test the complete workflow transitions between agents."""
    coach = DesignCoachAgent()
    strategist = DesignStrategistAgent()
    evaluator = DesignEvaluatorAgent()
    
    # Set up shared userdata and activity
    coach._activity = mock_activity
    strategist._activity = mock_activity
    evaluator._activity = mock_activity
    
    # Test Coach to Strategist transition
    await coach.on_enter()
    assert mock_session.userdata.status == "awaiting_problem_definition"
    
    # Test Strategist to Evaluator transition
    await strategist.on_enter()
    assert mock_session.userdata.status == "ready_for_evaluation"
    
    # Test final evaluation
    await evaluator.on_enter()
    assert mock_session.userdata.status == "evaluation_complete"

@pytest.mark.asyncio
async def test_userdata_persistence(mock_session, mock_activity):
    """Test that user data persists through agent transitions."""
    # Simulate a design challenge
    mock_session.userdata.design_challenge = "Improve user onboarding experience"
    mock_session.userdata.target_users = "New mobile app users"
    mock_session.userdata.emotional_goals = "Reduce user anxiety and increase confidence"
    
    # Test data persistence through transitions
    coach = DesignCoachAgent()
    coach._activity = mock_activity
    await coach.on_enter()
    assert mock_session.userdata.design_challenge == "Improve user onboarding experience"
    
    strategist = DesignStrategistAgent()
    strategist._activity = mock_activity
    await strategist.on_enter()
    assert mock_session.userdata.target_users == "New mobile app users"
    
    evaluator = DesignEvaluatorAgent()
    evaluator._activity = mock_activity
    await evaluator.on_enter()
    assert mock_session.userdata.emotional_goals == "Reduce user anxiety and increase confidence" 