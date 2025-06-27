from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime
import os
import json

SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_calendar_service():
    """
    Returns an authenticated Google Calendar service.
    Requires token.json to exist (created after OAuth via /oauth2callback).
    """
    if not os.path.exists("token.json"):
        raise Exception("🔐 Not authorized. Please visit /authorize to login.")

    try:
        with open("token.json", "r") as f:
            creds_data = json.load(f)
        creds = Credentials.from_authorized_user_info(info=creds_data, scopes=SCOPES)

        if not creds.valid and creds.expired and creds.refresh_token:
            from google.auth.transport.requests import Request
            creds.refresh(Request())
            with open("token.json", "w") as token:
                token.write(creds.to_json())

        service = build("calendar", "v3", credentials=creds)
        return service

    except Exception as e:
        raise Exception(f"❌ Failed to load Google credentials: {e}")


def check_availability(service, start_time, end_time):
    try:
        print("🔎 Checking availability from:", start_time, "to", end_time)
        events_result = service.events().list(
            calendarId='primary',
            timeMin=start_time,
            timeMax=end_time,
            singleEvents=True,
            orderBy='startTime',
            timeZone='Asia/Kolkata'
        ).execute()

        events = events_result.get('items', [])
        print(f"📅 Found {len(events)} events in that range.")
        return len(events) == 0
    except Exception as e:
        print("❌ Error while checking availability:", e)
        return False


def book_slot(service, summary, start_time, end_time):
    event = {
        'summary': summary,
        'start': {
            'dateTime': start_time,
            'timeZone': 'Asia/Kolkata'
        },
        'end': {
            'dateTime': end_time,
            'timeZone': 'Asia/Kolkata'
        }
    }

    try:
        print("📤 Booking event from:", start_time, "to", end_time)
        event = service.events().insert(calendarId='primary', body=event).execute()
        print("✅ Event created:", event.get('htmlLink'))
        return event
    except Exception as e:
        print("❌ Failed to create event:", e)
        return {"htmlLink": "❌ Booking failed, check terminal"}
