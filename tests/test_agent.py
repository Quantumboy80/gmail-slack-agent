import unittest
from unittest.mock import MagicMock, patch
# Add parent directory to path so we can import modules correctly
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from agent.engine import AgentEngine, EmailTriage

class TestAgentEngine(unittest.TestCase):
    @patch('agent.engine.genai.Client')
    @patch('config.GEMINI_API_KEY', 'test-api-key')
    def test_triage_email_success(self, mock_genai_client_cls):
        # Setup mock client behavior
        mock_client = MagicMock()
        mock_genai_client_cls.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.text = (
            '{"category": "action_required", "urgency": "high", '
            '"summary": "Wants a budget negotiation call.", "reasoning": "Sender explicitly asks for scheduling."}'
        )
        mock_client.models.generate_content.return_value = mock_response
        
        # Instantiate and run triage
        engine = AgentEngine()
        result = engine.triage_email(
            sender="jane@partner.com",
            subject="Partnership Discussion",
            body="Let's connect tomorrow to review the budget."
        )
        
        # Assertions
        self.assertIsInstance(result, EmailTriage)
        self.assertEqual(result.category, "action_required")
        self.assertEqual(result.urgency, "high")
        self.assertEqual(result.summary, "Wants a budget negotiation call.")
        
    @patch('agent.engine.genai.Client')
    @patch('config.GEMINI_API_KEY', 'test-api-key')
    def test_generate_draft_success(self, mock_genai_client_cls):
        mock_client = MagicMock()
        mock_genai_client_cls.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.text = "Hi Jane,\n\nI'm available to review the budget. Let me check the schedule.\n\nBest, User"
        mock_client.models.generate_content.return_value = mock_response
        
        engine = AgentEngine()
        draft = engine.generate_draft(
            sender="jane@partner.com",
            subject="Partnership Discussion",
            body="Let's connect tomorrow to review the budget."
        )
        
        self.assertEqual(draft, "Hi Jane,\n\nI'm available to review the budget. Let me check the schedule.\n\nBest, User")

if __name__ == '__main__':
    unittest.main()