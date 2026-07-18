from pydantic import BaseModel, Field
from google import genai
from google.genai import types
import config
from agent.templates import (
    CATEGORIZATION_SYSTEM_PROMPT,
    DRAFT_SYSTEM_PROMPT,
    REVISION_SYSTEM_PROMPT
)

# Define schemas for Structured Outputs
class EmailTriage(BaseModel):
    category: str = Field(description="Must be one of: 'action_required', 'informational', or 'spam'")
    urgency: str = Field(description="Must be one of: 'high', 'medium', or 'low'")
    summary: str = Field(description="A brief, one-sentence summary of the email's core message.")
    reasoning: str = Field(description="Brief explanation of why you chose this category.")

class AgentEngine:
    def __init__(self):
        if not config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not configured in environment.")
        # Instantiate the new Google Gen AI client
        self.client = genai.Client(api_key=config.GEMINI_API_KEY)
        self.model_name = "gemini-2.0-flash-lite"  # Highly performant and fast for triage

    def triage_email(self, sender: str, subject: str, body: str) -> EmailTriage:
        """Categorizes and summarizes the incoming email."""
        prompt = f"From: {sender}\nSubject: {subject}\n\nEmail Content:\n{body}"
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=CATEGORIZATION_SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    response_schema=EmailTriage,
                    temperature=0.1,  # Lower temperature for deterministic classification
                )
            )
            # Parse the JSON response directly into Pydantic model
            return EmailTriage.model_validate_json(response.text)
        except Exception as e:
            print(f"Error during triage: {e}")
            # Fallback in case of API failure
            return EmailTriage(
                category="action_required",
                urgency="medium",
                summary="Failed to summarize email due to an API error.",
                reasoning=str(e)
            )

    def generate_draft(self, sender: str, subject: str, body: str) -> str:
        """Generates a response draft for the incoming email."""
        prompt = f"From: {sender}\nSubject: {subject}\n\nEmail Content:\n{body}"
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=DRAFT_SYSTEM_PROMPT,
                    temperature=0.7,
                )
            )
            return response.text.strip()
        except Exception as e:
            print(f"Error generating draft: {e}")
            return f"Hi,\n\n[Failed to generate draft. Error: {e}]"

    def revise_draft(self, original_body: str, current_draft: str, feedback: str) -> str:
        """Revises a draft based on user feedback."""
        prompt = (
            f"--- ORIGINAL EMAIL ---\n{original_body}\n\n"
            f"--- CURRENT DRAFT ---\n{current_draft}\n\n"
            f"--- USER FEEDBACK ---\n{feedback}\n\n"
            f"Please revise the current draft according to the user feedback."
        )
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=REVISION_SYSTEM_PROMPT,
                    temperature=0.7,
                )
            )
            return response.text.strip()
        except Exception as e:
            print(f"Error revising draft: {e}")
            return current_draft