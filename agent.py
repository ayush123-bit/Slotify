# agent.py

import os, json, re
from datetime import datetime, timedelta, date
from dotenv import load_dotenv
from pytz import timezone
from dateparser import parse as parse_date
import google.generativeai as genai
from gcal import get_calendar_service, check_availability, book_slot

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

# Timezone setup
IST = timezone("Asia/Kolkata")
TODAY = datetime.now(IST).date()

# Default mappings for vague time phrases
DEFAULT_TIME_MAP = {
    "morning": "10:00",
    "noon": "12:00",
    "afternoon": "15:00",
    "evening": "18:00",
    "night": "20:00"
}

def parse_json_response(text):
    try:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        return json.loads(match.group()) if match else {}
    except Exception as e:
        print("❌ JSON parsing error:", e)
        return {}

def extract_time_range(user_input, start_dt):
    """Extracts end time if a time range is present in the input."""
    match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(AM|PM|am|pm)?\s*(?:-|to)\s*(\d{1,2})(?::(\d{2}))?\s*(AM|PM|am|pm)?', user_input, re.IGNORECASE)
    if match:
        sh, sm, sap, eh, em, eap = match.groups()
        sh, sm = int(sh), int(sm) if sm else 0
        eh, em = int(eh), int(em) if em else 0

        def to_24h(hour, minute, ampm):
            if ampm:
                ampm = ampm.lower()
                if ampm == "pm" and hour != 12:
                    hour += 12
                elif ampm == "am" and hour == 12:
                    hour = 0
            return hour, minute

        sh, sm = to_24h(sh, sm, sap or eap)
        eh, em = to_24h(eh, em, eap or sap)

        end_dt = start_dt.replace(hour=eh, minute=em)
        if end_dt <= start_dt:
            end_dt = start_dt + timedelta(hours=1)
        return end_dt
    return None

def run_agent(user_input):
    try:
        # Today's date string for context
        today_str = TODAY.strftime("%Y-%m-%d")

        # Prompt to Gemini
        prompt = f"""
You are a smart and precise calendar assistant. Today's date is {today_str}.
Always interpret relative expressions like "tomorrow", "next week", etc. based on this date.

Extract and return the following fields **as a valid JSON object only**:
- "intent": either "book" or "check"
- "date": in YYYY-MM-DD format
- "time": in 24-hour format "HH:MM"
- "reason": short title (e.g., "Team Sync", "Doctor Call")

Rules:
- Default time to "12:00" if not mentioned.
- If time is a range like "3-5 PM", use the start (e.g., "15:00").
- If time is vague like "afternoon", map to "15:00", "evening" → "18:00", etc.
- Return a complete JSON object, no explanation, no markdown.

User: "{user_input}"
"""

        response = model.generate_content(prompt)
        print("🔍 Gemini raw response:", response.text)

        data = parse_json_response(response.text)
        intent = data.get("intent", "book").lower()
        date_str = data.get("date")
        time_str = data.get("time", "12:00")
        reason = data.get("reason", "TailorTalk Appointment")

        # Fallback if Gemini fails
        if not date_str or not time_str:
            dt = parse_date(user_input, settings={
                'PREFER_DATES_FROM': 'future',
                'RELATIVE_BASE': datetime.now(IST),
                'TIMEZONE': 'Asia/Kolkata',
                'RETURN_AS_TIMEZONE_AWARE': True
            })
            if not dt:
                return "❌ Couldn’t extract date or time. Please rephrase."
            dt = dt.replace(minute=0, second=0, microsecond=0)
            start_dt = dt if dt.tzinfo else IST.localize(dt)
        else:
            # Handle vague time expressions
            if time_str == "12:00":
                for keyword, mapped_time in DEFAULT_TIME_MAP.items():
                    if keyword in user_input.lower():
                        time_str = mapped_time
                        break

            try:
                start_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
                start_dt = IST.localize(start_dt.replace(minute=0, second=0, microsecond=0))

                # Gemini bug fix: past year correction
                if start_dt.date() < TODAY:
                    start_dt = start_dt.replace(year=TODAY.year)
            except ValueError:
                return "❌ Invalid date or time format. Please rephrase."

        # ⏱️ Extract actual end time from time range or fallback to 1 hour
        end_dt = extract_time_range(user_input, start_dt) or (start_dt + timedelta(hours=1))

        start_iso = start_dt.isoformat()
        end_iso = end_dt.isoformat()

        print("📅 Final start:", start_iso)
        print("📅 Final end:", end_iso)

        # Google Calendar integration
        service = get_calendar_service()
        is_free = check_availability(service, start_iso, end_iso)

        if intent == "check":
            return "✅ That time slot is available!" if is_free else "⚠️ That time is already booked."

        if intent == "book":
            if is_free:
                event = book_slot(service, reason, start_iso, end_iso)
                return f"✅ Your meeting for *{reason}* is booked!\n📅 [View in Calendar]({event['htmlLink']})"
            else:
                return "⚠️ That time slot is already booked. Try another time."

        return "🤔 I couldn't determine your intent. Try using 'book' or 'check'."

    except Exception as e:
        print("❌ Agent Error:", e)
        return f"🚨 Agent Error: {str(e)}"
