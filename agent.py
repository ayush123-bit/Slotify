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

# Time mappings with variations
TIME_MAPPINGS = {
    "morning": ["10am", "10:00", "morning", "early"],
    "noon": ["12pm", "12:00", "noon", "midday"],
    "afternoon": ["3pm", "15:00", "afternoon", "early evening"],
    "evening": ["6pm", "18:00", "evening", "late afternoon"],
    "night": ["8pm", "20:00", "night", "late"]
}

# Enhanced conversation handling
CONVERSATION_HANDLERS = {
    "greetings": {
        "patterns": ["hi", "hello", "hey", "hola", "greetings", "howdy",
                   "good morning", "good afternoon", "good evening", "good night"],
        "responses": [
            "Hello! How can I assist with your schedule today?",
            "Hi there! Ready to help with your calendar needs.",
            "Greetings! What would you like to schedule?"
        ]
    },
    "thanks": {
        "patterns": ["thanks", "thank you", "appreciate it"],
        "responses": [
            "You're welcome! Let me know if you need anything else.",
            "Happy to help! What else can I do for you?",
            "My pleasure! Feel free to ask for more assistance."
        ]
    },
    "help": {
        "patterns": ["help", "what can you do", "assistance"],
        "response": """
I'm your smart scheduling assistant. Here's what I can do:

📅 Schedule appointments: 
   "Book a meeting tomorrow at 2pm"
   "Schedule a call next Tuesday afternoon"

🗓️ Check availability:
   "Am I free on Friday at 3pm?"
   "What's my schedule like tomorrow?"

💡 I understand natural language:
   "Set up a doctor's visit next week"
   "Do I have anything scheduled for Monday morning?"
"""
    },
    "farewell": {
        "patterns": ["bye", "goodbye", "see you", "later"],
        "responses": [
            "Goodbye! Have a great day!",
            "See you later! Don't hesitate to come back if you need help.",
            "Take care! Come back anytime you need scheduling help."
        ]
    }
}

def is_conversational(text):
    """Check if the input is conversational rather than scheduling-related"""
    text_lower = text.lower().strip()
    for handler in CONVERSATION_HANDLERS.values():
        if any(pattern in text_lower for pattern in handler["patterns"]):
            return True
    return False

def handle_conversation(text):
    """Generate appropriate responses for conversational inputs"""
    text_lower = text.lower().strip()
    for handler_type, handler in CONVERSATION_HANDLERS.items():
        if any(pattern in text_lower for pattern in handler["patterns"]):
            if handler_type == "help":
                return handler["response"]
            return random.choice(handler["responses"])
    return None

def parse_json_response(text):
    """Robust JSON parsing with error handling"""
    try:
        # Handle cases where response might include markdown or other formatting
        text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to extract JSON from malformed responses
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        return {}

def extract_time_info(user_input):
    """Flexible time extraction with multiple format support"""
    # Handle time ranges
    range_pattern = r'(\d{1,2})(?::(\d{2}))?\s*(AM|PM|am|pm)?\s*(?:-|to|until)\s*(\d{1,2})(?::(\d{2}))?\s*(AM|PM|am|pm)?'
    range_match = re.search(range_pattern, user_input, re.IGNORECASE)
    if range_match:
        return range_match.groups()
    
    # Handle single time points
    time_pattern = r'(\d{1,2})(?::(\d{2}))?\s*(AM|PM|am|pm)?'
    time_match = re.search(time_pattern, user_input, re.IGNORECASE)
    if time_match:
        return (*time_match.groups(), None, None, None)
    
    # Handle natural time expressions
    for time_name, variations in TIME_MAPPINGS.items():
        if any(variation in user_input.lower() for variation in variations):
            default_time = variations[1] if len(variations) > 1 else "12:00"
            return (default_time[:2], default_time[3:], "AM" if int(default_time[:2]) < 12 else "PM", None, None, None)
    
    return (None, None, None, None, None, None)

def process_datetime(user_input, date_str=None, time_str=None):
    """Flexible datetime processing with natural language support"""
    # First try to parse complete datetime string
    dt = parse_date(user_input, settings={
        'PREFER_DATES_FROM': 'future',
        'RELATIVE_BASE': datetime.now(IST),
        'TIMEZONE': 'Asia/Kolkata',
        'RETURN_AS_TIMEZONE_AWARE': True
    })
    
    if dt:
        return dt.replace(minute=0, second=0, microsecond=0)
    
    # Fallback to separate date and time components
    if date_str and time_str:
        try:
            # Handle vague time expressions
            if time_str == "12:00":
                for time_name, variations in TIME_MAPPINGS.items():
                    if any(variation in user_input.lower() for variation in variations):
                        time_str = variations[1] if len(variations) > 1 else "12:00"
                        break

            start_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
            start_dt = IST.localize(start_dt.replace(minute=0, second=0, microsecond=0))
            
            # Correct past dates to current year
            if start_dt.date() < TODAY:
                start_dt = start_dt.replace(year=TODAY.year)
                
            return start_dt
        except ValueError:
            pass
    
    return None

