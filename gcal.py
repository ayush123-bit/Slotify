from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime
import os

SCOPES = ['https://www.googleapis.com/auth/calendar']

# For demo purposes: memory storage (replace with DB/session in production)
user_token_store = {}

def set_user_token(user_id, credentials_dict):
    user_token_store[user_id] = credentials_dict

def get_calendar_service(user_id):
    if user_id not in user_token_store:
        raise Exception("🔐 Not authorized. Please visit /authorize to login.")

    creds = Credentials.from_authorized_user_info(user_token_store[user_id], SCOPES)
    service = build('calendar', 'v3', credentials=creds)
    return service

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
        'start': {'dateTime': start_time, 'timeZone': 'Asia/Kolkata'},
        'end': {'dateTime': end_time, 'timeZone': 'Asia/Kolkata'}
    }

    try:
        print("📤 Booking event from:", start_time, "to", end_time)
        event = service.events().insert(calendarId='primary', body=event).execute()
        print("✅ Event created:", event.get('htmlLink'))
        return event
    except Exception as e:
        print("❌ Failed to create event:", e)
        return {"htmlLink": "❌ Booking failed, check terminal"}
