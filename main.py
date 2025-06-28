from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from agent import run_agent

app = FastAPI()

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with your frontend domain in production
    allow_methods=["*"],
    allow_headers=["*"]
)

# Must allow both GET and HEAD for Render to detect the service is alive
@app.api_route("/", methods=["GET", "HEAD"])
def root():
    return {"message": "Slotify backend running!"}

# Main chat route
@app.post("/chat")
async def chat(request: Request):
    try:
        body = await request.json()
        user_input = body.get("user_input", "").strip()

        if not user_input:
            return JSONResponse(content={"response": "❌ No input received."}, status_code=400)

        response = run_agent(user_input)
        return JSONResponse(content={"response": response})

    except Exception as e:
        print("❌ Error in /chat:", e)
        return JSONResponse(content={"response": f"❌ Agent Error: {str(e)}"}, status_code=500)
