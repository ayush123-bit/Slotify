import re
import dateparser
from datetime import datetime, timedelta
from gcal import get_calendar_service, check_availability, book_slot
from pytz import timezone

IST = timezone('Asia/Kolkata')

def extract_datetime_from_text(text):
    """
    Extracts a datetime object from user input using regex and dateparser.
    Handles special phrases like 'day after tomorrow'.
    Returns start and end ISO-formatted datetime strings in IST.
    """
    now = datetime.now(IST)

    # Handle specific human phrases manually
    if "day after tomorrow" in text.lower():
        future_date = (now + timedelta(days=2)).strftime("%d %B")
        text = re.sub(r"day after tomorrow", future_date, text, flags=re.IGNORECASE)

    # Strong regex to extract common natural date-time patterns
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

    # Fix year if parsed weirdly
    if parsed_dt.year is None or parsed_dt.year < now.year:
        parsed_dt = parsed_dt.replace(year=now.year)

    # Round to hour
    start_time = parsed_dt.replace(second=0, microsecond=0)
    end_time = start_time + timedelta(hours=1)

    print("✅ Final parsed start_time:", start_time.isoformat())
    print("✅ Final parsed end_time:", end_time.isoformat())

    return start_time.isoformat(), end_time.isoformat()

def run_agent(user_input):
    """
    Parses user input, checks calendar availability, and books the slot.
    """
    start_iso, end_iso = extract_datetime_from_text(user_input)

    if not start_iso or not end_iso:
        return (
            "❌ Sorry, I couldn’t understand your request.\n"
            "Try saying: 'Book a meeting tomorrow at 4 PM', '4 July at 1 PM', or 'day after tomorrow at 6 PM'."
        )

    try:
        service = get_calendar_service()

        print("📅 Checking calendar availability...")
        if check_availability(service, start_iso, end_iso):
            print("✅ Slot is free. Booking now...")
            event = book_slot(service, "TailorTalk Appointment", start_iso, end_iso)
            print("📌 Event created:", event.get('htmlLink'))
            return f"✅ Your meeting is booked!\n\n📅 [View in Calendar]({event['htmlLink']})"
        else:
            print("⚠️ Slot is already booked.")
            return "⚠️ That time slot is already booked. Please try a different time."
    except Exception as e:
        print("❌ Backend error:", e)
        return f"🚨 An unexpected error occurred: {str(e)}"
