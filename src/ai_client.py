import os
from dotenv import load_dotenv
from google import genai


class AIClient:
    """Simple client for Google Gemini API using the Interactions API."""

    def __init__(self):
        # Load environment variables
        load_dotenv()

        # Get API key
        api_key = os.getenv("GOOGLE_API_KEY")

        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY not found in environment variables"
            )

        # Create Gemini client
        self.client = genai.Client(api_key=api_key)

        # Choose the Gemini model
        self.model = "gemini-3.6-flash"

    def chat(self, message):
        """Send a message to AI and get a response."""
        try:
            interaction = self.client.interactions.create(
                model=self.model,
                input=message
            )

            return interaction.output_text

        except Exception as e:
            return f"Error: {str(e)}"

    def chat_with_history(self, messages):
        """Send a message using conversation history."""

        try:
            # For a simple conversation, use the latest message
            # and let the Interactions API maintain the conversation
            # using previous_interaction_id.
            interaction = self.client.interactions.create(
                model=self.model,
                input=messages[-1]
            )

            return interaction.output_text

        except Exception as e:
            return f"Error: {str(e)}"


# Test the client
if __name__ == "__main__":
    try:
        client = AIClient()

        response = client.chat(
            "Hello! Tell me a fun fact about AI."
        )

        print(f"AI Response: {response}")

    except Exception as e:
        print(f"Error: {e}")