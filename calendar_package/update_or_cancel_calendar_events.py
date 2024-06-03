from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import BaseTool
from typing import Optional, Type, Dict, Any
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

class UpdateOrCancelEventInput(BaseModel):
    calendar_id: str = Field(default='primary', description="ID of the calendar")
    event_id: str = Field(description="ID of the event to update or cancel")
    update_body: Optional[Dict[str, Any]] = Field(default=None, description="Body of the event update")

class UpdateOrCancelEventTool(BaseTool):
    name = "update_or_cancel_event"
    description = "Update or cancel an event in Google Calendar"
    args_schema: Type[BaseModel] = UpdateOrCancelEventInput

    def _run(
            self, calendar_id: str = 'primary', event_id: str = None, update_body: Optional[Dict[str, Any]] = None, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool."""
        return self.update_or_cancel_event(calendar_id, event_id, update_body)

    async def _arun(
            self, calendar_id: str = 'primary', event_id: str = None, update_body: Optional[Dict[str, Any]] = None, run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("update_or_cancel_event does not support async")

    def update_or_cancel_event(self, calendar_id: str, event_id: str, update_body: Optional[Dict[str, Any]]) -> str:
        if update_body:
            try:
                updated_event = service.events().update(calendarId=calendar_id, eventId=event_id, body=update_body).execute()
                return f"Event updated: {updated_event.get('htmlLink')}"
            except Exception as e:
                return f"An error occurred: {e}"
        else:
            try:
                service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
                return 'Event deleted.'
            except Exception as e:
                return f"An error occurred: {e}"

# Example usage
if __name__ == "__main__":
    tool = UpdateOrCancelEventTool()
    print(tool._run(calendar_id="primary", event_id="EVENT_ID", update_body={"summary": "Updated Event"}))
