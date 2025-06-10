"""
Design Database Module

This module implements the database layer for the Design Assistant application using Supabase.
It provides a high-level interface for managing users, design sessions, iterations, and feedback.

Key Features:
- User management (creation and retrieval)
- Design session lifecycle management
- Design iteration tracking
- Feedback collection and storage
- Session history and retrieval

Dependencies:
- supabase: Database client
- python-dotenv: Environment variable management
- logging: Application logging

Database Schema:
- users: Stores user information
- design_sessions: Tracks design sessions and their state
- design_iterations: Records design iterations within sessions
- feedback_history: Stores feedback for design sessions
"""

import os
import re
import uuid
from typing import List, Dict, Optional, Any
import logging
from supabase import create_client, Client
from supabase._sync.client import SupabaseException
from postgrest.exceptions import APIError
from dotenv import load_dotenv
import json
from dataclasses import asdict

logger = logging.getLogger("design-assistant-db")
logger.setLevel(logging.INFO)

class DesignDatabase:
    """
    Database interface for the Design Assistant application.
    
    This class provides methods for interacting with the Supabase database,
    handling all data persistence needs of the application.
    
    Attributes:
        supabase_url (str): URL of the Supabase project
        supabase_key (str): API key for Supabase authentication
        client (Client): Supabase client instance
    """
    
    def __init__(self, supabase_url: str = None, supabase_key: str = None):
        """
        Initialize the design database with Supabase.
        
        Args:
            supabase_url (str, optional): Supabase project URL. If None, reads from SUPABASE_URL env var.
            supabase_key (str, optional): Supabase API key. If None, reads from SUPABASE_KEY env var.
            
        Raises:
            ValueError: If Supabase URL or key is not provided and not found in environment variables.
        """
        load_dotenv()
        self.supabase_url = supabase_url or os.getenv('SUPABASE_URL')
        self.supabase_key = supabase_key or os.getenv('SUPABASE_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Supabase URL and key must be provided or set in environment variables")
            
        try:
            self.client: Client = create_client(self.supabase_url, self.supabase_key)
            logger.info("Connected to Supabase database")
        except SupabaseException as e:
            raise ValueError(f"Failed to connect to Supabase: {str(e)}")

    def _validate_uuid(self, uuid_str: str) -> None:
        """Validate UUID format."""
        try:
            uuid.UUID(uuid_str)
        except ValueError:
            raise ValueError(f"Invalid UUID format: {uuid_str}")

    def _validate_required_fields(self, data: Dict[str, Any], required_fields: List[str]) -> None:
        """Validate required fields are present and not empty."""
        for field in required_fields:
            if field not in data or data[field] is None or (isinstance(data[field], str) and not data[field].strip()):
                raise ValueError(f"Required field '{field}' is missing or empty")

    def get_or_create_user(self, first_name: str, last_name: str) -> str:
        """
        Get a user by name or create if not exists.
        
        Args:
            first_name (str): The user's first name
            last_name (str): The user's last name
            
        Returns:
            str: The user's ID (either existing or newly created)
            
        Raises:
            ValueError: If first_name or last_name is empty
        """
        if not first_name or not last_name:
            raise ValueError("First name and last name are required")
            
        try:
            # Check if user exists
            response = self.client.table('users') \
                .select('id') \
                .eq('first_name', first_name) \
                .eq('last_name', last_name) \
                .execute()
                
            if response.data:
                user_id = response.data[0]['id']
                logger.info(f"Found existing user: {first_name} {last_name} (ID: {user_id})")
                return user_id
                
            # Create new user
            response = self.client.table('users') \
                .insert({
                    'first_name': first_name,
                    'last_name': last_name
                }) \
                .execute()
                
            user_id = response.data[0]['id']
            logger.info(f"Created new user: {first_name} {last_name} (ID: {user_id})")
            return user_id
        except APIError as e:
            raise ValueError(f"Failed to get or create user: {str(e)}")

    def create_design_session(self, user_id: str, design_challenge: str, target_users: List[str], emotional_goals: List[str], status: str) -> str:
        """
        Create a new design session.
        
        Args:
            user_id (str): The ID of the user creating the session
            design_challenge (str): The design challenge description
            target_users (List[str]): List of target users
            emotional_goals (List[str]): List of emotional goals
            status (str): The initial status of the session
            
        Returns:
            str: The ID of the newly created session
            
        Raises:
            ValueError: If required fields are missing or invalid
        """
        self._validate_uuid(user_id)
        self._validate_required_fields({
            'design_challenge': design_challenge,
            'target_users': target_users,
            'emotional_goals': emotional_goals,
            'status': status
        }, ['design_challenge', 'target_users', 'emotional_goals', 'status'])
        
        try:
            response = self.client.table('design_sessions') \
                .insert({
                    'user_id': user_id,
                    'design_challenge': design_challenge,
                    'target_users': target_users,
                    'emotional_goals': emotional_goals,
                    'status': status
                }) \
                .execute()
                
            session_id = response.data[0]['id']
            logger.info(f"Created new design session (ID: {session_id}) for user ID: {user_id}")
            return session_id
        except APIError as e:
            raise ValueError(f"Failed to create design session: {str(e)}")

    def update_session(self, session_id: str, updates: Dict[str, Any]) -> None:
        """
        Update a design session with new data.
        
        Args:
            session_id (str): The ID of the session to update
            updates (Dict[str, Any]): Dictionary of fields to update
            
        Raises:
            ValueError: If session_id is invalid or session not found
        """
        self._validate_uuid(session_id)
        
        try:
            response = self.client.table('design_sessions') \
                .update(updates) \
                .eq('id', session_id) \
                .execute()
                
            if not response.data:
                raise ValueError(f"Session not found: {session_id}")
                
            logger.info(f"Updated design session (ID: {session_id})")
        except APIError as e:
            raise ValueError(f"Failed to update session: {str(e)}")

    def add_design_iteration(self, session_id: str, problem_statement: str, solution: str) -> str:
        """
        Add a new design iteration to a session.
        
        Args:
            session_id (str): The ID of the session
            problem_statement (str): The problem statement
            solution (str): The proposed solution
            
        Returns:
            str: The ID of the new iteration
            
        Raises:
            ValueError: If required fields are missing or invalid
        """
        self._validate_uuid(session_id)
        self._validate_required_fields({
            'problem_statement': problem_statement,
            'solution': solution
        }, ['problem_statement', 'solution'])
        
        try:
            response = self.client.table('design_iterations') \
                .insert({
                    'session_id': session_id,
                    'problem_statement': problem_statement,
                    'solution': solution
                }) \
                .execute()
                
            iteration_id = response.data[0]['id']
            logger.info(f"Added new design iteration (ID: {iteration_id}) to session ID: {session_id}")
            return iteration_id
        except APIError as e:
            raise ValueError(f"Failed to add design iteration: {str(e)}")

    def add_feedback(self, session_id: str, feedback_data: Dict[str, Any]) -> str:
        """
        Add feedback to a design session.
        
        Args:
            session_id (str): The ID of the session
            feedback_data (Dict[str, Any]): The feedback data
            
        Returns:
            str: The ID of the new feedback entry
            
        Raises:
            ValueError: If session_id is invalid or feedback_data is empty
        """
        self._validate_uuid(session_id)
        if not feedback_data:
            raise ValueError("Feedback data cannot be empty")
        
        try:
            response = self.client.table('feedback_history') \
                .insert({
                    'session_id': session_id,
                    'feedback_data': feedback_data
                }) \
                .execute()
                
            feedback_id = response.data[0]['id']
            logger.info(f"Added new feedback (ID: {feedback_id}) to session ID: {session_id}")
            return feedback_id
        except APIError as e:
            raise ValueError(f"Failed to add feedback: {str(e)}")

    def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all design sessions for a user.
        
        Args:
            user_id (str): The ID of the user
            
        Returns:
            List[Dict[str, Any]]: List of design sessions
            
        Raises:
            ValueError: If user_id is invalid
        """
        self._validate_uuid(user_id)
        
        try:
            response = self.client.table('design_sessions') \
                .select('*') \
                .eq('user_id', user_id) \
                .order('created_at', desc=True) \
                .execute()
                
            return response.data
        except APIError as e:
            raise ValueError(f"Failed to get user sessions: {str(e)}")

    def get_session_details(self, session_id: str) -> Dict[str, Any]:
        """
        Get full details of a design session including iterations and feedback.
        
        Args:
            session_id (str): The ID of the session
            
        Returns:
            Dict[str, Any]: Session details including iterations and feedback
            
        Raises:
            ValueError: If session_id is invalid or session not found
        """
        self._validate_uuid(session_id)
        
        try:
            # Get session
            session_response = self.client.table('design_sessions') \
                .select('*') \
                .eq('id', session_id) \
                .single() \
                .execute()
                
            if not session_response.data:
                raise ValueError(f"Session not found: {session_id}")
                
            session = session_response.data
            
            # Get iterations
            iterations_response = self.client.table('design_iterations') \
                .select('*') \
                .eq('session_id', session_id) \
                .order('created_at', desc=True) \
                .execute()
                
            # Get feedback
            feedback_response = self.client.table('feedback_history') \
                .select('*') \
                .eq('session_id', session_id) \
                .order('created_at', desc=True) \
                .execute()
                
            return {
                **session,
                'iterations': iterations_response.data,
                'feedback': feedback_response.data
            }
        except APIError as e:
            raise ValueError(f"Failed to get session details: {str(e)}")

    def save_user_data(self, user_data: Any) -> str:
        """
        Save the current state of a UserData instance to the database.
        
        Args:
            user_data: The UserData instance to save
            
        Returns:
            str: The ID of the session
            
        Raises:
            ValueError: If required fields are missing or invalid
        """
        # Validate required fields
        self._validate_required_fields({
            'first_name': user_data.first_name,
            'last_name': user_data.last_name,
            'design_challenge': user_data.design_challenge
        }, ['first_name', 'last_name', 'design_challenge'])
        
        # Create a copy of the data without non-serializable fields
        data_dict = {
            'first_name': user_data.first_name,
            'last_name': user_data.last_name,
            'user_id': user_data.user_id,
            'design_challenge': user_data.design_challenge,
            'status': user_data.status,
            'proposed_solution': user_data.proposed_solution,
            'design_iterations': user_data.design_iterations,
            'feedback_history': user_data.feedback_history,
            'personas': user_data.personas,
            'ctx': user_data.ctx
        }
        
        try:
            # Create or update user record
            user_id = self.get_or_create_user(data_dict['first_name'], data_dict['last_name'])
            
            # Check for existing session
            existing_sessions = self.get_user_sessions(user_id)
            session_id = None
            
            for session in existing_sessions:
                if session['design_challenge'] == data_dict['design_challenge']:
                    session_id = session['id']
                    break
            
            if session_id:
                # Update existing session
                self.update_session(session_id, {
                    'proposed_solution': data_dict['proposed_solution'],
                    'personas': data_dict['personas'],
                    'ctx': data_dict['ctx'],
                    'status': data_dict['status']
                })
            else:
                # Create new session
                session_id = self.create_design_session(
                    user_id=user_id,
                    design_challenge=data_dict['design_challenge'],
                    target_users=user_data.target_users,
                    emotional_goals=user_data.emotional_goals,
                    status=data_dict['status']
                )
                
                # Update session with additional data
                self.update_session(session_id, {
                    'proposed_solution': data_dict['proposed_solution'],
                    'personas': data_dict['personas'],
                    'ctx': data_dict['ctx']
                })
            
            # Save iterations and feedback, avoiding duplicates
            existing_iterations_res = self.client.table('design_iterations').select('problem_statement,solution').eq('session_id', session_id).execute()
            existing_iterations = [(i['problem_statement'], i['solution']) for i in existing_iterations_res.data]

            for iteration in data_dict['design_iterations']:
                if (iteration['problem_statement'], iteration['solution']) not in existing_iterations:
                    self.add_design_iteration(session_id, iteration['problem_statement'], iteration['solution'])

            existing_feedback_res = self.client.table('feedback_history').select('feedback_data').eq('session_id', session_id).execute()
            existing_feedback = [f['feedback_data'] for f in existing_feedback_res.data]

            for feedback in data_dict['feedback_history']:
                if feedback not in existing_feedback:
                    self.add_feedback(session_id, feedback)
            
            return session_id
        except APIError as e:
            raise ValueError(f"Failed to save user data: {str(e)}")

    def load_user_data(self, session_id: str) -> Any:
        """
        Load a UserData instance from the database using a session ID.
        
        Args:
            session_id: The ID of the session to load
            
        Returns:
            UserData: A new UserData instance populated with the saved state
            
        Raises:
            ValueError: If the session ID is invalid or the session doesn't exist
        """
        self._validate_uuid(session_id)
        
        try:
            # Get session details
            session = self.get_session_details(session_id)
            if not session:
                raise ValueError("Session not found")
            
            # Get user details
            user = self.client.table('users').select('*').eq('id', session['user_id']).single().execute()
            if not user.data:
                raise ValueError("User not found")
            
            # Get iterations and feedback
            iterations = self.client.table('design_iterations').select('*').eq('session_id', session_id).execute()
            feedback = self.client.table('feedback_history').select('*').eq('session_id', session_id).execute()
            
            # Create new UserData instance
            from design_assistant.design_assistant import UserData
            user_data = UserData(
                first_name=user.data['first_name'],
                last_name=user.data['last_name'],
                user_id=user.data['id'],
                design_challenge=session['design_challenge'],
                target_users=session.get('target_users', []),
                emotional_goals=session.get('emotional_goals', []),
                status=session['status'],
                proposed_solution=session.get('proposed_solution'),
                design_iterations=[{
                    'problem_statement': i['problem_statement'],
                    'solution': i['solution']
                } for i in iterations.data],
                feedback_history=[f['feedback_data'] for f in feedback.data],
                personas=session.get('personas', {}),
                ctx=session.get('ctx'),
                db=self
            )
            
            return user_data
        except APIError as e:
            raise ValueError(f"Failed to load user data: {str(e)}") 