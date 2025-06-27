from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from google_auth_oauthlib.flow import Flow
from gcal import set_user_token, get_calendar_service, check_availability, book_slot
from agent import extract_datetime_from_text
import os
import uuid

app = FastAPI()

# Allow frontend (e.g., Streamlit) to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Read secrets from environment variables
client_id = os.getenv("GOOGLE_CLIENT_ID")
client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
redirect_uri = os.getenv("OAUTH_REDIRECT_URI")

@app.get("/")
def home():
    return {"message": "✅ TailorTalk API is running."}

@app.get("/authorize")
def authorize():
    # Generate temporary session ID for the user (in real use, use OAuth state/session)
    user_id = str(uuid.uuid4())
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [redirect_uri]
            }
        },
        scopes=["https://www.googleapis.com/auth/calendar"],
        redirect_uri=redirect_uri
    )
    auth_url, state = flow.authorization_url(prompt="consent", include_granted_scopes="true")
    return RedirectResponse(f"{auth_url}&state={user_id}")

@app.get("/oauth2callback")
async def oauth2callback(request: Request):
    full_url = str(request.url)
    user_id = request.query_params.get("state")

    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [redirect_uri]
            }
        },
        scopes=["https://www.googleapis.com/auth/calendar"],
        redirect_uri=redirect_uri
    )
    flow.fetch_token(authorization_response=full_url)

    # Save token in memory (for production, use DB/session storage)
    credentials = flow.credentials
    set_user_token(user_id, credentials.to_json())

    return {"message": "✅ Authorization successful. You can now book slots.", "user_id": user_id}

@app.post("/chat")
async def chat(request: Request):
    try:
        data = await request.json()
        user_input = data.get("user_input", "")
        user_id = data.get("user_id")  # required to retrieve credentials

        if not user_id:
            return {"response": "❌ Please authorize first using /authorize."}

        start_iso, end_iso = extract_datetime_from_text(user_input)
        if not start_iso or not end_iso:
            return {"response": "❌ Couldn’t parse the datetime. Try: 'Book at 5 PM tomorrow'."}

        service = get_calendar_service(user_id)

        if check_availability(service, start_iso, end_iso):
            summary = "TailorTalk Booking"
            if "for" in user_input.lower():
                summary = user_input.split("for")[-1].strip()
            event = book_slot(service, summary, start_iso, end_iso)
            return {"response": f"✅ Your slot is booked for **{summary}** on **{start_iso}**\n📅 [View]({event['htmlLink']})"}
        else:
            return {"response": "❌ The slot is already booked. Please choose another time."}

    except Exception as e:
        print("❌ Backend error:", e)
        return {"response": f"🚨 Unexpected error: {str(e)}"}
