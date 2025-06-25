"""
Database Cleanup Script

This script connects to the Supabase database and deletes all records from the
application's tables to ensure a clean state for testing.

It deletes records in the correct order to respect foreign key constraints.
"""
import sys
import os

# Add project root to Python path for module resolution
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from design_assistant.design_database import DesignDatabase
from dotenv import load_dotenv

def cleanup_database():
    """
    Connects to the database and deletes all data from all tables.
    """
    print("--- Starting Database Cleanup ---")
    try:
        load_dotenv()
        db = DesignDatabase()
        client = db.client

        # The order of deletion is important to avoid foreign key violations.
        # We delete from tables with foreign keys first.

        print("1. Deleting all records from 'feedback_history'...")
        client.table('feedback_history').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
        print("✓ 'feedback_history' cleared.")

        print("\n2. Deleting all records from 'design_iterations'...")
        client.table('design_iterations').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
        print("✓ 'design_iterations' cleared.")

        print("\n3. Deleting all records from 'design_sessions'...")
        client.table('design_sessions').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
        print("✓ 'design_sessions' cleared.")
        
        print("\n4. Deleting all records from 'users'...")
        client.table('users').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
        print("✓ 'users' cleared.")

        print("\n--- Database Cleanup Complete ---")

    except Exception as e:
        print(f"🛑 An unexpected error occurred during cleanup: {e}")

if __name__ == "__main__":
    cleanup_database() 