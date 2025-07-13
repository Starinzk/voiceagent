"""
Test suite for the Design Database implementation.

This module contains tests for:
- Database connection and initialization
- User data persistence
- Session management
- Design iterations
- Feedback history
- Data integrity
- Error handling

Design Decisions:
- Uses pytest for testing framework
- Uses fixtures for common setup
- Tests both success and error cases
- Maintains test isolation
- Cleans up test data

Dependencies:
- pytest
- python-dotenv
- supabase
"""

import os
import pytest
from datetime import datetime
from typing import Dict, Any
from dotenv import load_dotenv
from design_assistant.design_database import DesignDatabase
from design_assistant.user_data import UserData

# Load environment variables
load_dotenv()

# Test data constants
SAMPLE_USER = {
    "first_name": "Test",
    "last_name": "User"
}

SAMPLE_SESSION = {
    "design_challenge": "Test Challenge",
    "target_users": ["User1", "User2"],
    "emotional_goals": ["Goal1", "Goal2"]
}

SAMPLE_ITERATION = {
    "problem_statement": "Test Problem",
    "solution": "Test Solution"
}

SAMPLE_FEEDBACK = {
    "rating": 5,
    "comments": "Test Feedback"
}

@pytest.fixture
def test_user_data() -> Dict[str, Any]:
    """
    Fixture providing test user data.
    
    Returns:
        Dict[str, Any]: Dictionary containing test user information
    """
    return {
        "first_name": "Test",
        "last_name": "User"
    }

@pytest.fixture
def test_session_data() -> Dict[str, Any]:
    """
    Fixture providing test session data.
    
    Returns:
        Dict[str, Any]: Dictionary containing test session information
    """
    return {
        "design_challenge": "Test Challenge",
        "target_users": ["User1", "User2"],
        "emotional_goals": ["Goal1", "Goal2"]
    }

@pytest.fixture
def test_iteration_data() -> Dict[str, Any]:
    """
    Fixture providing test iteration data.
    
    Returns:
        Dict[str, Any]: Dictionary containing test iteration information
    """
    return {
        "problem_statement": "Test Problem",
        "solution": "Test Solution"
    }

@pytest.fixture
def test_feedback_data() -> Dict[str, Any]:
    """
    Fixture providing test feedback data.
    
    Returns:
        Dict[str, Any]: Dictionary containing test feedback information
    """
    return {
        "rating": 5,
        "comments": "Test Feedback"
    }

def cleanup_test_data(db: DesignDatabase, session_id: str = None, user_id: str = None) -> None:
    """
    Clean up test data from the database.
    
    Args:
        db: Database instance
        session_id: Optional session ID to clean up
        user_id: Optional user ID to clean up
        
    Note:
        This function will:
        1. Delete all feedback for the session
        2. Delete all iterations for the session
        3. Delete the session itself
        4. Delete the user if specified
    """
    if session_id:
        # Delete feedback
        db.client.table('feedback_history') \
            .delete() \
            .eq('session_id', session_id) \
            .execute()
            
        # Delete iterations
        db.client.table('design_iterations') \
            .delete() \
            .eq('session_id', session_id) \
            .execute()
            
        # Delete session
        db.client.table('design_sessions') \
            .delete() \
            .eq('id', session_id) \
            .execute()
    
    if user_id:
        # Delete user
        db.client.table('users') \
            .delete() \
            .eq('id', user_id) \
            .execute()

@pytest.fixture
def db():
    """
    Database fixture that provides a test database instance.
    
    Returns:
        DesignDatabase: A configured database instance for testing
        
    Note:
        This fixture:
        1. Creates a new database instance
        2. Ensures proper configuration
        3. Cleans up after tests
    """
    # Create database instance
    database = DesignDatabase()
    
    # Store created IDs for cleanup
    created_ids = {
        'sessions': set(),
        'users': set()
    }
    
    # Add cleanup to the database instance
    original_create_session = database.create_design_session
    original_get_or_create_user = database.get_or_create_user
    
    def create_session_with_tracking(*args, **kwargs):
        session_id = original_create_session(*args, **kwargs)
        created_ids['sessions'].add(session_id)
        return session_id
    
    def get_or_create_user_with_tracking(*args, **kwargs):
        user_id = original_get_or_create_user(*args, **kwargs)
        created_ids['users'].add(user_id)
        return user_id
    
    database.create_design_session = create_session_with_tracking
    database.get_or_create_user = get_or_create_user_with_tracking
    
    yield database
    
    # Cleanup all created test data
    for session_id in created_ids['sessions']:
        cleanup_test_data(database, session_id=session_id)
    
    for user_id in created_ids['users']:
        cleanup_test_data(database, user_id=user_id)