def suggest_alternative_times(start_dt):
    """Generate alternative time suggestions when slot is booked"""
    suggestions = []
    for delta in [30, 60, 90, 120]:  # Suggest times in 30-min increments for next 2 hours
        new_time = start_dt + timedelta(minutes=delta)
        if check_availability(get_calendar_service(), new_time.isoformat(), (new_time + timedelta(hours=1)).isoformat()):
            suggestions.append(new_time)
            if len(suggestions) >= 3:  # Limit to 3 suggestions
                break
    return suggestions

def handle_scheduling(intent, start_dt, end_dt, reason):
    """Handle the scheduling logic with better user feedback"""
    service = get_calendar_service()
    is_free = check_availability(service, start_dt.isoformat(), end_dt.isoformat())

    if intent == "check":
        if is_free:
            return f"You're available on {start_dt.strftime('%A, %B %d at %I:%M %p')}."
        else:
            return f"You already have an event scheduled on {start_dt.strftime('%A, %B %d at %I:%M %p')}."

    if intent == "book":
        if is_free:
            event = book_slot(service, reason, start_dt.isoformat(), end_dt.isoformat())
            return (
                f"✅ Successfully booked '{reason}' for {start_dt.strftime('%A, %B %d at %I:%M %p')}.\n"
                f"You can view it here: {event.get('htmlLink', '(calendar link not available)')}"
            )
        else:
            suggestions = suggest_alternative_times(start_dt)
            response = (
                f"Sorry, {start_dt.strftime('%A at %I:%M %p')} is already booked.\n"
            )
            if suggestions:
                response += "\nHere are some available times:\n"
                for time in suggestions:
                    response += f"- {time.strftime('%A, %B %d at %I:%M %p')}\n"
                response += "\nWould you like to book one of these instead?"
            else:
                response += "I couldn't find available times nearby. Please try a different time."
            return response
    
    return "I'm not sure what you'd like to do. You can say 'book' or 'check'."

def run_agent(user_input):
    """Main agent function with improved natural language handling"""
    # First handle conversational inputs
    if is_conversational(user_input):
        return handle_conversation(user_input)

    today_str = TODAY.strftime("%Y-%m-%d")
    
    # Enhanced prompt with examples
    prompt = f"""
You are an intelligent scheduling assistant. Today is {today_str}.
Extract the following details from the user's input:

1. Intent ("book" or "check")
2. Date (YYYY-MM-DD format)
3. Time (24-hour format)
4. Event title/reason

Examples:
- "Book a meeting tomorrow at 3pm" → {{"intent": "book", "date": "{TODAY + timedelta(days=1)}", "time": "15:00", "reason": "Meeting"}}
- "Is Friday at 10am available?" → {{"intent": "check", "date": "{TODAY + timedelta(days=(4 - TODAY.weekday()) % 7)}", "time": "10:00", "reason": "Appointment"}}
- "Schedule team sync next Monday afternoon" → {{"intent": "book", "date": "{TODAY + timedelta(days=(7 - TODAY.weekday()) % 7)}", "time": "15:00", "reason": "Team Sync"}}

Current input: "{user_input}"

Respond with ONLY the JSON object:
"""
    
    try:
        response = model.generate_content(prompt)
        data = parse_json_response(response.text)
        
        if not data:
            return "I didn't quite get that. Could you rephrase or say 'help' for assistance?"

        intent = data.get("intent", "book").lower()
        date_str = data.get("date")
        time_str = data.get("time", "12:00")
        reason = data.get("reason", "Meeting")

        start_dt = process_datetime(user_input, date_str, time_str)
        if not start_dt:
            return "I couldn't determine the date or time. Please try something like 'Book a meeting tomorrow at 2pm'."

        end_dt = extract_time_range(user_input, start_dt) or (start_dt + timedelta(hours=1))
        
        return handle_scheduling(intent, start_dt, end_dt, reason)

    except Exception as e:
        return "Sorry, I encountered an issue. Please try again or say 'help' for assistance."
