import unittest
from unittest.mock import MagicMock, patch
import sys
import base64
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from integrations.gmail_client import GmailClient

class TestGmailClient(unittest.TestCase):
    @patch('integrations.gmail_client.Credentials')
    @patch('integrations.gmail_client.build')
    @patch('os.path.exists', return_value=True)
    def setUp(self, mock_exists, mock_build, mock_credentials):
        self.mock_service = MagicMock()
        mock_build.return_value = self.mock_service
        self.client = GmailClient()

    def test_get_message_details_plain_text(self):
        # Setup mock payload with plain text body encoded in URLsafe base64
        body_content = "Hello, this is a test email body."
        encoded_body = base64.urlsafe_b64encode(body_content.encode('utf-8')).decode('utf-8')
        
        mock_message_response = {
            'id': '12345',
            'threadId': 'abcde',
            'snippet': 'Hello, this is a test...',
            'payload': {
                'mimeType': 'text/plain',
                'headers': [
                    {'name': 'From', 'value': 'Sender Name <sender@example.com>'},
                    {'name': 'Subject', 'value': 'Test Subject Line'},
                    {'name': 'Date', 'value': 'Sat, 18 Jul 2026 12:00:00 -0000'},
                    {'name': 'Message-ID', 'value': '<unique-msg-id@mail.com>'}
                ],
                'body': {
                    'data': encoded_body
                }
            }
        }
        
        # Configure Gmail API mock response
        self.mock_service.users().messages().get(
            userId='me', id='12345', format='full'
        ).execute.return_value = mock_message_response

        # Call the method
        details = self.client.get_message_details('12345')

        # Assertions
        self.assertEqual(details['id'], '12345')
        self.assertEqual(details['threadId'], 'abcde')
        self.assertEqual(details['subject'], 'Test Subject Line')
        self.assertEqual(details['sender'], 'Sender Name <sender@example.com>')
        self.assertEqual(details['body'], body_content)
        self.assertEqual(details['message_id_header'], '<unique-msg-id@mail.com>')

if __name__ == '__main__':
    unittest.main()