# 🧠 TailorTalk – AI Calendar Assistant 🤖📅

TailorTalk is an intelligent calendar booking assistant powered by Gemini and Google Calendar APIs. It allows users to book or check meeting availability using natural language like:

"Book a meeting on 22 July at 7 PM for Birthday Party"  
"Do I have any free time next Friday?"

The app understands vague phrases like “tomorrow afternoon” or “between 3–5 PM”, parses them using Gemini, checks your Google Calendar for conflicts, and books the event if available.

---

## 🚀 Features

- Understands natural language time/date expressions
- Uses Gemini (Google Generative AI) to extract intent, date, time, and reason
- Checks real-time Google Calendar availability
- Auto-books confirmed time slots
- Chat-based frontend via Streamlit
- FastAPI backend that connects Gemini + Google Calendar
- Securely deployed using Render and Google Secrets

---

## 🧱 Tech Stack

Frontend: Streamlit  
Backend: FastAPI  
Agent: Gemini via google-generativeai  
Calendar API: Google Calendar  
Deployment: Streamlit Cloud (frontend) + Render (backend)

---

## 📁 Project Structure

tailortalk/  
├── app.py                # Streamlit chat frontend  
├── main.py               # FastAPI backend routes  
├── agent.py              # Gemini + calendar agent logic  
├── gcal.py               # Google Calendar integration  
├── requirements.txt  
└── .env / secrets        # API keys, credentials.json, token.json

---

## 🔐 Setup: API Keys & Credentials

1. Google Cloud Setup  
   - Go to https://console.cloud.google.com/  
   - Enable the Google Calendar API  
   - Create OAuth 2.0 Client ID credentials  
   - Download the file as `credentials.json`

2. Gemini API Key  
   - Get it from https://makersuite.google.com/app/apikey  
   - Store it in `.env`:

GOOGLE_API_KEY=your_gemini_key_here

3. Run locally once to trigger auth flow and generate `token.json`.

---

## 💻 Running Locally

### 1. Clone the repo

git clone https://github.com/your-username/tailortalk.git  
cd tailortalk

### 2. Install dependencies

pip install -r requirements.txt

### 3. Start FastAPI backend

uvicorn main:app --reload

### 4. Start Streamlit frontend

streamlit run app.py

---

## 🌐 Deployment

### Backend on Render

- Push to GitHub  
- Create a Web Service  
- Use the following `run.py`:

import os  
import uvicorn  
if __name__ == "__main__":  
    port = int(os.environ.get("PORT", 8000))  
    uvicorn.run("main:app", host="0.0.0.0", port=port)

- Add Secret Files:
  - `/etc/secrets/credentials.json`
  - `/etc/secrets/token.json`

---

### Frontend on Streamlit Cloud

- Push frontend (`app.py`, `requirements.txt`) to GitHub  
- Go to https://streamlit.io/cloud  
- Deploy the app  
- Update backend endpoint in `app.py`:

BACKEND_URL = "https://your-backend.onrender.com/chat"

---

## 🧠 How It Works

1. User sends:

"Book a meeting tomorrow at 3 PM for team sync"

2. Gemini returns:

{  
  "intent": "book",  
  "date": "2025-07-20",  
  "time": "15:00",  
  "reason": "team sync"  
}

3. Google Calendar API checks slot.  
4. If free, it books the event.  
5. Chatbot returns:

✅ Your meeting for *team sync* is booked!  
📅 [View in Calendar](https://...)

---

## 📦 `requirements.txt`

fastapi  
uvicorn  
streamlit  
google-generativeai  
langchain  
langchain-google-genai  
google-auth  
google-auth-oauthlib  
google-api-python-client  
python-dotenv  
dateparser  
pytz  
requests

---

## 🧪 API Example

curl -X POST https://your-backend.onrender.com/chat \  
     -H "Content-Type: application/json" \  
     -d '{"user_input": "Book a meeting on 22 July at 7 PM for Birthday Party"}'

---

## ✅ Sample Logs

📅 Final start: 2025-07-22T19:00:00+05:30  
📅 Final end: 2025-07-22T20:00:00+05:30  
🔎 Checking availability from: 2025-07-22T19:00:00+05:30 to 2025-07-22T20:00:00+05:30  
📅 Found 0 events in that range.  
📤 Booking event from: 2025-07-22T19:00:00+05:30 to 2025-07-22T20:00:00+05:30  
✅ Event created: https://www.google.com/calendar/event?eid=...

---

## 🙋‍♂️ Developed By

**Ayush Rai**  
Portfolio: https://ayushrai-jan-2004.netlify.app  
GitHub: https://github.com/ayush123-bit  
LinkedIn: https://linkedin.com/in/ayush-rai-7109202b6

---

## ✅ Project Status

✅ Agent fully functional (Gemini + Fallback)  
✅ Calendar slot parsing, booking, checking  
✅ Frontend and backend deployed  
✅ Streamlit and Render integrated  
✅ Ready for demo or submission
