from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
#import logger
from typing import Any


# from pathlib import Path
# import json
# from fastapi import Query


from controller import Controller


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"] ,
    allow_headers=["*"] ,
)

controller: Controller
controller = None

class InitPayload(BaseModel):
    observation: Any

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

# @app.post("/api/init")
# def init_chat(payload: InitPayload, idx: int = Query(0, ge=0)):
#     global controller

#     repo_root = Path(__file__).resolve().parent
#     examples_path = repo_root / "resp_example" / "heart_rate_first10_responses.json"
#     records = json.loads(examples_path.read_text(encoding="utf-8"))

#     if not isinstance(records, list) or not records:
#         raise HTTPException(status_code=500, detail="Examples file is empty or invalid")

#     if idx >= len(records):
#         raise HTTPException(status_code=400, detail=f"idx out of range: {idx} (len={len(records)})")

#     observation = records[idx]
#     controller = Controller(observation)

#     return {
#         "status": "initialized",
#         "response": controller.get_init_response(),
#         "history": controller.get_history(),
#     }


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


