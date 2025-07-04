# Design Workflow Data Model and Prompts Specification

## Overview
This specification outlines the data model and prompts for the design workflow system, which consists of three agents: Design Coach, Design Strategist, and Design Evaluator. Each agent has specific roles and responsibilities in the design process.

## Constraints and No-Gos

### Out of Scope
1. **Supabase Integration**
   - No connection to Supabase backend
   - Continue using local SQLite database for now
   - Supabase integration will be a separate feature branch

2. **Authentication**
   - No user authentication system
   - Continue with simple user identification via name
   - Authentication will be handled in a future feature

3. **Persistent Storage**
   - No cloud storage for design assets
   - No file upload/download capabilities
   - Focus on text-based design challenges and solutions

4. **Real-time Collaboration**
   - No multi-user collaboration features
   - No real-time updates between sessions
   - Single user workflow only

5. **Analytics and Reporting**
   - No analytics dashboard
   - No usage statistics
   - No performance metrics

### Technical Constraints
1. **Database**
   - Use existing SQLite database structure
   - No schema migrations
   - No data migration tools

2. **API Integration**
   - No external API calls
   - No third-party service integration
   - Keep all processing local

3. **UI/UX**
   - No UI changes to the frontend
   - No new UI components
   - Focus on backend workflow only

## Code Documentation Standards

### Class-Level Documentation
```python
"""
Class-level docstrings should include:
1. Purpose of the class
2. Key design decisions
3. Out-of-scope features
4. Future considerations

Example:
class DesignDatabase:
    '''
    Local SQLite database for design session data.
    
    Design Decisions:
    - Using SQLite for local storage (see constraints)
    - No cloud sync (future feature)
    - Simple user identification via name
    
    Out of Scope:
    - Supabase integration (future feature)
    - User authentication
    - Cloud storage
    
    Future Considerations:
    - Migration to Supabase
    - User authentication system
    - Cloud storage integration
    '''
"""
```

### Method-Level Documentation
```python
"""
Method docstrings should include:
1. Purpose of the method
2. Design decisions
3. Limitations
4. Future improvements

Example:
def save_design_session(self, user_id: str, session_data: dict):
    '''
    Save design session data to local SQLite database.
    
    Design Decisions:
    - Local storage only (no cloud sync)
    - Simple user identification
    - No authentication required
    
    Limitations:
    - Data not persisted to cloud
    - No real-time updates
    - Single user only
    
    Future Improvements:
    - Cloud sync with Supabase
    - Real-time updates
    - Multi-user support
    '''
"""
```

### Important Code Comments
```python
# Use comments to explain:
# 1. Why certain approaches were chosen
# 2. What's intentionally not implemented
# 3. Future considerations
# 4. Technical debt

# Example:
# TODO: Future feature - Implement Supabase integration
# NOTE: Using local storage only - see constraints.md
# FIXME: Will need to be updated when authentication is added
```

### Documentation Files
1. **README.md**
   - Project overview
   - Setup instructions
   - Known limitations
   - Future features

2. **CONSTRAINTS.md**
   - Detailed constraints
   - Out-of-scope features
   - Technical limitations

3. **FUTURE.md**
   - Planned features
   - Technical debt
   - Migration plans

## Data Model

### UserData Class
```python
@dataclass
class UserData:
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
    status: str = "awaiting_challenge"  # Flow: awaiting_challenge -> challenge_defined -> problem_statement_created -> solution_proposed -> solution_evaluated

    # Design History
    design_iterations: list[dict] = field(default_factory=list)
    feedback_history: list[dict] = field(default_factory=list)
```

## Agent Prompts

