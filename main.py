
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from agent import run_agent

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/")
def root():
    return {"message": "TailorTalk backend running!"}

@app.post("/chat")
async def chat(request: Request):
    user_input = (await request.json()).get("user_input", "")
    response = run_agent(user_input)
    return {"response": response}
