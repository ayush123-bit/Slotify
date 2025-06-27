# agent.py
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from gcal import get_calendar_service, check_availability, book_slot
from datetime import datetime, timedelta
import os

# Gemini model setup
llm = ChatGoogleGenerativeAI(
    model="gemini-pro",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0
)

# Structured output parser
parser = JsonOutputParser()

# Prompt template
prompt = ChatPromptTemplate.from_messages([
    ("system", "Extract booking info (date, time, reason) from user input. Respond in JSON."),
    ("human", "{user_input}\nFormat:\n{format_instructions}")
])

chain = prompt | llm | parser

def run_agent(user_input):
    try:
        response = chain.invoke({
            "user_input": user_input,
            "format_instructions": parser.get_format_instructions()
        })

        print("🔍 Gemini parsed:", response)

        date = response["date"]
        time = response["time"]
        reason = response.get("reason", "TailorTalk Appointment")

        start_dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        end_dt = start_dt + timedelta(hours=1)

        start_iso = start_dt.isoformat()
        end_iso = end_dt.isoformat()

        service = get_calendar_service()
        if check_availability(service, start_iso, end_iso):
            event = book_slot(service, reason, start_iso, end_iso)
            return f"✅ Meeting booked for {reason}!\n📅 [View in Calendar]({event['htmlLink']})"
        else:
            return "⚠️ That time slot is already booked."
    except Exception as e:
        print("❌ Error in agent:", e)
        return f"🚨 Error: {str(e)}"
