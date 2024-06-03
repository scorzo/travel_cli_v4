from datetime import datetime, timedelta, timezone
from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import BaseTool
from typing import Optional, Type
import pytz
import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import sys
import traceback
import json
from termcolor import colored

from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)

SCOPES = ['https://www.googleapis.com/auth/calendar']
CREDENTIALS_FILE = 'client_secret.json'

def get_calendar_service():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    service = build('calendar', 'v3', credentials=creds)
    return service

service = get_calendar_service()

class FreeBusyInput(BaseModel):
    calendar_id: str = Field(default='primary', description="ID of the calendar to check for free/busy times")
    start_time: Optional[str] = Field(default=None, description="Start time in ISO 8601 format")
    end_time: Optional[str] = Field(default=None, description="End time in ISO 8601 format")
    timezone: str = Field(default='UTC', description="Timezone for the query")

class FreeBusyTool(BaseTool):
    name = "free_busy"
    description = "Check free/busy times from Google Calendar within a specified time range and timezone"
    args_schema: Type[BaseModel] = FreeBusyInput

    def _run(
            self, calendar_id: str = 'primary', start_time: Optional[str] = None, end_time: Optional[str] = None, timezone: str = 'UTC', run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool."""
        return self.check_free_busy(calendar_id, start_time, end_time, timezone)

    async def _arun(
            self, calendar_id: str = 'primary', start_time: Optional[str] = None, end_time: Optional[str] = None, timezone: str = 'UTC', run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("free_busy does not support async")

    def check_free_busy(self, calendar_id: str, start_time: Optional[str], end_time: Optional[str], timezone: str) -> str:
        tz = pytz.timezone(timezone)

        if start_time is None:
            start_time = datetime.now(tz).isoformat()
        else:
            try:
                start_time = datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%S%z').isoformat()
            except ValueError:
                start_time = datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%S').replace(tzinfo=tz).isoformat()

        if end_time is None:
            end_time = (datetime.now(tz) + timedelta(days=90)).isoformat()
        else:
            try:
                end_time = datetime.strptime(end_time, '%Y-%m-%dT%H:%M:%S%z').isoformat()
            except ValueError:
                end_time = datetime.strptime(end_time, '%Y-%m-%dT%H:%M:%S').replace(tzinfo=tz).isoformat()

        print(colored(f"Querying Google Calendar API for free/busy times in calendar '{calendar_id}' from '{start_time}' to '{end_time}' in timezone '{timezone}'.", "white", "on_grey"))

        try:
            request_body = {
                "timeMin": start_time,
                "timeMax": end_time,
                "timeZone": timezone,
                "items": [{"id": calendar_id}]
            }

            freebusy_result = service.freebusy().query(body=request_body).execute()

            busy_times = freebusy_result['calendars'][calendar_id]['busy']

            if not busy_times:
                return 'No busy times found in that time span.'

            free_times = []
            current_time = datetime.fromisoformat(start_time)
            end_time_dt = datetime.fromisoformat(end_time)

            print("\nFree times:")
            while current_time < end_time_dt:
                free_slot_start = current_time
                next_busy_time = None
                for busy_time in busy_times:
                    busy_start = datetime.fromisoformat(busy_time['start'])
                    if busy_start > current_time:
                        next_busy_time = busy_start
                        break

                if next_busy_time:
                    free_slot_end = next_busy_time
                else:
                    free_slot_end = end_time_dt

                if free_slot_end > free_slot_start:
                    free_times.append((free_slot_start, free_slot_end))
                    print(f"From {free_slot_start} to {free_slot_end}")

                current_time = free_slot_end

            if not free_times:
                return "No free times found."

            return free_times

        except Exception as e:
            print(f"An error occurred: {str(e)}")
            traceback.print_exc()
            sys.exit(0)

# Example usage
if __name__ == "__main__":
    tool = FreeBusyTool()
    print(tool._run())
