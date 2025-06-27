from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime
import os

SCOPES = ['https://www.googleapis.com/auth/calendar']

# ✅ Use token from session/env (NOT local file)
def get_calendar_service(token_dict: dict):
    try:
        creds = Credentials.from_authorized_user_info(token_dict, SCOPES)
        service = build('calendar', 'v3', credentials=creds)
        return service
    except Exception as e:
        print("❌ Failed to create calendar service:", e)
        return None

# ✅ Check slot availability
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

# ✅ Book calendar slot
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
