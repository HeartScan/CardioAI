from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import os
from dotenv import load_dotenv
#import logger

from controller import Controller

load_dotenv(".env")

print()
print(os.environ.get("WRITER_API_KEY"))
print()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"] ,
    allow_headers=["*"] ,
)

controller: Controller

class InitPayload(BaseModel):
    observation: str

class ChatPayload(BaseModel):
    message: str


@app.post("/api/init")
def init_chat(payload: InitPayload):
    global controller
    controller = Controller(payload.observation)
    return {
        "status": "initialized",
        "response": controller.get_init_response(),   # показываем фронту
        "history": controller.get_history(),          # (опционально)
    }


@app.post("/api/chat")
def chat(payload: ChatPayload):
    if controller is None:
        raise HTTPException(status_code=400, detail="Session not initialized")
    response = controller.send_user_message(payload.message)
    return {"response": response, "history": controller.get_history()}


if __name__ == "__main__":
    

    uvicorn.run(
        "server:app",           # module:object
        host="0.0.0.0",
        port=8000,
        reload=True             # уберите в продакшне
    )


