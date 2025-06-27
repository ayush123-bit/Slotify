from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
import os
import json

from agent import run_agent

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client_id = os.getenv("GOOGLE_CLIENT_ID")
client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
redirect_uri = os.getenv("OAUTH_REDIRECT_URI")

SESSION_TOKEN_FILE = "session_token.json"

@app.get("/")
def home():
    return {"message": "✅ TailorTalk backend is live!"}

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
    auth_url, _ = flow.authorization_url(prompt="consent")
    return RedirectResponse(auth_url)

@app.get("/oauth2callback")
async def oauth2callback(request: Request):
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
    creds = flow.credentials

    with open(SESSION_TOKEN_FILE, "w") as f:
        f.write(creds.to_json())

    return {"message": "✅ Authorized successfully. You can now book meetings!"}

@app.post("/chat")
async def chat(request: Request):
    user_input = (await request.json()).get("user_input", "")
    if not os.path.exists(SESSION_TOKEN_FILE):
        return {"response": "❌ Please authorize first using /authorize."}
    with open(SESSION_TOKEN_FILE, "r") as f:
        creds_json = f.read()

    return {"response": run_agent(user_input, creds_json)}
