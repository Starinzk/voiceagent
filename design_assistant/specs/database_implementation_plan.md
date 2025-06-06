# Database Implementation Plan

## Overview
This document outlines the current state of the Design Assistant application's state management and proposes a plan for adding Supabase persistence.

## Current State Analysis

### UserData Class Structure
The `UserData` class is the central state management system for the design assistant application. It currently:

1. **Manages Agent State**
   ```python
   personas: dict[str, Agent] = field(default_factory=dict)  # All agent instances
   prev_agent: Optional[Agent] = None  # Previous agent for context
   ctx: Optional[JobContext] = None  # LiveKit context
   ```

2. **Handles User Identification**
   ```python
   first_name: Optional[str] = None
   last_name: Optional[str] = None
   user_id: Optional[str] = None  # Currently first_name_last_name
   ```

3. **Stores Design Session Data**
   ```python
   design_challenge: Optional[str] = None
   target_users: Optional[list[str]] = None
   emotional_goals: Optional[list[str]] = None
   problem_statement: Optional[str] = None
   proposed_solution: Optional[str] = None
   ```

4. **Tracks Session State**
   ```python
   status: str = "awaiting_problem_definition"  # Workflow state
   ```

5. **Maintains Design History**
   ```python
   design_iterations: list[dict] = field(default_factory=list)  # Design changes
   feedback_history: list[dict] = field(default_factory=list)  # Feedback records
   ```

### Current Workflow
1. **User Identification**
   - User provides first and last name
   - Creates temporary user_id as first_name_last_name
   - No persistence between sessions

2. **Design Process**
   - Design Coach captures initial challenge and goals
   - Design Strategist refines problem and proposes solutions
   - Design Evaluator provides feedback
   - All state changes tracked in memory

3. **Agent Transitions**
   - State preserved during agent transitions
   - Previous agent context maintained
   - No persistence between sessions

### Current Limitations
1. **State Management**
   - All state is in-memory only
   - No persistence between sessions
   - State lost on application restart

2. **User Management**
   - Simple name-based identification
   - No authentication
   - No user accounts

3. **Data Storage**
   - No history preservation
   - No backup mechanism
   - No data recovery

4. **Collaboration**
   - No real-time updates
   - No multi-user support
   - No session sharing

## Implementation Plan

### Phase 1: Database Setup
1. Create Supabase Project
   - Set up new project
   - Configure environment
   - Set up RLS policies

2. Schema Implementation
   ```sql
   -- Core tables mirroring UserData structure
   CREATE TABLE users (
       id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
       first_name TEXT NOT NULL,
       last_name TEXT NOT NULL,
       created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
   );

   CREATE TABLE design_sessions (
       id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
       user_id UUID REFERENCES users(id),
       design_challenge TEXT,
       target_users TEXT[],
       emotional_goals TEXT[],
       problem_statement TEXT,
       proposed_solution TEXT,
       status TEXT NOT NULL,
       created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
       updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
   );

   CREATE TABLE design_iterations (
       id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
       session_id UUID REFERENCES design_sessions(id),
       problem_statement TEXT NOT NULL,
       solution TEXT NOT NULL,
       created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
   );

   CREATE TABLE feedback_history (
       id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
       session_id UUID REFERENCES design_sessions(id),
       feedback_data JSONB NOT NULL,
       created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
   );
   
   -- Indexes
   CREATE INDEX idx_users_name ON users(first_name, last_name);
   CREATE INDEX idx_sessions_user ON design_sessions(user_id);
   CREATE INDEX idx_sessions_status ON design_sessions(status);
   ```

### Phase 2: Database Class Implementation

1. Core Database Class
   ```python
   class DesignDatabase:
       def __init__(self):
           # Initialize Supabase client
           # Configure logging
   
       # User Data Persistence
       def save_user_data(self, user_data: UserData) -> str:
           """Save the current state of UserData to Supabase"""
   
       def load_user_data(self, session_id: str) -> UserData:
           """Load UserData state from Supabase"""
   
       def get_user_sessions(self, user_id: str) -> List[Dict]:
           """Get all sessions for a user"""
   
       # Session Management
       def create_session(self, user_id: str) -> str:
           """Create a new design session"""
   
       def update_session(self, session_id: str, user_data: UserData):
           """Update session with current UserData state"""
   
       def get_session(self, session_id: str) -> Dict:
           """Get session details"""
   ```

### Phase 3: Testing Implementation

1. Unit Tests
   ```python
   class TestDesignDatabase:
       def setup_method(self):
           # Set up test database
           # Create test tables
           # Initialize test data
   
       def test_user_data_persistence(self):
           # Test saving UserData state
           # Test loading UserData state
           # Test state consistency
   
       def test_session_management(self):
           # Test session creation
           # Test session updates
           # Test session retrieval
   
       def test_data_integrity(self):
           # Test data consistency
           # Test relationship integrity
           # Test state recovery
   ```

2. Integration Tests
   ```python
   class TestDesignWorkflow:
       def test_persistence_workflow(self):
           # Test save/load cycle
           # Test state recovery
           # Test session continuity
   
       def test_error_handling(self):
           # Test connection failures
           # Test invalid data
           # Test recovery mechanisms
   ```

## Success Criteria

1. Functionality
   - In-memory state management works as before
   - Data can be persisted to Supabase
   - State can be recovered from Supabase
   - Error handling works as expected

2. Performance
   - Response time < 200ms for persistence operations
   - No impact on existing in-memory operations
   - Efficient resource usage

3. Security
   - Proper access control
   - Data validation
   - Secure connections 