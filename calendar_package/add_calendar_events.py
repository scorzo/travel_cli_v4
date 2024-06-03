from datetime import datetime
from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import BaseTool
from typing import Optional, Type
import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)

SCOPES = ['https://www.googleapis.com/auth/calendar']
CREDENTIALS_FILE = 'client_secret.json'
CALENDAR_ID = 'primary'

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

class AddEventInput(BaseModel):
    event_summary: str = Field(description="Summary of the event")
    event_location: str = Field(description="Location of the event")
    event_description: str = Field(description="Description of the event")
    start_time: str = Field(description="Start time of the event in ISO 8601 format")
    end_time: str = Field(description="End time of the event in ISO 8601 format")
    start_time_zone: str = Field(description="Time zone of the start time")
    end_time_zone: str = Field(description="Time zone of the end time")

class AddCalendarEventTool(BaseTool):
    name = "add_calendar_event"
    description = "Add an event to Google Calendar"
    args_schema: Type[BaseModel] = AddEventInput

    def _run(
            self, event_summary: str, event_location: str, event_description: str, start_time: str, end_time: str, start_time_zone: str, end_time_zone: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool."""
        return self.add_calendar_event(event_summary, event_location, event_description, start_time, end_time, start_time_zone, end_time_zone)

    async def _arun(
            self, event_summary: str, event_location: str, event_description: str, start_time: str, end_time: str, start_time_zone: str, end_time_zone: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("add_calendar_event does not support async")

    def add_calendar_event(self, event_summary: str, event_location: str, event_description: str, start_time: str, end_time: str, start_time_zone: str, end_time_zone: str) -> str:
        event = {
            'summary': event_summary,
            'location': event_location,
            'description': event_description,
            'start': {
                'dateTime': start_time,
                'timeZone': start_time_zone,
            },
            'end': {
                'dateTime': end_time,
                'timeZone': end_time_zone,
            },
        }
        try:
            print(f"Created event '{event_summary}' at '{event_location}' starting from {start_time} to {end_time} in time zone {start_time_zone}.")
            event_result = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
            return f"Event created: {event_result.get('htmlLink')}"
        except Exception as e:
            return f"An error occurred: {e}"

# Example usage
if __name__ == "__main__":
    tool = AddCalendarEventTool()
    print(tool._run(event_summary="Test Event", event_location="Test Location", event_description="Test Description", start_time="2024-06-01T10:00:00", end_time="2024-06-01T11:00:00", start_time_zone="America/Los_Angeles", end_time_zone="America/Los_Angeles"))
