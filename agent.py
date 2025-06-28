# agent.py

import os
import json
import re
import random
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

# Time mappings
TIME_MAPPINGS = {
    "morning": "10:00",
    "noon": "12:00",
    "afternoon": "15:00",
    "evening": "18:00",
    "night": "20:00"
}

# Conversation handling
GREETINGS = {
    "hi", "hello", "hey", "hola", "greetings",
    "what's up", "how are you", "howdy", "good morning",
    "good afternoon", "good evening", "good night"
}

CASUAL_RESPONSES = [
    "I'm doing well, thank you! How can I assist with your schedule today?",
    "Hello! I'm here to help with your calendar needs.",
    "Hi there! Ready to book or check some appointments?",
    "Greetings! Let me know how I can help with your schedule.",
    "Good day! What would you like to schedule today?"
]

HELP_RESPONSE = """
I can help you with:
- Booking appointments (e.g., "Book a meeting tomorrow at 2pm")
- Checking availability (e.g., "Is 3pm Friday available?")
- General questions about your calendar

Try something like:
"Can we meet next Tuesday afternoon?"
"Is my calendar free on Wednesday?"
"Book a doctor's appointment for Friday at 10am"
"""

def is_casual_conversation(text):
    text = text.lower().strip()
    if any(greeting in text for greeting in GREETINGS):
        return True
    if text in {"thanks", "thank you", "help", "what can you do"}:
        return True
    return False

def generate_response(text):
    text = text.lower().strip()
    
    if any(greeting in text for greeting in GREETINGS):
        return random.choice(CASUAL_RESPONSES)
    if text == "help":
        return HELP_RESPONSE
    if text in {"thanks", "thank you"}:
        return "You're welcome! Let me know if you need anything else."
    return None

def parse_json_response(text):
    try:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        return json.loads(match.group()) if match else {}
    except json.JSONDecodeError:
        return {}

def extract_time_range(user_input, start_dt):
    pattern = r'(\d{1,2})(?::(\d{2}))?\s*(AM|PM|am|pm)?\s*(?:-|to)\s*(\d{1,2})(?::(\d{2}))?\s*(AM|PM|am|pm)?'
    match = re.search(pattern, user_input, re.IGNORECASE)
    
    if not match:
        return None
        
    sh, sm, sap, eh, em, eap = match.groups()
    sh, sm = int(sh), int(sm) if sm else 0
    eh, em = int(eh), int(em) if em else 0

    def to_24h(hour, minute, ampm):
        if not ampm:
            return hour, minute
        ampm = ampm.lower()
        if ampm == "pm" and hour != 12:
            hour += 12
        elif ampm == "am" and hour == 12:
            hour = 0
        return hour, minute

    sh, sm = to_24h(sh, sm, sap or eap)
    eh, em = to_24h(eh, em, eap or sap)

    end_dt = start_dt.replace(hour=eh, minute=em)
    return end_dt if end_dt > start_dt else start_dt + timedelta(hours=1)

def process_datetime(user_input, date_str, time_str):
    if not date_str or not time_str:
        dt = parse_date(user_input, settings={
            'PREFER_DATES_FROM': 'future',
            'RELATIVE_BASE': datetime.now(IST),
            'TIMEZONE': 'Asia/Kolkata',
            'RETURN_AS_TIMEZONE_AWARE': True
        })
        if not dt:
            return None
        return dt.replace(minute=0, second=0, microsecond=0)
    
    # Handle vague time expressions
    if time_str == "12:00":
        for keyword, mapped_time in TIME_MAPPINGS.items():
            if keyword in user_input.lower():
                time_str = mapped_time
                break

    try:
        start_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        start_dt = IST.localize(start_dt.replace(minute=0, second=0, microsecond=0))
        
        # Correct past dates to current year
        if start_dt.date() < TODAY:
            start_dt = start_dt.replace(year=TODAY.year)
            
        return start_dt
    except ValueError:
        return None

def handle_scheduling(intent, start_dt, end_dt, reason):
    service = get_calendar_service()
    is_free = check_availability(service, start_dt.isoformat(), end_dt.isoformat())

    if intent == "check":
        return "That time slot is available." if is_free else "That time is already booked."

    if intent == "book":
        if is_free:
            event = book_slot(service, reason, start_dt.isoformat(), end_dt.isoformat())
            return f"Your meeting '{reason}' has been booked. Calendar link: {event['htmlLink']}"
        return "That time slot is already booked. Please try another time."
    
    return "I'm not sure what you'd like to do. Please specify 'book' or 'check'."

def run_agent(user_input):
    # Check for casual conversation first
    casual_response = generate_response(user_input)
    if casual_response:
        return casual_response

    today_str = TODAY.strftime("%Y-%m-%d")
    
    prompt = f"""
You are a conversational calendar assistant. Today is {today_str}.
Extract scheduling details from this input and return ONLY valid JSON:

{{
    "intent": "book" or "check",
    "date": "YYYY-MM-DD",
    "time": "HH:MM" (24-hour),
    "reason": "Meeting title"
}}

User: "{user_input}"
"""
    
    try:
        response = model.generate_content(prompt)
        data = parse_json_response(response.text)
        
        if not data:
            return "I couldn't understand your request. Please try again or say 'help'."

        intent = data.get("intent", "book").lower()
        date_str = data.get("date")
        time_str = data.get("time", "12:00")
        reason = data.get("reason", "Meeting")

        start_dt = process_datetime(user_input, date_str, time_str)
        if not start_dt:
            return "I couldn't determine the date or time. Please try again."

        end_dt = extract_time_range(user_input, start_dt) or (start_dt + timedelta(hours=1))
        
        return handle_scheduling(intent, start_dt, end_dt, reason)

    except Exception as e:
        return f"Sorry, I encountered an error: {str(e)}. Please try again."
