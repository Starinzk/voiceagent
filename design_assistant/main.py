"""
Main Application Entry Point

This module serves as the new entrypoint for the design assistant application.
It instantiates all components and starts the voice-enabled design workflow.

Refactored from design_assistant.py as part of the backend refactoring.
"""

import os
import sys
import json
import logging
from dotenv import load_dotenv

from livekit.agents import JobContext, WorkerOptions, WorkerType, cli, WorkerPermissions, JobRequest

from user_data import UserData
from session import DesignSession  
from design_database import DesignDatabase

# Load environment variables
load_dotenv()

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Environment Variable Check ---
REQUIRED_ENV_VARS = [
    "SUPABASE_URL",
    "SUPABASE_KEY", 
    "OPENAI_API_KEY",
    "DEEPGRAM_API_KEY",
    "CARTESIA_API_KEY",
    "LIVEKIT_URL",
    "LIVEKIT_API_KEY",
    "LIVEKIT_API_SECRET",
]

missing_vars = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
if missing_vars:
    print("FATAL ERROR: The following required environment variables are not set:")
    for var in missing_vars:
        print(f"- {var}")
    print("\nPlease set them in your .env file before running the application.")
    sys.exit(1)
# --- End of Environment Variable Check ---

async def entrypoint(ctx: JobContext):
    """Initialize and start the design assistant application in a worker."""
    print(f"\\n=== WORKER AGENT JOB RECEIVED ===")
    print(f"Joining room: {ctx.room.name}")

    await ctx.connect()
    print(f"Successfully connected to room: {ctx.room.name}")

    print("--- DATABASE: Initializing DesignDatabase inside entrypoint ---")
    db = DesignDatabase()
    print("--- DATABASE: DesignDatabase initialized ---")

    # Create user data with database connection
    user_data = UserData(ctx=ctx, db=db)

    # Create and initialize the design session
    session = DesignSession(user_data)
    await session.initialize()
    
    print("--- SESSION: DesignSession initialized with all agents ---")

    # Start the session with the initial agent (Coach)
    await session.start(ctx.room)


async def request_fnc(req: JobRequest):
    """Handle incoming job requests."""
    print("Received job request", req)
    await req.accept(
        identity="design_coach",
        metadata=json.dumps({"is_agent": "true"})
    )


def main():
    """Main application entry point."""
    print("\n=== STARTING DESIGN ASSISTANT WORKER ===")

    permissions = WorkerPermissions(
        can_publish=True,
        can_publish_data=True,
        can_subscribe=True,
        hidden=False,
    )

    worker_opts = WorkerOptions(
        request_fnc=request_fnc,
        entrypoint_fnc=entrypoint,
        permissions=permissions,
        num_idle_processes=1,
    )

    # Add 'start' to the command-line arguments if no command is provided
    if len(sys.argv) < 2 or sys.argv[1] not in [
        "connect",
        "console", 
        "dev",
        "download-files",
        "start",
    ]:
        sys.argv.insert(1, "start")

    cli.run_app(worker_opts)


if __name__ == "__main__":
    main() 