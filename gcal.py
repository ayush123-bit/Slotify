from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from datetime import datetime
import os

SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_calendar_service():
    creds = None

    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Load from environment variables instead of credentials.json
            flow = InstalledAppFlow.from_client_config(
                {
                    "installed": {
                        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [os.getenv("OAUTH_REDIRECT_URI")]
                    }
                },
                scopes=SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save token for reuse
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return build('calendar', 'v3', credentials=creds)

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