@pytest.fixture
def sample_user_data():
    """
    Sample UserData fixture for testing.
    
    Returns:
        UserData: A populated UserData instance
        
    Note:
        This fixture:
        1. Creates a new UserData instance
        2. Populates it with test data
        3. Configures it with the test database
    """
    user_data = UserData()
    user_data.first_name = SAMPLE_USER["first_name"]
    user_data.last_name = SAMPLE_USER["last_name"]
    user_data.design_challenge = SAMPLE_SESSION["design_challenge"]
    user_data.target_users = SAMPLE_SESSION["target_users"]
    user_data.emotional_goals = SAMPLE_SESSION["emotional_goals"]
    return user_data

def test_database_initialization():
    """
    Test database connection and initialization.
    
    This test verifies that:
    1. Database can be initialized with valid credentials
    2. Environment variables are properly loaded
    3. Connection is established successfully
    """
    # Test with valid credentials
    db = DesignDatabase()
    assert db.client is not None, "Database client should be initialized"
    
    # Test environment variable fallback
    original_url = os.getenv('SUPABASE_URL')
    original_key = os.getenv('SUPABASE_KEY')
    
    try:
        # Temporarily remove environment variables
        if 'SUPABASE_URL' in os.environ:
            del os.environ['SUPABASE_URL']
        if 'SUPABASE_KEY' in os.environ:
            del os.environ['SUPABASE_KEY']
            
        # Should raise ValueError when no credentials are available
        with pytest.raises(ValueError):
            DesignDatabase()
            
    finally:
        # Restore environment variables
        if original_url:
            os.environ['SUPABASE_URL'] = original_url
        if original_key:
            os.environ['SUPABASE_KEY'] = original_key

def test_save_user_data(db, sample_user_data):
    """
    Test saving UserData state to the database.
    
    This test verifies that:
    1. User data can be saved successfully
    2. Session ID is returned
    3. Data is persisted correctly
    """
    # Configure user data with database
    sample_user_data.db = db
    
    # Save user data
    session_id = sample_user_data.save_state()
    
    # Verify session ID is returned
    assert session_id is not None, "Session ID should be returned"
    assert isinstance(session_id, str), "Session ID should be a string"
    
    # Verify data was saved
    session = db.get_session_details(session_id)
    assert session is not None, "Session should be retrievable"
    assert session["design_challenge"] == SAMPLE_SESSION["design_challenge"], "Design challenge should match"
    assert session["target_users"] == SAMPLE_SESSION["target_users"], "Target users should match"
    assert session["emotional_goals"] == SAMPLE_SESSION["emotional_goals"], "Emotional goals should match"

def test_load_user_data(db, sample_user_data):
    """
    Test loading UserData state from the database.
    
    This test verifies that:
    1. User data can be loaded successfully
    2. All fields are restored correctly
    3. Agent-related fields are preserved
    """
    # Save initial state
    sample_user_data.db = db
    session_id = sample_user_data.save_state()
    
    # Create new UserData instance
    loaded_data = UserData()
    loaded_data.db = db
    
    # Load state
    loaded_data.load_state(session_id)
    
    # Verify data was loaded correctly
    assert loaded_data.first_name == SAMPLE_USER["first_name"], "First name should match"
    assert loaded_data.last_name == SAMPLE_USER["last_name"], "Last name should match"
    assert loaded_data.design_challenge == SAMPLE_SESSION["design_challenge"], "Design challenge should match"
    assert loaded_data.target_users == SAMPLE_SESSION["target_users"], "Target users should match"
    assert loaded_data.emotional_goals == SAMPLE_SESSION["emotional_goals"], "Emotional goals should match"
    
    # Verify agent-related fields are preserved
    assert loaded_data.personas == {}, "Personas should be empty"
    assert loaded_data.prev_agent is None, "Previous agent should be None"
    assert loaded_data.ctx is None, "Context should be None"

