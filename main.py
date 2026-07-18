import time
import sys
import config
from config import validate_config, POLL_INTERVAL_SECONDS
from integrations.gmail_client import GmailClient
from integrations.slack_client import SlackClient
from agent.engine import AgentEngine
def main():
    print("================================================")
    print("🚀 Starting Slack-Gmail Agentic AI System...")
    print("================================================")
    
    # Print loaded API Key preview for diagnostic verification
    api_key_preview = config.GEMINI_API_KEY[:8] + "..." if config.GEMINI_API_KEY else "Not Configured"
    print(f"[Diagnostic] Loaded Gemini API Key starts with: {api_key_preview}")
    
    # 1. Validate environment configuration
    try:
        validate_config()
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("\nPlease fill in your configuration values in the '.env' file.")
        sys.exit(1)
    
    # 2. Initialize integrations and agent engine
    try:
        print("[System] Connecting to Gmail API (this may prompt browser login if running first time)...")
        gmail_client = GmailClient()
        
        print("[System] Connecting to Gemini AI engine...")
        agent_engine = AgentEngine()
        
        print("[System] Initializing Slack App client...")
        slack_client = SlackClient(gmail_client=gmail_client, agent_engine=agent_engine)
        
    except Exception as e:
        print(f"❌ Initialization error: {e}")
        sys.exit(1)
    # 3. Start Slack Socket Mode Listener (handles interactive buttons in background)
    try:
        slack_client.start()
    except Exception as e:
        print(f"❌ Failed to start Slack Socket Mode handler: {e}")
        sys.exit(1)
    # 4. Polling loop to fetch new Gmail messages
    print(f"\n[System] Active polling enabled. Checking for unread emails every {POLL_INTERVAL_SECONDS} seconds.")
    print("Press Ctrl+C to stop the application.\n")
    
    try:
        while True:
            try:
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Polling Gmail for new unread messages...")
                unread_emails = gmail_client.fetch_unread_messages(max_results=5)
                
                if not unread_emails:
                    print("-> No new unread emails.")
                
                for email in unread_emails:
                    print(f"\n📨 Processing email ID: {email['id']}")
                    print(f"   Subject: '{email['subject']}'")
                    print(f"   From: {email['sender']}")
                    
                    # Call Gemini Agent Engine to triage email
                    triage = agent_engine.triage_email(
                        sender=email['sender'],
                        subject=email['subject'],
                        body=email['body']
                    )
                    print(f"   AI Triage: Category={triage.category.upper()}, Urgency={triage.urgency.upper()}")
                    
                    if triage.category == "spam":
                        print("   Action: Auto-archiving (marking as read).")
                        gmail_client.mark_as_read(email['id'])
                        
                    elif triage.category == "informational":
                        print("   Action: Posting summary to Slack and marking as read.")
                        # Post a simple notification block for info-only email
                        info_blocks = [
                            {
                                "type": "section",
                                "text": {
                                    "type": "mrkdwn",
                                    "text": f"ℹ️ *Informational Email Alert*\n*From:* {email['sender']}\n*Subject:* {email['subject']}\n\n*AI Summary:*\n{triage.summary}"
                                }
                            }
                        ]
                        slack_client.app.client.chat_postMessage(
                            channel=config.SLACK_CHANNEL_ID,
                            text=f"Informational email: {email['subject']}",
                            blocks=info_blocks
                        )
                        gmail_client.mark_as_read(email['id'])
                        
                    elif triage.category == "action_required":
                        print("   Action: Generating reply draft and posting to Slack channel...")
                        draft_content = agent_engine.generate_draft(
                            sender=email['sender'],
                            subject=email['subject'],
                            body=email['body']
                        )
                        
                        # Post full interactive block to Slack (saves details for callbacks)
                        slack_client.post_email_notification(email, triage, draft_content)
                        
                        # Mark as read instantly in Gmail to prevent duplicate polling detection
                        gmail_client.mark_as_read(email['id'])
                        
            except Exception as e:
                print(f"⚠️ Error during polling cycle: {e}")
                
            time.sleep(POLL_INTERVAL_SECONDS)
            
    except KeyboardInterrupt:
        print("\n[System] Keyboard interrupt received. Shutting down...")
    finally:
        print("[System] Closing active sessions...")
        slack_client.stop()
        print("👋 System stopped. Goodbye!")
if __name__ == "__main__":
    main()
