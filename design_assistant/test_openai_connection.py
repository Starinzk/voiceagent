import os
import openai
from dotenv import load_dotenv

def test_openai_connection():
    """
    Tests the connection to the OpenAI API using the provided API key.
    """
    print("--- Testing OpenAI API Connection ---")
    try:
        # Load environment variables from .env file
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            print("🛑 ERROR: OPENAI_API_KEY not found in .env file.")
            return

        print("✓ OPENAI_API_KEY loaded.")

        # Initialize the OpenAI client
        client = openai.OpenAI(api_key=api_key)
        print("✓ OpenAI client initialized.")

        # Make a simple test call
        print("... Sending a test message to gpt-3.5-turbo ...")
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": "Say this is a test.",
                }
            ],
            model="gpt-3.5-turbo",
        )

        response_message = chat_completion.choices[0].message.content
        print(f"✓ SUCCESS! Response from OpenAI: '{response_message}'")
        print("--- Test Complete ---")

    except openai.APIConnectionError as e:
        print("🛑 ERROR: Failed to connect to OpenAI.")
        print("This may be a network issue (firewall, proxy) or the API is temporarily down.")
        print(f"Details: {e.__cause__}")
    except openai.RateLimitError as e:
        print("🛑 ERROR: OpenAI Rate Limit Exceeded.")
        print("You have hit your usage limit. Please check your OpenAI account.")
    except openai.AuthenticationError as e:
        print("🛑 ERROR: OpenAI Authentication Failed.")
        print("Your API key is likely invalid or has been revoked. Please verify it.")
    except Exception as e:
        print(f"🛑 An unexpected error occurred: {e}")

if __name__ == "__main__":
    test_openai_connection() 