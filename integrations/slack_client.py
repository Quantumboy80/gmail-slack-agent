import json
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import config

class SlackClient:
    def __init__(self, gmail_client=None, agent_engine=None):
        self.gmail_client = gmail_client
        self.agent_engine = agent_engine
        
        # Initialize the Slack Bolt App
        self.app = App(
            token=config.SLACK_BOT_TOKEN,
            signing_secret=config.SLACK_SIGNING_SECRET
        )
        
        # In-memory store for pending email drafts
        # Key: slack_message_ts, Value: email details dict
        self.pending_actions = {}
        
        # Register Slack event and action handlers
        self._register_handlers()

    def start(self):
        """Starts the Slack Socket Mode listener in the background."""
        if not config.SLACK_APP_TOKEN:
            raise ValueError("SLACK_APP_TOKEN is required for Socket Mode.")
        self.handler = SocketModeHandler(self.app, config.SLACK_APP_TOKEN)
        self.handler.connect()
        print("[Slack] Socket Mode listener started successfully.")

    def stop(self):
        """Stops the Slack Socket Mode listener."""
        if hasattr(self, 'handler'):
            self.handler.close()

    def post_email_notification(self, email_meta, triage, draft_content):
        """Formats and posts a new email notification to the Slack channel."""
        channel_id = config.SLACK_CHANNEL_ID
        
        # Determine urgency color block indicator
        urgency_indicator = "🔴 *HIGH*" if triage.urgency == "high" else "🟡 *MEDIUM*" if triage.urgency == "medium" else "🟢 *LOW*"
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "📬 New Email Received"
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*From:*\n{email_meta['sender']}"},
                    {"type": "mrkdwn", "text": f"*Subject:*\n{email_meta['subject']}"}
                ]
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Urgency:*\n{urgency_indicator}"},
                    {"type": "mrkdwn", "text": f"*AI Summary:*\n{triage.summary}"}
                ]
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Proposed Response Draft:*\n```\n{draft_content}\n```"
                }
            },
            {
                "type": "actions",
                "block_id": "email_actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "🚀 Approve & Send"},
                        "style": "primary",
                        "action_id": "approve_action",
                        "value": email_meta['id']
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "✍️ Revise Draft"},
                        "action_id": "revise_action",
                        "value": email_meta['id']
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "🗑️ Discard"},
                        "style": "danger",
                        "action_id": "discard_action",
                        "value": email_meta['id']
                    }
                ]
            }
        ]

        try:
            response = self.app.client.chat_postMessage(
                channel=channel_id,
                text=f"New email from {email_meta['sender']}: {email_meta['subject']}",
                blocks=blocks
            )
            ts = response['ts']
            
            # Store full context mapped to the Slack message timestamp
            self.pending_actions[ts] = {
                'email_meta': email_meta,
                'triage': triage,
                'draft': draft_content
            }
            print(f"[Slack] Posted notification for email ID: {email_meta['id']} (TS: {ts})")
            return ts
        except Exception as e:
            print(f"[Slack] Error posting message: {e}")
            return None

    def _register_handlers(self):
        """Registers Bolt handlers for interactive events."""
        
        @self.app.action("approve_action")
        def handle_approve(ack, body, client):
            ack()
            ts = body["message"]["ts"]
            channel = body["channel"]["id"]
            
            if ts not in self.pending_actions:
                client.chat_postEphemeral(
                    channel=channel,
                    user=body["user"]["id"],
                    text="⚠️ Error: Session expired or draft context not found."
                )
                return
            
            pending = self.pending_actions[ts]
            meta = pending['email_meta']
            draft = pending['draft']
            
            # Perform Action: Send the email
            try:
                if self.gmail_client:
                    self.gmail_client.send_email(
                        to=meta['sender'],
                        subject=f"Re: {meta['subject']}",
                        body=draft,
                        thread_id=meta['threadId'],
                        in_reply_to=meta['message_id_header']
                    )
                    # Mark email as read in Gmail
                    self.gmail_client.mark_as_read(meta['id'])
                
                # Update Slack message to show success state
                client.chat_update(
                    channel=channel,
                    ts=ts,
                    text="✅ Email Sent!",
                    blocks=[
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"✅ *Email Response Sent!*\n*To:* {meta['sender']}\n*Subject:* Re: {meta['subject']}\n\n*Sent Response:*\n```\n{draft}\n```"
                            }
                        }
                    ]
                )
                # Remove from active cache
                del self.pending_actions[ts]
                print(f"[Slack] Email sent for TS {ts}")
            except Exception as e:
                client.chat_postEphemeral(
                    channel=channel,
                    user=body["user"]["id"],
                    text=f"❌ Failed to send email: {e}"
                )

        @self.app.action("discard_action")
        def handle_discard(ack, body, client):
            ack()
            ts = body["message"]["ts"]
            channel = body["channel"]["id"]
            
            if ts not in self.pending_actions:
                return
            
            pending = self.pending_actions[ts]
            meta = pending['email_meta']
            
            # Mark as read so we don't pick it up again
            if self.gmail_client:
                self.gmail_client.mark_as_read(meta['id'])
                
            client.chat_update(
                channel=channel,
                ts=ts,
                text="🗑️ Email Discarded.",
                blocks=[
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"🗑️ *Triage Discarded / Marked Read*\n*From:* {meta['sender']}\n*Subject:* {meta['subject']}"
                        }
                    }
                ]
            )
            # Remove from cache
            del self.pending_actions[ts]

        @self.app.action("revise_action")
        def handle_revise_trigger(ack, body, client):
            ack()
            ts = body["message"]["ts"]
            trigger_id = body["trigger_id"]
            
            if ts not in self.pending_actions:
                return
            
            pending = self.pending_actions[ts]
            
            # Open a modal dialog to receive user revision feedback
            client.views_open(
                trigger_id=trigger_id,
                view={
                    "type": "modal",
                    "callback_id": "revise_modal",
                    "private_metadata": json.dumps({"ts": ts}),
                    "title": {"type": "plain_text", "text": "Revise Email Draft"},
                    "submit": {"type": "plain_text", "text": "Regenerate Draft"},
                    "close": {"type": "plain_text", "text": "Cancel"},
                    "blocks": [
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"*Current Draft:*\n```\n{pending['draft']}\n```"
                            }
                        },
                        {
                            "type": "input",
                            "block_id": "feedback_block",
                            "element": {
                                "type": "plain_text_input",
                                "action_id": "feedback_input",
                                "multiline": True,
                                "placeholder": {
                                    "type": "plain_text",
                                    "text": "e.g., Make it sound more enthusiastic, add that I am busy on Tuesday but free on Friday."
                                }
                            },
                            "label": {"type": "plain_text", "text": "What would you like to change?"}
                        }
                    ]
                }
            )

        @self.app.view("revise_modal")
        def handle_modal_submission(ack, body, client):
            ack()
            metadata = json.loads(body["view"]["private_metadata"])
            ts = metadata["ts"]
            
            feedback = body["view"]["state"]["values"]["feedback_block"]["feedback_input"]["value"]
            
            if ts not in self.pending_actions or not self.agent_engine:
                return
            
            pending = self.pending_actions[ts]
            meta = pending['email_meta']
            current_draft = pending['draft']
            triage = pending['triage']
            
            # Use LLM to revise draft
            new_draft = self.agent_engine.revise_draft(
                original_body=meta['body'],
                current_draft=current_draft,
                feedback=feedback
            )
            
            # Update cache
            self.pending_actions[ts]['draft'] = new_draft
            
            # Reconstruct the Slack message blocks
            urgency_indicator = "🔴 *HIGH*" if triage.urgency == "high" else "🟡 *MEDIUM*" if triage.urgency == "medium" else "🟢 *LOW*"
            
            updated_blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "📬 New Email Received (Draft Revised)"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*From:*\n{meta['sender']}"},
                        {"type": "mrkdwn", "text": f"*Subject:*\n{meta['subject']}"}
                    ]
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Urgency:*\n{urgency_indicator}"},
                        {"type": "mrkdwn", "text": f"*AI Summary:*\n{triage.summary}"}
                    ]
                },
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Proposed Response Draft (Revised):*\n```\n{new_draft}\n```"
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {"type": "mrkdwn", "text": f"_Last edit feedback: {feedback}_"}
                    ]
                },
                {
                    "type": "actions",
                    "block_id": "email_actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "🚀 Approve & Send"},
                            "style": "primary",
                            "action_id": "approve_action",
                            "value": meta['id']
                        },
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "✍️ Revise Draft"},
                            "action_id": "revise_action",
                            "value": meta['id']
                        },
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "🗑️ Discard"},
                            "style": "danger",
                            "action_id": "discard_action",
                            "value": meta['id']
                        }
                    ]
                }
            ]
            
            # Update the original Slack notification message with the new blocks
            client.chat_update(
                channel=config.SLACK_CHANNEL_ID,
                ts=ts,
                text=f"New email draft revised for {meta['sender']}",
                blocks=updated_blocks
            )
            print(f"[Slack] Updated message {ts} with revised draft.")