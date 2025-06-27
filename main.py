from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import status
from starlette.middleware.sessions import SessionMiddleware
from google_auth_oauthlib.flow import Flow
from agent import run_agent
import os

app = FastAPI()

# ✅ Allow Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Session support for storing user token
app.add_middleware(SessionMiddleware, secret_key="secret-session-key")

# 🌍 Health Check
@app.get("/")
def home():
    return {"message": "✅ TailorTalk backend is running!"}

# 🔐 OAuth Settings
client_id = os.getenv("GOOGLE_CLIENT_ID")
client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
redirect_uri = os.getenv("OAUTH_REDIRECT_URI")

# 🌐 Start Authorization
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
        redirect_uri=redirect_uri,
    )
    auth_url, _ = flow.authorization_url(prompt="consent", include_granted_scopes="true")
    return RedirectResponse(auth_url)

# ✅ OAuth2 callback
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
            redirect_uri=redirect_uri,
        )
        flow.fetch_token(authorization_response=str(request.url))
        credentials = flow.credentials

        # ✅ Save credentials in user session
        request.session["token"] = {
            "token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": credentials.scopes,
        }

        return RedirectResponse(url="https://slotify.streamlit.app")  # 🔁 Redirect to your Streamlit UI
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})

# 🤖 Chat-based Booking Endpoint
@app.post("/chat")
async def chat(request: Request):
    user_input = (await request.json()).get("user_input", "")
    token_dict = request.session.get("token")

    if not token_dict:
        return {"response": "❌ Please authorize first using /authorize."}

    response = run_agent(user_input, token_dict)
    return {"response": response}
