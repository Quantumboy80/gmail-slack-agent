# Slack-Gmail Agentic AI System

This project is an agentic AI system that monitors your Gmail inbox for new unread messages, uses Gemini 2.0 to summarize and triage them, drafts replies, and posts them as interactive notifications to a Slack channel. You can approve and send the draft, request revisions, or discard the triage directly from Slack.

---

## 📐 Architecture & Decision Flow

The system runs a polling loop that queries Gmail, uses Gemini with **Structured Outputs** to categorize the mail, and posts alerts to Slack via **Socket Mode** for interactive control.

```mermaid
graph TD
    A[New Email Received] -->|Gmail Polling| B(AI Agent Engine)
    B -->|Analyze Context & Goal| C{Categorize Email}
    
    C -->|Low Priority / Spam| D[Auto-Archive / Mark Read]
    C -->|Action Required| E[Generate Reply Draft]
    C -->|Informational| H[Post Summary Alert to Slack]
    
    E --> F[Send Slack Notification with Draft & Interactive Buttons]
    F -->|User clicks 'Approve'| G[Gmail API: Send Email]
    F -->|User clicks 'Edit'| I[Slack Modal: Input customized edits] --> J[Regenerate Draft] --> F
    F -->|User clicks 'Discard'| K[Ignore / Keep Read]
```

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

## 🛠️ Tech Stack & Prerequisites

*   **Language**: Python 3.10+
*   **APIs**: Google Gemini API, Gmail API, Slack Bolt API (Socket Mode)
*   **Key Libraries**: `google-genai`, `slack-bolt`, `google-api-python-client`, `pydantic`

---

## 🔑 Setup & Configuration

### 1. Slack App Configuration (Socket Mode)
1.  Go to the [Slack App Console](https://api.slack.com/apps) and click **Create New App** -> **From Scratch**. Name your app (e.g., `Gmail AI Agent`) and choose your workspace.
2.  **Enable Socket Mode**:
    *   Navigate to **Socket Mode** in the left sidebar and toggle it **On**.
    *   It will ask you to generate an **App-Level Token**. Set the name (e.g., `AppToken`) and add the `connections:write` scope.
    *   Copy the token (starts with `xapp-...`). This is your `SLACK_APP_TOKEN`.
3.  **Add Scopes & Permissions**:
    *   Navigate to **OAuth & Permissions** in the sidebar.
    *   Scroll down to **Scopes** -> **Bot Token Scopes** and add:
        *   `chat:write` (Allows the bot to post messages)
        *   `chat:write.public` (Allows posting to public channels without joining)
    *   Scroll up and click **Install to Workspace**. Authorize the app.
    *   Copy the **Bot User OAuth Token** (starts with `xoxb-...`). This is your `SLACK_BOT_TOKEN`.
4.  **Get Signing Secret**:
    *   Go to **Basic Information** and find the **Signing Secret** under "App Credentials". Copy this as `SLACK_SIGNING_SECRET`.
5.  **Enable Interactivity**:
    *   Go to **Interactivity & Shortcuts** in the sidebar and toggle it **On**. (You don't need a Request URL since Socket Mode handles events). Click **Save Changes**.

---

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

---

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
