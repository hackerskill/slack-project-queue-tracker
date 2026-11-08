# slack-project-queue-tracker
A slack bot to track number of project in queue

## Description
A Slack Bot which fetches queue from a base url and can be called using both slash command and app mentions. Supports sending notifications to specific channel.

## Features

- **Slack Bot** Integrates into the Slack workspace.
- **Dual Usage Approach** Can be called using both slash command and app mention.
- **Socket Mode** Utilises socket mode to maintain persistent connection.
- **Notifications** Sends notifications when new project is added or queue hits zero.
- **Toggle** Notifications can be toggled using variables for specific operation.
- **Threading** Automatically threads message when app is used using app mention.

## Setup

1. Create a New App on [Slack API Dashboard](https://api.slack.com/apps).

2. Under `OAuth & Permissions`, provide `commands`, `app_mentions:read`, `channels:read`, and `chat:write` Bot Token Scopes.

3. Under `Slash Commands`, create a new command and ensure `Escape channels, users, and links sent to your app` is checked.

4. Install the app from `Install App`

5. Clone the repo

6. **Change `.env.example` to `.env` with the following keys-**
    * Bot User OAuth Token which can be obtained from `OAuth & Permissions`
    * App-Level Tokens which can be obtained from `Basic Information`
    * Base URL
    * Slack Notification Channel ID

7. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### Running the Application

Once setup is verified, `main.py` can be run to start the discord bot.
