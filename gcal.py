# gcal.py

import os
from datetime import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

# Required calendar access scope
SCOPES = ['https://www.googleapis.com/auth/calendar']

# Paths to secret files in Render
TOKEN_PATH = '/etc/secrets/token.json'
CREDENTIALS_PATH = '/etc/secrets/credentials.json'

def get_calendar_service():
    """
    Initializes and returns a Google Calendar API service object.
    Uses token.json and credentials.json stored securely in /etc/secrets/.
    """
    creds = None

    # Load token if it exists
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    # If token is missing or expired
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                # ❌ Do NOT write token.json back — /etc/secrets is read-only
            except Exception as e:
                print("❌ Failed to refresh credentials:", e)
                raise RuntimeError("Token refresh failed")
        else:
            raise RuntimeError("Missing or invalid credentials. Run locally once to generate token.json.")

    # Build and return the calendar service
    try:
        service = build('calendar', 'v3', credentials=creds)
        return service
    except Exception as e:
        print("❌ Failed to initialize Calendar service:", e)
        raise

def check_availability(service, start_time, end_time):
    """
    Checks if a calendar slot is free.
    Assumes start_time and end_time are ISO-8601 strings with timezone info.
    """
    try:
        print("🔎 Checking availability from:", start_time, "to", end_time)
        events_result = service.events().list(
            calendarId='primary',
            timeMin=start_time,
            timeMax=end_time,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])
        print(f"📅 Found {len(events)} events in that range.")
        return len(events) == 0
    except Exception as e:
        print("❌ Error while checking availability:", e)
        return False

def book_slot(service, summary, start_time, end_time):
    """
    Creates a new event in the user's calendar.
    Times must be ISO-8601 strings with timezone info.
    """
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