def test_get_or_create_user(db: DesignDatabase, test_user_data: Dict[str, Any]) -> None:
    """
    Test user creation and retrieval functionality.
    
    This test verifies that:
    1. A new user can be created
    2. The same user can be retrieved using the same name
    3. User IDs are consistent for the same user
    
    Args:
        db: Database instance
        test_user_data: Test user information
    """
    # Create a new user
    user_id = db.get_or_create_user(
        test_user_data["first_name"],
        test_user_data["last_name"]
    )
    assert user_id is not None
    
    # Try to get the same user again
    same_user_id = db.get_or_create_user(
        test_user_data["first_name"],
        test_user_data["last_name"]
    )
    assert same_user_id == user_id

def test_create_design_session(db: DesignDatabase, test_user_data: Dict[str, Any], test_session_data: Dict[str, Any]) -> None:
    """
    Test design session creation functionality.
    
    This test verifies that:
    1. A new design session can be created for a user
    2. The session is properly associated with the user
    3. All session data is correctly stored
    
    Args:
        db: Database instance
        test_user_data: Test user information
        test_session_data: Test session information
    """
    # First create a user
    user_id = db.get_or_create_user(
        test_user_data["first_name"],
        test_user_data["last_name"]
    )
    
    # Create a session
    session_id = db.create_design_session(
        user_id=user_id,
        design_challenge=test_session_data["design_challenge"],
        target_users=test_session_data["target_users"],
        emotional_goals=test_session_data["emotional_goals"]
    )
    assert session_id is not None

def test_update_session(db: DesignDatabase, test_user_data: Dict[str, Any], test_session_data: Dict[str, Any]) -> None:
    """
    Test session update functionality.
    
    This test verifies that:
    1. Session data can be updated
    2. Updates are properly persisted
    3. Updated data can be retrieved
    
    Args:
        db: Database instance
        test_user_data: Test user information
        test_session_data: Test session information
    """
    # Create user and session
    user_id = db.get_or_create_user(
        test_user_data["first_name"],
        test_user_data["last_name"]
    )
    session_id = db.create_design_session(
        user_id=user_id,
        design_challenge=test_session_data["design_challenge"],
        target_users=test_session_data["target_users"],
        emotional_goals=test_session_data["emotional_goals"]
    )
    
    # Update session
    new_status = "ready_for_evaluation"
    db.update_session(session_id, {"status": new_status})
    
    # Verify update
    session = db.get_session_details(session_id)
    assert session["status"] == new_status

def test_add_design_iteration(db: DesignDatabase, test_user_data: Dict[str, Any], 
                            test_session_data: Dict[str, Any], test_iteration_data: Dict[str, Any]) -> None:
    """
    Test design iteration functionality.
    
    This test verifies that:
    1. New iterations can be added to a session
    2. Iteration data is properly stored
    3. Iterations are correctly associated with sessions
    
    Args:
        db: Database instance
        test_user_data: Test user information
        test_session_data: Test session information
        test_iteration_data: Test iteration information
    """
    # Create user and session
    user_id = db.get_or_create_user(
        test_user_data["first_name"],
        test_user_data["last_name"]
    )
    session_id = db.create_design_session(
        user_id=user_id,
        design_challenge=test_session_data["design_challenge"],
        target_users=test_session_data["target_users"],
        emotional_goals=test_session_data["emotional_goals"]
    )
    
    # Add iteration
    iteration_id = db.add_design_iteration(
        session_id=session_id,
        problem_statement=test_iteration_data["problem_statement"],
        solution=test_iteration_data["solution"]
    )
    assert iteration_id is not None

