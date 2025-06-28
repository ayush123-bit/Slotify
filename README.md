# 🧠 Slotify – AI Calendar Assistant 🤖📅

Slotify is an intelligent calendar scheduling agent powered by **Gemini** and **Google Calendar APIs**. It allows users to book or check meeting availability using natural language like:

"Book a meeting on 22 July at 7 PM for Birthday Party"  
"Do I have any free time next Friday?"  
"Schedule a call between 3–5 PM tomorrow for a project discussion"

Slotify understands vague time expressions like “tomorrow evening” or “next week”, uses Gemini to extract intent, and automatically checks and books slots via Google Calendar.

---

## 🚀 Features

- 💬 Chat-style natural language booking
- 🤖 Gemini-powered intent extraction (date, time, reason)
- 🧠 Handles vague phrases like "tomorrow", "evening", "3-5 PM"
- 📅 Google Calendar slot checking
- 📤 Automatic calendar booking
- 🔒 Secure deployment with secret files on Render

---

## 🧱 Tech Stack

Frontend: Streamlit  
Backend: FastAPI  
AI: Gemini (Google Generative AI API)  
Calendar API: Google Calendar  
Deployment: Streamlit Cloud (frontend) + Render (backend)

---

## 📁 Project Structure

Slotify/  
├── app.py                → Streamlit frontend  
├── main.py               → FastAPI backend routes  
├── agent.py              → Gemini + fallback date parser  
├── gcal.py               → Google Calendar integration  
├── requirements.txt  
└── /secrets/             → credentials.json, token.json (on Render)

---

## 🔐 Setup

1. **Google Cloud Console**
   - Enable Google Calendar API
   - Create OAuth 2.0 credentials
   - Download `credentials.json`

2. **Gemini API Key**
   - Get it from https://makersuite.google.com/app/apikey
   - Add to `.env` as:

GOOGLE_API_KEY=your_gemini_key

3. **Run Locally Once**  
   To generate `token.json` via browser auth

---

## 💻 Running Locally

Clone the repository:

git clone https://github.com/ayush123-bit/Slotify.git  
cd Slotify

Install dependencies:

pip install -r requirements.txt

Start the backend (FastAPI):

uvicorn main:app --reload

Start the frontend (Streamlit):

streamlit run app.py

---

## 🌐 Deployment

### 🔧 Backend: Deployed on Render

- Live URL: https://slotify-zmfm.onrender.com  
- `main.py` must bind to the dynamic port:

import os  
import uvicorn  
if __name__ == "__main__":  
    port = int(os.environ.get("PORT", 8000))  
    uvicorn.run("main:app", host="0.0.0.0", port=port)

- Add Secret Files in Render:
  - `/etc/secrets/credentials.json`
  - `/etc/secrets/token.json`

---

### 💬 Frontend: Deployed on Streamlit Cloud

1. Push frontend (`app.py`, `requirements.txt`) to a repo  
2. Go to https://streamlit.io/cloud  
3. Deploy and connect to backend

Set your backend URL in `app.py`:

BACKEND_URL = "https://slotify-zmfm.onrender.com/chat"

---

## 🧠 How It Works

1. User types:  
"Book a meeting tomorrow at 6 PM for demo"

2. Gemini returns:

{  
  "intent": "book",  
  "date": "2025-07-20",  
  "time": "18:00",  
  "reason": "demo"  
}

3. Calendar checked → slot is free → booked  
4. Response shown in Streamlit:

✅ Your meeting for *demo* is booked!  
📅 [View in Calendar](https://...)

---

## 📦 Requirements

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

## 🧪 Test API

curl -X POST https://slotify-zmfm.onrender.com/chat \  
     -H "Content-Type: application/json" \  
     -d '{"user_input": "Book a meeting on 20 July at 7 PM for Birthday Party"}'

---

## ✅ Sample Logs

📅 Final start: 2025-07-20T19:00:00+05:30  
📅 Final end: 2025-07-20T20:00:00+05:30  
🔎 Checking availability...  
📅 Found 0 events in that range  
📤 Booking...  
✅ Event created: https://www.google.com/calendar/event?eid=...

---

## 🙋‍♂️ Developed By

**Ayush Rai**  
Portfolio: https://ayushrai-jan-2004.netlify.app  
GitHub: https://github.com/ayush123-bit  
LinkedIn: https://linkedin.com/in/ayush-rai-7109202b6

---

## ✅ Project Status

✅ Agent working end-to-end  
✅ Gemini + fallback parsing logic  
✅ Calendar integration complete  
✅ Backend hosted on Render  
✅ Frontend ready for Streamlit  
✅ Ideal for internship/project submissions
