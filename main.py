from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from agent import run_agent

app = FastAPI()

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with specific domain in production
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/")
def root():
    return {"message": "TailorTalk backend running!"}

@app.post("/chat")
async def chat(request: Request):
    try:
        body = await request.json()
        user_input = body.get("user_input", "")
        
        if not user_input:
            return JSONResponse(content={"response": "❌ No input received."}, status_code=400)
        
        response = run_agent(user_input)
        return JSONResponse(content={"response": response})
    
    except Exception as e:
        print("❌ Error in /chat:", e)
        return JSONResponse(content={"response": f"❌ Agent Error: {str(e)}"}, status_code=500)
