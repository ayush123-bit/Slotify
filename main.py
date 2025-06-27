from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from google_auth_oauthlib.flow import Flow
from agent import run_agent
import os

app = FastAPI()

# 🔓 CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Root endpoint (health check for Render)
@app.get("/")
def home():
    return {"message": "✅ TailorTalk API is running!"}

# 🔐 OAuth credentials from environment
client_id = os.getenv("GOOGLE_CLIENT_ID")
client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
redirect_uri = os.getenv("OAUTH_REDIRECT_URI")

# 🌐 Authorize user with Google Calendar
@app.get("/authorize")
def authorize():
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [redirect_uri],
            }
        },
        scopes=["https://www.googleapis.com/auth/calendar"],
        redirect_uri=redirect_uri
    )
    auth_url, _ = flow.authorization_url(prompt="consent")
    return RedirectResponse(auth_url)

# ✅ Callback handler after user logs in
@app.get("/oauth2callback")
async def oauth2callback(request: Request):
    try:
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [redirect_uri],
                }
            },
            scopes=["https://www.googleapis.com/auth/calendar"],
            redirect_uri=redirect_uri
        )
        flow.fetch_token(authorization_response=str(request.url))
        credentials = flow.credentials

        # 🚨 Save credentials per user securely in DB/session in production
        return {"message": "✅ Authorized. You can now book slots!"}
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})

# 🤖 Conversational Booking Endpoint
@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    user_input = data.get("user_input", "")
    response = run_agent(user_input)
    return {"response": response}
