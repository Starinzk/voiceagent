import sys
import os

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from dotenv import load_dotenv
from design_assistant.design_database import DesignDatabase
import json

def verify_database_data(first_name, last_name):
    """
    Connects to the database and fetches all data for a specific user.
    """
    print(f"--- Verifying Database for User: {first_name} {last_name} ---")
    try:
        load_dotenv()
        db = DesignDatabase()

        # 1. Find the user
        print(f"\n1. Searching for user '{first_name} {last_name}'...")
        user_res = db.client.table('users').select('id').eq('first_name', first_name).eq('last_name', last_name).execute()
        if not user_res.data:
            print(f"🛑 ERROR: User '{first_name} {last_name}' not found.")
            return

        user_id = user_res.data[0]['id']
        print(f"✓ User found with ID: {user_id}")

        # 2. Find their design sessions
        print(f"\n2. Searching for design sessions for user ID: {user_id}...")
        sessions = db.get_user_sessions(user_id)
        if not sessions:
            print("🛑 ERROR: No design sessions found for this user.")
            return

        print(f"✓ Found {len(sessions)} session(s).")

        # 3. Print details for each session
        for i, session in enumerate(sessions):
            session_id = session['id']
            print(f"\n--- Details for Session #{i+1} (ID: {session_id}) ---")
            
            session_details = db.get_session_details(session_id)
            
            print("\n[Session Data]")
            print(json.dumps({k: v for k, v in session_details.items() if k not in ['iterations', 'feedback']}, indent=2))
            
            print("\n[Iterations]")
            if session_details.get('iterations'):
                print(json.dumps(session_details['iterations'], indent=2))
            else:
                print("No iterations found.")
                
            print("\n[Feedback]")
            if session_details.get('feedback'):
                print(json.dumps(session_details['feedback'], indent=2))
            else:
                print("No feedback found.")
            
            print("-" * 40)
        
        print("\n--- Verification Complete ---")

    except Exception as e:
        print(f"🛑 An unexpected error occurred: {e}")

if __name__ == "__main__":
    # IMPORTANT: Change these names to the exact first and last name you gave the agent
    TEST_FIRST_NAME = "Daniel"  # <--- Make sure this matches the name you used
    TEST_LAST_NAME = "Sylvia"  # <--- Make sure this matches the name you used
    verify_database_data(TEST_FIRST_NAME, TEST_LAST_NAME) 