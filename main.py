import os
import requests
import time
from datetime import datetime
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

load_dotenv()

app_token=os.environ.get("SLACK_APP_TOKEN")
bot_token=os.environ.get("SLACK_BOT_TOKEN")
base_url=os.environ.get("BASE_URL")
endpoint=f"{base_url}/queue/"

app=App(token=bot_token)

@app.command("/queue")
def handle_some_command(ack, respond, command, logger):
    ack()

    logger.info(f"Queue called by {command['user_name']}({command['user_id']}) in channel {command['channel_name']}({command['channel_id']})")

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
                respond(f"Total projects: *{total_projects}*\nProject T1: *{project_t1}*\nProject T2: *{project_t2}*\nOldest: *{oldest_hours}* days\nTimestamp: *{final_timestamp_time}*\n")
            else:
                respond("Error Occured")

        elif response.status_code==400:
            respond(f"Bad request: {response.json()}")
        else:
            respond(f"Unexpected error: {response.status_code}, {response.json()}")

if __name__ == "__main__":
    SocketModeHandler(app, app_token).start()
