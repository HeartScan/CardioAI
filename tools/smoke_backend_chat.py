"""
Smoke test for the deployed/local backend `POST /api/chat`.

Usage:
  - Set CARDIOAI_BACKEND_URL (e.g. https://your-service.onrender.com)
  - Run: python tools/smoke_backend_chat.py
"""

import json
import os

import requests


def main() -> None:
    backend = os.environ.get("CARDIOAI_BACKEND_URL", "http://localhost:8000").rstrip("/")
    url = f"{backend}/api/chat"
    payload = {"message": "Hello! This is a smoke test.", "history": []}

    print("--- Starting Backend Smoke Test ---")
    print(f"Target URL: {url}")
    print(f"Payload: {json.dumps(payload, ensure_ascii=False, indent=2)}")

    try:
        res = requests.post(url, json=payload, timeout=90)
        print(f"\nStatus: {res.status_code}")
        if res.ok:
            data = res.json()
            print("\nOK")
            print(data.get("response"))
        else:
            print("\nFAILED")
            print(res.text)
    except requests.exceptions.Timeout:
        print("\nFAILED: request timed out")
    except Exception as e:
        print(f"\nFAILED: {e}")


if __name__ == "__main__":
    main()