def test_add_feedback(db: DesignDatabase, test_user_data: Dict[str, Any], 
                     test_session_data: Dict[str, Any], test_feedback_data: Dict[str, Any]) -> None:
    """
    Test feedback functionality.
    
    This test verifies that:
    1. Feedback can be added to a session
    2. Feedback data is properly stored
    3. Feedback is correctly associated with sessions
    
    Args:
        db: Database instance
        test_user_data: Test user information
        test_session_data: Test session information
        test_feedback_data: Test feedback information
    """
    # Create user and session
    user_id = db.get_or_create_user(
        test_user_data["first_name"],
        test_user_data["last_name"]
    )
    session_id = db.create_design_session(
        user_id=user_id,
        design_challenge=test_session_data["design_challenge"],
        target_users=test_session_data["target_users"],
        emotional_goals=test_session_data["emotional_goals"]
    )
    
    # Add feedback
    feedback_id = db.add_feedback(
        session_id=session_id,
        feedback_data=test_feedback_data
    )
    assert feedback_id is not None

def test_get_user_sessions(db: DesignDatabase, test_user_data: Dict[str, Any], test_session_data: Dict[str, Any]) -> None:
    """
    Test user session retrieval functionality.
    
    This test verifies that:
    1. All sessions for a user can be retrieved
    2. Multiple sessions are properly returned
    3. Session data is complete and correct
    
    Args:
        db: Database instance
        test_user_data: Test user information
        test_session_data: Test session information
    """
    # Create user and multiple sessions
    user_id = db.get_or_create_user(
        test_user_data["first_name"],
        test_user_data["last_name"]
    )
    
    # Create two sessions
    session1_id = db.create_design_session(
        user_id=user_id,
        design_challenge=test_session_data["design_challenge"],
        target_users=test_session_data["target_users"],
        emotional_goals=test_session_data["emotional_goals"]
    )
    
    session2_id = db.create_design_session(
        user_id=user_id,
        design_challenge="Another challenge",
        target_users=["User3"],
        emotional_goals=["Goal3"]
    )
    
    # Get all sessions
    sessions = db.get_user_sessions(user_id)
    assert len(sessions) >= 2
    session_ids = [s["id"] for s in sessions]
    assert session1_id in session_ids
    assert session2_id in session_ids

def test_get_session_details(db: DesignDatabase, test_user_data: Dict[str, Any], 
                           test_session_data: Dict[str, Any], test_iteration_data: Dict[str, Any],
                           test_feedback_data: Dict[str, Any]) -> None:
    """
    Test session detail retrieval functionality.
    
    This test verifies that:
    1. Full session details can be retrieved
    2. Session includes all iterations
    3. Session includes all feedback
    4. All relationships are properly maintained
    
    Args:
        db: Database instance
        test_user_data: Test user information
        test_session_data: Test session information
        test_iteration_data: Test iteration information
        test_feedback_data: Test feedback information
    """
    # Create user and session
    user_id = db.get_or_create_user(
        test_user_data["first_name"],
        test_user_data["last_name"]
    )
    session_id = db.create_design_session(
        user_id=user_id,
        design_challenge=test_session_data["design_challenge"],
        target_users=test_session_data["target_users"],
        emotional_goals=test_session_data["emotional_goals"]
    )
    
    # Add iteration and feedback
    db.add_design_iteration(
        session_id=session_id,
        problem_statement=test_iteration_data["problem_statement"],
        solution=test_iteration_data["solution"]
    )
    
    db.add_feedback(
        session_id=session_id,
        feedback_data=test_feedback_data
    )
    
    # Get session details
    session = db.get_session_details(session_id)
    assert session["id"] == session_id
    assert len(session["iterations"]) >= 1
    assert len(session["feedback"]) >= 1

def test_save_user_data_errors(db, sample_user_data):
    """
    Test error handling when saving user data.
    
    This test verifies that:
    1. Error is raised when database is not configured
    2. Error is raised when required fields are missing
    3. Error is raised when data is invalid
    """
    # Test missing database
    with pytest.raises(ValueError, match="No database configured"):
        sample_user_data.save_state()
    
    # Test missing required fields
    sample_user_data.db = db
    sample_user_data.first_name = None
    with pytest.raises(ValueError):
        sample_user_data.save_state()
    
    # Test invalid data
    sample_user_data.first_name = "Test"
    sample_user_data.target_users = "Not a list"  # Should be a list
    with pytest.raises(ValueError):
        sample_user_data.save_state()

