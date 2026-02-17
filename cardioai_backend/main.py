import os


try:
    # When running from repo root: `python -m cardioai_backend.main`
    from cardioai_backend.app import create_app
except Exception:
    # When running from within cardioai_backend/: `python main.py`
    from app import create_app  # type: ignore


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
