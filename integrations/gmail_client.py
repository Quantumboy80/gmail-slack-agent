import os
import base64
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import config

# If modifying these scopes, delete the file token.json.
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.compose',
    'https://www.googleapis.com/auth/gmail.modify'
]

class GmailClient:
    def __init__(self):
        self.creds = self._authenticate()
        self.service = build('gmail', 'v1', credentials=self.creds)

    def _authenticate(self):
        """Handles user authentication and returns Google credentials."""
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first time.
        if os.path.exists(config.GMAIL_TOKEN_PATH):
            creds = Credentials.from_authorized_user_file(config.GMAIL_TOKEN_PATH, SCOPES)
        
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(config.GMAIL_CREDENTIALS_PATH):
                    raise FileNotFoundError(
                        f"Gmail OAuth client secret file '{config.GMAIL_CREDENTIALS_PATH}' not found. "
                        f"Please download it from Google Cloud Console and place it in the project root."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    config.GMAIL_CREDENTIALS_PATH, SCOPES)
                # Local webserver flow for authentication
                creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open(config.GMAIL_TOKEN_PATH, 'w') as token:
                token.write(creds.to_json())
        
        return creds

    def fetch_unread_messages(self, max_results=5):
        """Fetches unread messages from the inbox."""
        try:
            results = self.service.users().messages().list(
                userId='me', q='is:unread label:INBOX', maxResults=max_results
            ).execute()
            messages = results.get('messages', [])
            
            detailed_messages = []
            for msg in messages:
                detailed_msg = self.get_message_details(msg['id'])
                if detailed_msg:
                    detailed_messages.append(detailed_msg)
            return detailed_messages
        except HttpError as error:
            print(f"An error occurred fetching messages: {error}")
            return []

    def get_message_details(self, message_id):
        """Retrieves details (Headers, Snippet, Body) for a single message."""
        try:
            message = self.service.users().messages().get(
                userId='me', id=message_id, format='full'
            ).execute()
            
            headers = message.get('payload', {}).get('headers', [])
            subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '(No Subject)')
            sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), '(Unknown Sender)')
            to_email = next((h['value'] for h in headers if h['name'].lower() == 'to'), '')
            message_id_header = next((h['value'] for h in headers if h['name'].lower() == 'message-id'), '')
            date = next((h['value'] for h in headers if h['name'].lower() == 'date'), '')
            
            # Extract plain text body
            body = ""
            payload = message.get('payload', {})
            
            def extract_body(part):
                part_body = ""
                mime_type = part.get('mimeType', '')
                data = part.get('body', {}).get('data', '')
                
                if mime_type == 'text/plain' and data:
                    part_body = base64.urlsafe_b64decode(data.encode('ASCII')).decode('utf-8')
                elif 'parts' in part:
                    for subpart in part['parts']:
                        part_body += extract_body(subpart)
                return part_body

            if 'parts' in payload:
                for part in payload['parts']:
                    body += extract_body(part)
            else:
                data = payload.get('body', {}).get('data', '')
                if data:
                    body = base64.urlsafe_b64decode(data.encode('ASCII')).decode('utf-8')
            
            if not body:
                body = message.get('snippet', '')

            return {
                'id': message_id,
                'threadId': message.get('threadId'),
                'subject': subject,
                'sender': sender,
                'to': to_email,
                'date': date,
                'snippet': message.get('snippet', ''),
                'body': body,
                'message_id_header': message_id_header
            }
        except HttpError as error:
            print(f"An error occurred getting message details for {message_id}: {error}")
            return None

    def mark_as_read(self, message_id):
        """Removes the UNREAD label from a message."""
        try:
            self.service.users().messages().batchModify(
                userId='me',
                body={
                    'ids': [message_id],
                    'removeLabelIds': ['UNREAD']
                }
            ).execute()
            return True
        except HttpError as error:
            print(f"An error occurred modifying message labels: {error}")
            return False

    def send_email(self, to, subject, body, thread_id=None, in_reply_to=None):
        """Sends an email, optionally as a reply in a thread."""
        try:
            mime_message = MIMEText(body)
            mime_message['to'] = to
            mime_message['subject'] = subject
            if in_reply_to:
                mime_message['In-Reply-To'] = in_reply_to
                mime_message['References'] = in_reply_to

            raw_message = base64.urlsafe_b64encode(mime_message.as_bytes()).decode('utf-8')
            body_payload = {'raw': raw_message}
            if thread_id:
                body_payload['threadId'] = thread_id

            sent_message = self.service.users().messages().send(
                userId='me', body=body_payload
            ).execute()
            return sent_message
        except HttpError as error:
            print(f"An error occurred sending email: {error}")
            raise error