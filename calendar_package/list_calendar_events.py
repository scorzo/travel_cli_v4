from datetime import datetime, timedelta
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

def format_event_time(event_time_str, timezone_str):
    event_time = datetime.fromisoformat(event_time_str)
    timezone = pytz.timezone(timezone_str)
    event_time = event_time.astimezone(timezone)
    return event_time.strftime('%A, %B %d at %I:%M%p') + f" ({timezone_str})"

class ListEventsInput(BaseModel):
    calendar_id: str = Field(default='primary', description="ID of the calendar to list events from")
    max_results: int = Field(default=10, description="Maximum number of events to list")
    start_time: Optional[str] = Field(default=None, description="Start time in ISO 8601 format")
    end_time: Optional[str] = Field(default=None, description="End time in ISO 8601 format")
    timezone: str = Field(default='UTC', description="Timezone for the events")

class ListEventsTool(BaseTool):
    name = "list_events"
    description = "List events from Google Calendar within a specified time range and timezone"
    args_schema: Type[BaseModel] = ListEventsInput

    def _run(
            self, calendar_id: str = 'primary', max_results: int = 20, start_time: Optional[str] = None, end_time: Optional[str] = None, timezone: str = 'UTC', run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool."""
        return self.list_events(calendar_id, max_results, start_time, end_time, timezone)

    async def _arun(
            self, calendar_id: str = 'primary', max_results: int = 20, start_time: Optional[str] = None, end_time: Optional[str] = None, timezone: str = 'UTC', run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("list_events does not support async")

    def list_events(self, calendar_id: str, max_results: int, start_time: Optional[str], end_time: Optional[str], timezone: str) -> str:

        # hard code max results at 20 for now
        max_results = 20

        tz = pytz.timezone(timezone)

        if start_time is None:
            start_time = datetime.now(tz).isoformat()
        else:
            try:
                start_time = datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%S%z').isoformat()
            except ValueError:
                start_time = datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%S').replace(tzinfo=tz).isoformat()

        if end_time is None:
            end_time = (datetime.now(tz) + timedelta(days=7)).isoformat()
        else:
            try:
                end_time = datetime.strptime(end_time, '%Y-%m-%dT%H:%M:%S%z').isoformat()
            except ValueError:
                end_time = datetime.strptime(end_time, '%Y-%m-%dT%H:%M:%S').replace(tzinfo=tz).isoformat()


        print(colored(f"Querying Google Calendar API for events in calendar '{calendar_id}' from '{start_time}' to '{end_time}' with a maximum of {max_results} results in timezone '{timezone}'.", "white", "on_grey"))

        try:
            events_result = service.events().list(calendarId=calendar_id, timeMin=start_time, timeMax=end_time,
                                                  maxResults=max_results, singleEvents=True,
                                                  orderBy='startTime').execute()
            events = events_result.get('items', [])
            if not events:
                return 'No events found in that time span.'

            event_details = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))

                start_formatted = format_event_time(start, event['start'].get('timeZone', timezone))
                end_formatted = format_event_time(end, event['end'].get('timeZone', timezone))
                summary = event.get('summary', 'No Title')  # Use 'No Title' if summary is not present
                print(colored(f"{start_formatted} to {end_formatted} - {summary}", "white", "on_grey"))

                event_detail = {
                    "start": start,
                    "end": end,
                    "summary": summary,
                    "start_formatted": start_formatted,
                    "end_formatted": end_formatted
                }
                event_details.append(event_detail)

            return event_details

        except Exception as e:
            print(f"An error occurred: {str(e)}")
            traceback.print_exc()
            sys.exit(0)

# Example usage
if __name__ == "__main__":
    tool = ListEventsTool()
    print(tool._run())