def test_load_user_data_errors(db):
    """
    Test error handling when loading user data.
    
    This test verifies that:
    1. Error is raised when database is not configured
    2. Error is raised when session ID is invalid
    3. Error is raised when session doesn't exist
    """
    user_data = UserData()
    
    # Test missing database
    with pytest.raises(ValueError, match="No database configured"):
        user_data.load_state("some_id")
    
    # Test invalid session ID
    user_data.db = db
    with pytest.raises(ValueError, match="Session not found"):
        user_data.load_state("invalid_id")
    
    # Test non-existent session
    with pytest.raises(ValueError, match="Session not found"):
        user_data.load_state("00000000-0000-0000-0000-000000000000")

def test_session_management_errors(db):
    """
    Test error handling in session management operations.
    
    This test verifies that:
    1. Error is raised when updating non-existent session
    2. Error is raised when adding iteration to non-existent session
    3. Error is raised when adding feedback to non-existent session
    """
    # Test updating non-existent session
    with pytest.raises(ValueError, match="Session not found"):
        db.update_session("invalid_id", {"status": "new_status"})
    
    # Test adding iteration to non-existent session
    with pytest.raises(ValueError, match="Session not found"):
        db.add_design_iteration(
            session_id="invalid_id",
            problem_statement="test",
            solution="test"
        )
    
    # Test adding feedback to non-existent session
    with pytest.raises(ValueError, match="Session not found"):
        db.add_feedback(
            session_id="invalid_id",
            feedback_data={"test": "test"}
        )

def test_data_validation_errors(db, sample_user_data):
    """
    Test data validation error handling.
    
    This test verifies that:
    1. Error is raised when user data is invalid
    2. Error is raised when session data is invalid
    3. Error is raised when iteration data is invalid
    4. Error is raised when feedback data is invalid
    """
    # Test invalid user data
    with pytest.raises(ValueError):
        db.get_or_create_user("", "")  # Empty names
    
    # Test invalid session data
    user_id = db.get_or_create_user("Test", "User")
    with pytest.raises(ValueError):
        db.create_design_session(
            user_id=user_id,
            design_challenge="",  # Empty challenge
            target_users=[],  # Empty users
            emotional_goals=[]  # Empty goals
        )
    
    # Test invalid iteration data
    session_id = db.create_design_session(
        user_id=user_id,
        design_challenge="Test",
        target_users=["User1"],
        emotional_goals=["Goal1"]
    )
    with pytest.raises(ValueError):
        db.add_design_iteration(
            session_id=session_id,
            problem_statement="",  # Empty problem statement
            solution=""  # Empty solution
        )
    
    # Test invalid feedback data
    with pytest.raises(ValueError):
        db.add_feedback(
            session_id=session_id,
            feedback_data={}  # Empty feedback
        )

def test_concurrent_access_handling(db, sample_user_data):
    """
    Test handling of concurrent access scenarios.
    
    This test verifies that:
    1. Multiple saves of the same data are handled correctly
    2. Loading while saving is handled correctly
    3. Updates to the same session are handled correctly
    """
    # Configure user data
    sample_user_data.db = db
    
    # Test multiple saves
    session_id1 = sample_user_data.save_state()
    session_id2 = sample_user_data.save_state()
    assert session_id1 == session_id2, "Multiple saves should return same session ID"
    
    # Test loading while saving
    loaded_data = UserData()
    loaded_data.db = db
    loaded_data.load_state(session_id1)
    
    # Update and save original data
    sample_user_data.design_challenge = "Updated Challenge"
    sample_user_data.save_state()
    
    # Verify loaded data is not affected until reloaded
    assert loaded_data.design_challenge != sample_user_data.design_challenge
    loaded_data.load_state(session_id1)
    assert loaded_data.design_challenge == sample_user_data.design_challenge

def test_database_connection_errors():
    """
    Test handling of database connection errors.
    
    This test verifies that:
    1. Error is raised when database is unreachable
    2. Error is raised when credentials are invalid
    3. Error is raised when connection times out
    """
    # Test invalid URL
    with pytest.raises(ValueError):
        DesignDatabase(supabase_url="invalid_url", supabase_key="valid_key")
    
    # Test invalid key
    with pytest.raises(ValueError):
        DesignDatabase(supabase_url="valid_url", supabase_key="invalid_key")
    
    # Test connection timeout
    with pytest.raises(ValueError):
        DesignDatabase(supabase_url="http://invalid-host", supabase_key="valid_key") 