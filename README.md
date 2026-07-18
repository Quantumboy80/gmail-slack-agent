# ⚡ Slack-Gmail Agentic AI Copilot

<div align="center">

  <!-- Brand Logos -->
  <p align="center">
    <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/python/python-original.svg" width="45" height="45" alt="Python" />
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
    <img src="assets/gemini.svg" width="45" height="45" alt="Gemini" />
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
    <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/slack/slack-original.svg" width="45" height="45" alt="Slack" />
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
    <img src="https://upload.wikimedia.org/wikipedia/commons/7/7e/Gmail_icon_%282020%29.svg" width="45" height="45" alt="Gmail" />
  </p>

  <!-- Solid Brand Badges -->
  <p align="center">
    <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white" /></a>
    &nbsp;
    <a href="https://ai.google.dev"><img src="https://img.shields.io/badge/Gemini%202.0-Flash--Lite-8E75C2?style=flat-square&logo=googlegemini&logoColor=white" /></a>
    &nbsp;
    <a href="https://api.slack.com"><img src="https://img.shields.io/badge/Slack%20Bolt-v1.18-4A154B?style=flat-square&logo=slack&logoColor=white" /></a>
    &nbsp;
    <a href="https://developers.google.com/gmail/api"><img src="https://img.shields.io/badge/Gmail%20API-Integration-D14836?style=flat-square&logo=gmail&logoColor=white" /></a>
  </p>

  <p align="center">
    <b>An autonomous agentic AI copilot that triages your Gmail inbox, generates contextual drafts using Gemini 2.0, and puts control directly in your Slack workspace.</b>
  </p>
</div>

---

## 🎨 System Architecture Design (Excalidraw Style)

Here is a visual layout of the components interacting across Gmail, Google Gemini, and Slack:

<div align="center">
  <img src="assets/architecture_diagram.png" width="85%" alt="Slack Gmail AI Copilot System Architecture Design" />
</div>

---

## 📐 Decision Flowchart & Agentic Logic

The orchestrator polling loop queries Gmail, passes email data to the Gemini engine with **Structured Outputs** (enforced by Pydantic), triages the intent, and maps appropriate action vectors.

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

## 🔄 Interaction Sequence (Socket Mode Routing)

This diagram shows the complete sequence of message routing, API calls, and the **Human-in-the-Loop (HITL)** revision loop:

```mermaid
sequenceDiagram
    autonumber
    actor User as User (Slack)
    participant SlackApp as Slack Bot (Socket Mode)
    participant Main as Main Loop (Orchestrator)
    participant Gmail as Gmail Client
    participant AI as Gemini 2.0 (Agent Engine)

    loop Polling (Every 60s)
        Main->{{"Gmail"}}: Poll for unread emails
        Gmail-->>Main: Return new email details
        
        Main->>{{"Gemini"}}: Send email metadata (Triage & Summarize)
        Note over AI: Triage Prompt + Structured Output Schema
        AI-->>Main: Return Category (Action, Info, Spam), Urgency, Summary
        
        alt is Spam
            Main->>{{"Gmail"}}: Mark as read (skip)
        else is Informational
            Main->>{{"Slack"}}: Post FYI Summary Notification
            Main->>{{"Gmail"}}: Mark as read
        else is Action Required
            Main->>{{"Gemini"}}: Generate Contextual Response Draft
            AI-->>Main: Return proposed drafted response
            Main->>{{"Slack"}}: Post Interactive Notification with Buttons
            Main->>{{"Gmail"}}: Mark as read (clear from queue)
        end
    end

    User->>{{"Slack"}}: Click [🚀 Approve & Send]
    SlackApp->>{{"Gmail"}}: Call Gmail API to send email reply
    SlackApp->>User: Update Slack block -> ✅ Sent!

    User->>{{"Slack"}}: Click [✍️ Revise Draft]
    SlackApp->>User: Open Slack Modal (Get Feedback)
    User->>{{"Slack"}}: Submit Feedback ("make it friendly")
    SlackApp->>{{"Gemini"}}: Request draft revision (Orig + Old Draft + Feedback)
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
├── assets/
│   └── architecture_diagram.png # Hand-drawn Excalidraw design diagram
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
