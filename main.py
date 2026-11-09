import os
import requests
import time
from datetime import datetime
import logging
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

load_dotenv()

app_token=os.environ.get("SLACK_APP_TOKEN")
bot_token=os.environ.get("SLACK_BOT_TOKEN")
base_url=os.environ.get("BASE_URL")
endpoint=f"{base_url}/queue/"
channel_id=os.environ.get("SLACK_NOTIFICATION_CHANNEL_ID")

old_projects=None
new_project_notifications=True
queue_empty_notifications=True

app=App(token=bot_token)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

def new_project_update(total_projects, project_t1, project_t2, logger):
    global old_projects

    if old_projects is None:
        old_projects = total_projects
        logger.info(f"Initialized baseline old_projects to {total_projects}")
        return

    if new_project_notifications:
        if total_projects>old_projects:
            logger.info(f"New project detected. Total projects: {total_projects}, Old projects: {old_projects}")
            app.client.chat_postMessage(
            channel=channel_id,
            text=f"🚨 New project added! Total projects increased to {total_projects}\n*Updated Queue Status:*\nProject T1: *{project_t1}*\nProject T2: *{project_t2}*")
        else:
            logger.info(f"No new project detected. Total projects: {total_projects}, Old projects: {old_projects}")
    old_projects=total_projects

    if queue_empty_notifications:
        if project_t1==0:
            logger.info(f"Project T1 is empty.")
            app.client.chat_postMessage(
            channel=channel_id,
            text=f"🚨 Project T1 queue is empty!\n*Updated Queue Status:*\nTotal projects: *{total_projects}*\nProject T1: *{project_t1}*\nProject T2: *{project_t2}*")
        if project_t2==0:
            logger.info(f"Project T2 is empty.")
            app.client.chat_postMessage(
            channel=channel_id,
            text=f"🚨 Project T2 queue is empty!\n*Updated Queue Status:*\nTotal projects: *{total_projects}*\nProject T1: *{project_t1}*\nProject T2: *{project_t2}*")

@app.command("/queue")
def handle_some_command(ack, respond, command, logger):
    ack()

    logger.info(f"Queue called by {command['user_name']}({command['user_id']}) in channel {command['channel_name']}({command['channel_id']}) using command {command['command']}")
    max_attempts=3
    for attempt in range(max_attempts):
        try:
            response=requests.get(f"{endpoint}", timeout=5)
            if response.status_code==429:
                logger.warning(f"Rate limited (429). Attempt {attempt + 1}/{max_attempts}.")
                retry_after=int(response.headers.get("Retry-After", 1))
                respond(f"Too many requests: {response.json()}, retrying in {retry_after} seconds...")
                time.sleep(retry_after)
                continue
            else:
                break
        except requests.exceptions.RequestException as e:
            logger.exception(f"Request failed on attempt {attempt + 1}: {e}.")

            if attempt < max_attempts - 1:
                time.sleep(1)
                continue
            else:
                respond(f"Request failed: {e}, try again later.")
                return

    if response:
        if response.status_code==200:
            data=response.json()
            status=data.get("status", "")
            total_projects=data.get("total_projects", "")
            project_t1=data.get("project_t1", "")
            project_t2=data.get("project_t2", "")
            oldest_hours=(data.get("oldest_hours", ""))//24
            timestamp=data.get("timestamp", "")

            timestamp_time=datetime.fromisoformat(timestamp.replace("Z", "+00:00")) if timestamp else None
            final_timestamp_time=timestamp_time.strftime("%B %d, %Y at %I:%M %p") if timestamp_time else "N/A"

            if status=="success":
                respond(f"Total projects: *{total_projects}*\nProject T1: *{project_t1}*\nProject T2: *{project_t2}*\nOldest: *{oldest_hours} days*\nTimestamp: *{final_timestamp_time}*\n")
            else:
                respond("Error Occured")

        elif response.status_code==400:
            respond(f"Bad request: {response.json()}")
        else:
            respond(f"Unexpected error: {response.status_code}, {response.json()}")

    new_project_update(total_projects, project_t1, project_t2, logger)

@app.event("app_mention")
def handle_bot_ping(event, say, logger):
    logger.info(f"Queue called by {event["user"]} in channel {event['channel']} using app mention")

    thread_timestamp = event.get("ts")
    max_attempts=3
    for attempt in range(max_attempts):
        try:
            response=requests.get(f"{endpoint}", timeout=5)
            if response.status_code==429:
                logger.warning(f"Rate limited (429). Attempt {attempt + 1}/{max_attempts}.")
                retry_after=int(response.headers.get("Retry-After", 1))
                say(f"Too many requests: {response.json()}, retrying in {retry_after} seconds...")
                time.sleep(retry_after)
                continue
            else:
                break
        except requests.exceptions.RequestException as e:
            logger.exception(f"Request failed on attempt {attempt + 1}: {e}.")

            if attempt < max_attempts - 1:
                time.sleep(1)
                continue
            else:
                say(f"Request failed: {e}, try again later.")
                return

    if response:
        if response.status_code==200:
            data=response.json()
            status=data.get("status", "")
            total_projects=data.get("total_projects", "")
            project_t1=data.get("project_t1", "")
            project_t2=data.get("project_t2", "")
            oldest_hours=(data.get("oldest_hours", ""))//24
            timestamp=data.get("timestamp", "")

            timestamp_time=datetime.fromisoformat(timestamp.replace("Z", "+00:00")) if timestamp else None
            final_timestamp_time=timestamp_time.strftime("%B %d, %Y at %I:%M %p") if timestamp_time else "N/A"

            if status=="success":
                say(f"Total projects: *{total_projects}*\nProject T1: *{project_t1}*\nProject T2: *{project_t2}*\nOldest: *{oldest_hours} days*\nTimestamp: *{final_timestamp_time}*\n", thread_ts=thread_timestamp)
            else:
                say("Error Occured")

        elif response.status_code==400:
            say(f"Bad request: {response.json()}")
        else:
            say(f"Unexpected error: {response.status_code}, {response.json()}")

    new_project_update(total_projects, project_t1, project_t2, logger)

if __name__ == "__main__":
    SocketModeHandler(app, app_token).start()