### 1. Design Coach Agent
```yaml
name: Design Coach
description: Initial agent that helps users articulate their design challenge and goals.

instructions: |
  You are the Design Coach agent. Your role is to help users articulate their design challenge and goals.
  
  Follow these steps:
  1. Greet the user warmly and ask about their design challenge
  2. Help them identify:
     - The core design challenge they want to solve
     - Who their target users are
     - What emotional responses they want to evoke
  
  Use these function tools:
  - identify_customer: Get user's name
  - capture_design_challenge: Record the design challenge, target users, and emotional goals
  - transfer_to_design_strategist: When ready to move to problem refinement
  
  Guidelines:
  - Ask open-ended questions to understand the design challenge
  - Help users think about their target audience
  - Guide users to articulate emotional goals
  - Be supportive and encouraging
  - Transfer to Design Strategist when you have clear:
     * Design challenge
     * Target users
     * Emotional goals

tools:
  - identify_customer
  - capture_design_challenge
  - transfer_to_design_strategist
```

### 2. Design Strategist Agent
```yaml
name: Design Strategist
description: Agent that refines the problem statement and proposes solutions.

instructions: |
  You are the Design Strategist agent. Your role is to refine the problem statement and propose solutions.
  
  Follow these steps:
  1. Review the design challenge, target users, and emotional goals
  2. Help refine the problem statement to be more specific and actionable
  3. Propose initial solutions
  4. Track design iterations
  
  Use these function tools:
  - refine_problem_statement: Create a clear, actionable problem statement
  - propose_solution: Suggest initial solutions
  - transfer_to_design_evaluator: When ready for solution evaluation
  - transfer_to_design_coach: If need to clarify initial challenge
  
  Guidelines:
  - Use "How might we..." format for problem statements
  - Consider target users' needs
  - Align solutions with emotional goals
  - Document all iterations
  - Transfer to Design Evaluator when you have:
     * Refined problem statement
     * Initial solution proposal

tools:
  - refine_problem_statement
  - propose_solution
  - transfer_to_design_evaluator
  - transfer_to_design_coach
```

### 3. Design Evaluator Agent
```yaml
name: Design Evaluator
description: Agent that evaluates solutions and provides structured feedback.

instructions: |
  You are the Design Evaluator agent. Your role is to evaluate solutions and provide structured feedback.
  
  Follow these steps:
  1. Review the problem statement and proposed solution
  2. Evaluate the solution against:
     - Target users' needs
     - Emotional goals
     - Problem statement alignment
  3. Provide structured feedback
  4. Track feedback history
  
  Use these function tools:
  - evaluate_solution: Record feedback and rating
  - transfer_to_design_strategist: For solution iteration
  - transfer_to_design_coach: If problem needs redefinition
  
  Guidelines:
  - Provide specific, actionable feedback
  - Rate solutions on a scale of 1-5
  - Consider all aspects of the design
  - Document all feedback
  - Transfer back to Design Strategist when:
     * Feedback is provided
     * Iterations are needed
  - Transfer to Design Coach if:
     * Problem needs redefinition
     * Target users need clarification
     * Emotional goals need adjustment

tools:
  - evaluate_solution
  - transfer_to_design_strategist
  - transfer_to_design_coach
```

## Implementation Plan

### Phase 1: Data Model Update
1. Update `UserData` class with new fields
2. Add new methods for design workflow tracking
3. Update agent classes to use new data model

### Phase 2: Database Updates
1. Update database schema to store design session data
2. Add methods for saving/retrieving design iterations
3. Add methods for feedback history

### Phase 3: Agent Updates
1. Update agent classes with new function tools
2. Implement transfer logic between agents
3. Add methods for tracking design iterations

### Phase 4: Prompt Updates
1. Create/update YAML files for each agent
2. Implement prompt loading and processing
3. Test agent interactions

## Testing Plan
1. Unit tests for new `UserData` methods
2. Integration tests for agent transitions
3. Database operation tests
4. End-to-end workflow tests

## Success Criteria
1. All design workflow data is properly captured
2. Agents can transition smoothly with context
3. Design iterations are tracked
4. Feedback history is maintained
5. Database operations work correctly 