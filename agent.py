import re
import dateparser
from datetime import datetime, timedelta
from gcal import get_calendar_service, check_availability, book_slot
from pytz import timezone

IST = timezone('Asia/Kolkata')

def extract_datetime_from_text(text):
    """
    Extract datetime object from user input using regex and dateparser.
    Handles phrases like 'day after tomorrow'.
    """
    now = datetime.now(IST)

    if "day after tomorrow" in text.lower():
        future_date = (now + timedelta(days=2)).strftime("%d %B")
        text = re.sub(r"day after tomorrow", future_date, text, flags=re.IGNORECASE)

    time_pattern = r"((?:on\s+)?(?:\d{1,2}(?:st|nd|rd|th)?\s+\w+|\w+\s+\d{1,2})(?:\s+at\s+\d{1,2}(?::\d{2})?\s*(?:AM|PM)?)?|today|tomorrow(?:\s+at\s+\d{1,2}(?::\d{2})?\s*(?:AM|PM)?)?)"
    match = re.search(time_pattern, text, re.IGNORECASE)
    time_text = match.group().strip() if match else text.strip()

    print(f"🔍 Extracted text for parsing: '{time_text}'")

    parsed_dt = dateparser.parse(
        time_text,
        settings={
            'PREFER_DATES_FROM': 'future',
            'TIMEZONE': 'Asia/Kolkata',
            'RETURN_AS_TIMEZONE_AWARE': True,
        }
    )

    if not parsed_dt:
        print("❌ Failed to parse datetime.")
        return None, None

    if parsed_dt.year < now.year:
        parsed_dt = parsed_dt.replace(year=now.year)

    start_time = parsed_dt.replace(second=0, microsecond=0)
    end_time = start_time + timedelta(hours=1)

    print("✅ Final parsed start_time:", start_time.isoformat())
    print("✅ Final parsed end_time:", end_time.isoformat())

    return start_time.isoformat(), end_time.isoformat()

def extract_reason(text):
    """
    Extracts booking reason based on 'for <something>' pattern.
    """
    match = re.search(r"for (.+)", text, re.IGNORECASE)
    if match:
        return match.group(1).strip().capitalize()
    return "TailorTalk Appointment"

def run_agent(user_input, token_dict):
    """
    Parses input, checks availability, and books slot using user token.
    """
    start_iso, end_iso = extract_datetime_from_text(user_input)
    reason = extract_reason(user_input)

    if not start_iso or not end_iso:
        return "❌ Sorry, I couldn’t understand your request. Try saying: 'Book a meeting on 6 July at 7 PM for Demo'."

    try:
        service = get_calendar_service(token_dict)
        print("📅 Checking calendar availability...")

        if check_availability(service, start_iso, end_iso):
            print("✅ Slot is free. Booking now...")
            event = book_slot(service, reason, start_iso, end_iso)
            return f"✅ Your slot is booked for **{reason}** on **{start_iso}**.\n📅 [View in Calendar]({event['htmlLink']})"
        else:
            print("⚠️ Slot is already booked.")
            return "⚠️ The slot is not empty. Please try another time."
    except Exception as e:
        print("❌ Backend error:", e)
        return f"🚨 An unexpected error occurred: {str(e)}"
