import os
from supabase import create_client, Client
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_database():
    """Set up the database schema in Supabase."""
    # Load environment variables
    load_dotenv()
    
    # Initialize Supabase client
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    if not supabase_url or not supabase_key:
        raise ValueError("Supabase URL and key must be set in environment variables")
    
    client: Client = create_client(supabase_url, supabase_key)
    logger.info("Connected to Supabase")

    # Create exec_sql function if it doesn't exist
    create_exec_sql = """
    CREATE OR REPLACE FUNCTION exec_sql(query text)
    RETURNS void AS $$
    BEGIN
        EXECUTE query;
    END;
    $$ LANGUAGE plpgsql SECURITY DEFINER;
    """
    
    try:
        client.rpc('exec_sql', {'query': create_exec_sql}).execute()
        logger.info("Created exec_sql function")
    except Exception as e:
        logger.warning(f"Error creating exec_sql function: {str(e)}")

    # SQL commands to execute
    commands = [
        # 1. Enable UUID extension
        """
        CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
        """,
        
        # 2. Drop existing tables
        """
        DROP TABLE IF EXISTS orders;
        DROP TABLE IF EXISTS customers;
        """,
        
        # 3. Create new tables
        """
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
            personas JSONB DEFAULT '{}',
            ctx JSONB,
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
        """,
        
        # 4. Create indexes
        """
        CREATE INDEX idx_users_name ON users(first_name, last_name);
        CREATE INDEX idx_sessions_user ON design_sessions(user_id);
        CREATE INDEX idx_sessions_status ON design_sessions(status);
        """,
        
        # 5. Set up RLS policies
        """
        ALTER TABLE users ENABLE ROW LEVEL SECURITY;
        ALTER TABLE design_sessions ENABLE ROW LEVEL SECURITY;
        ALTER TABLE design_iterations ENABLE ROW LEVEL SECURITY;
        ALTER TABLE feedback_history ENABLE ROW LEVEL SECURITY;

        CREATE POLICY "Allow all operations for authenticated users" ON users
            FOR ALL USING (true);

        CREATE POLICY "Allow all operations for authenticated users" ON design_sessions
            FOR ALL USING (true);

        CREATE POLICY "Allow all operations for authenticated users" ON design_iterations
            FOR ALL USING (true);

        CREATE POLICY "Allow all operations for authenticated users" ON feedback_history
            FOR ALL USING (true);
        """
    ]

    # Execute each command
    for i, command in enumerate(commands, 1):
        try:
            logger.info(f"Executing command set {i}...")
            client.rpc('exec_sql', {'query': command}).execute()
            logger.info(f"Successfully executed command set {i}")
        except Exception as e:
            logger.error(f"Error executing command set {i}: {str(e)}")
            raise

    logger.info("Database setup completed successfully")

if __name__ == "__main__":
    setup_database() 