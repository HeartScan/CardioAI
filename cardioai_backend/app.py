from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from cardioai_backend.api.chat import router as chat_router


def create_app() -> FastAPI:
    app = FastAPI()

    # Enable CORS for frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # tighten in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(chat_router)
    return app

