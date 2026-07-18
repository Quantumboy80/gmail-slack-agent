# ⚡ Slack-Gmail Agentic AI Copilot

<div align="center">

  ![Python](https://img.shields.io/badge/python-v3.10+-blue?style=for-the-badge&logo=python&logoColor=white)
  ![Gemini](https://img.shields.io/badge/Gemini%20AI-2.0%20Flash--Lite-orange?style=for-the-badge&logo=google-gemini&logoColor=white)
  ![Slack](https://img.shields.io/badge/Slack-Bolt%20SDK-green?style=for-the-badge&logo=slack&logoColor=white)
  ![Gmail](https://img.shields.io/badge/Gmail%20API-Integration-red?style=for-the-badge&logo=gmail&logoColor=white)
  ![License](https://img.shields.io/badge/license-MIT-brightgreen?style=for-the-badge)

  <p align="center">
    An autonomous agentic AI copilot that triages your Gmail inbox, generates contextual drafts using Gemini 2.0, and puts control directly in your Slack workspace.
  </p>
</div>

---

## 🤖 The Agentic Workflow (System Design)

This app functions as a **reactive agent loop** with **Human-in-the-Loop (HITL)** safeguards. The agent autonomously classifies, decides, and drafts responses, but delegates the final execution (sending) to you via Slack interactive block actions.

```mermaid
sequenceDiagram
    autonumber
    actor User as User (Slack)
    participant SlackApp as Slack Bot (Socket Mode)
    participant Main as Main Loop (Orchestrator)
    participant Gmail as Gmail Client
    participant AI as Gemini 2.0 (Agent Engine)

    loop Polling (Every 60s)
        Main->>Gmail: Poll for unread emails
        Gmail-->>Main: Return new email details
        
        Main->>AI: Send email metadata (Triage & Summarize)
        Note over AI: Triage Prompt + Structured Output Schema
        AI-->>Main: Return Category (Action, Info, Spam), Urgency, Summary
        
        alt is Spam
            Main->>Gmail: Mark as read (skip)
        else is Informational
            Main->>SlackApp: Post FYI Summary Notification
            Main->>Gmail: Mark as read
        else is Action Required
            Main->>AI: Generate Contextual Response Draft
            AI-->>Main: Return proposed drafted response
            Main->>SlackApp: Post interactive Block Notification with Approve/Revise/Discard
            Main->>Gmail: Mark as read (clear from polling queue)
        end
    end

    User->>SlackApp: Click [🚀 Approve & Send]
    SlackApp->>Gmail: Call Gmail API to send email reply
    SlackApp->>User: Update Slack block -> ✅ Sent!

    User->>SlackApp: Click [✍️ Revise Draft]
    SlackApp->>User: Open Slack Modal (Get Feedback)
    User->>SlackApp: Submit Feedback ("make it friendly")
    SlackApp->>AI: Request draft revision (Orig + Old Draft + Feedback)
    AI-->>SlackApp: Return updated draft response
    SlackApp->>User: Update Slack block with new draft
```

---

## 🌟 Key Features

*   🧠 **Structured Triage**: Utilizes Pydantic schemas and Gemini Structured Outputs to classify email intent with near-perfect consistency.
*   💬 **Human-in-the-Loop Revision**: Don't like the draft? Click `Revise Draft` to open a Slack Modal, type what you want to change, and the agent regenerates the draft.
*   ⚡ **Zero-Tunneling Socket Mode**: Running locally over WebSockets. No `ngrok` or port-forwarding required.
*   ⏱️ **Built-in Rate-Limiting**: Polling runs on a controlled delay system to respect free-tier Gemini API limitations.

---

## 📁 Directory Structure

```
gmail-slack-agent/
├── .env.example              # Template config with placeholders
├── .gitignore                # File to exclude sensitive data from GitHub
├── requirements.txt          # Third-party library list
├── config.py                 # Configuration loader with force-override support
├── main.py                   # Main loop orchestrator with rate-limit sleep controls
├── README.md                 # Project guide (this file)
├── integrations/
│   ├── gmail_client.py       # Handles local OAuth flow, reads unread mail, writes replies
│   └── slack_client.py       # Handles Socket Mode, interactive button clicks, and revision modals
├── agent/
│   ├── templates.py          # Structured triage & draft prompt templates
│   └── engine.py             # Interfaces with Gemini using structured outputs
└── tests/
    ├── __init__.py
    ├── test_agent.py         # Mock tests for AgentEngine offline execution
    └── test_gmail.py         # Mock tests for Gmail parser and decoder logic
```

---

## 🔑 Setup & Configuration

### 1. Slack App Configuration (Socket Mode)
1.  Go to the [Slack App Console](https://api.slack.com/apps) -> **Create New App** -> **From Scratch**.
2.  **Enable Socket Mode**: Go to **Socket Mode** in the sidebar, toggle it **On**, and generate an App Token (add scope `connections:write`). Copy the token (starts with `xapp-...`). This is your `SLACK_APP_TOKEN`.
3.  **Add Scopes & Permissions**: Under **OAuth & Permissions** -> **Bot Token Scopes**, add:
    *   `chat:write` (Allows the bot to post messages)
    *   `chat:write.public` (Allows posting to public channels without joining)
4.  Click **Install to Workspace** and copy the **Bot User OAuth Token** (starts with `xoxb-...`). This is your `SLACK_BOT_TOKEN`.
5.  Under **Basic Information**, copy the **Signing Secret** (`SLACK_SIGNING_SECRET`).
6.  Go to **Interactivity & Shortcuts** in the sidebar and toggle it **On** (Socket Mode handles routing, so you don't need a Request URL). Click **Save Changes**.

### 2. Google Cloud / Gmail API Configuration
1.  Go to the [Google Cloud Console](https://console.cloud.google.com/).
2.  Create a new project.
3.  Search for **Gmail API** in the library search bar and click **Enable**.
4.  **Configure OAuth Consent Screen**:
    *   Go to **OAuth consent screen** -> Choose **External** -> Click **Create**.
    *   Fill in basic info (App name, support email, developer email).
    *   In **Scopes**, click **Add or Remove Scopes** and manually enter:
        *   `https://www.googleapis.com/auth/gmail.readonly`
        *   `https://www.googleapis.com/auth/gmail.compose`
        *   `https://www.googleapis.com/auth/gmail.modify`
    *   In **Test Users**, click **Add Users** and add the Gmail address you want to monitor.
5.  **Create Credentials**:
    *   Go to the **Credentials** tab -> Click **+ Create Credentials** -> Select **OAuth client ID**.
    *   Set Application Type to **Desktop app**. Name it `Gmail Slack Agent`.
    *   Click **Create**, then click **Download JSON** on the OAuth client screen.
    *   Rename this downloaded file to `credentials.json` and save it directly in the project root.

### 3. Gemini API Key
*   Obtain a Gemini API key from [Google AI Studio](https://aistudio.google.com/). Select **Create key in new project** to avoid project-level quota policies.

---

## 🚀 Installation & Running

1.  **Clone or Open the Project**:
    ```bash
    cd gmail-slack-agent
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Setup Environment Variables**:
    *   Copy `.env.example` to a new file named `.env`:
    *   Fill in all configuration keys:
    ```env
    GEMINI_API_KEY=AIzaSy...
    SLACK_BOT_TOKEN=xoxb-...
    SLACK_APP_TOKEN=xapp-...
    SLACK_SIGNING_SECRET=...
    SLACK_CHANNEL_ID=C...       # Target channel ID
    POLL_INTERVAL_SECONDS=60
    ```

4.  **Run the Application**:
    ```bash
    python main.py
    ```

5.  **First-time Google Auth**:
    *   On the first run, the terminal will open a browser window requesting Google Account permissions.
    *   Sign in with your registered Gmail test user account.
    *   After approval, a file named `token.json` will be saved locally so you won't need to authenticate again.

---

## 🔄 How to Test
1.  Send an unread test email to yourself from another account.
2.  Watch the Python terminal detect the email.
3.  Go to your Slack channel and view the AI's triage card.
4.  Interact with the buttons to approve, revise, or discard!
