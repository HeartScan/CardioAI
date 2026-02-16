import requests
import json
import time

# --- CONFIGURATION ---
BASE_URL = "https://cardioai-pky1.onrender.com/api" # Your Render URL

def test_math_api_direct(key):
    url = "https://heartscan-api-175148683457.us-central1.run.app/api/v1/cardiolog/realtime_analysis"
    print(f"\n--- Testing Math API directly with key: {key[:10]}... ---")
    headers = {"X-API-Key": key}
    # Send enough samples to avoid 400
    payload = {
        "az_data_array": [{"ax": 0, "ay": 0, "az": 9.8, "timestamp": i*10} for i in range(110)],
        "device": {"userAgent": "Test", "platform": "Test"}
    }
    try:
        res = requests.post(url, json=payload, headers=headers, timeout=15)
        if res.status_code == 200:
            print(f"✅ Success! Math API key is valid.")
            return True
        elif res.status_code == 400:
            print(f"✅ Success! Math API key is valid (got status 400, but key was accepted).")
            return True
        else:
            print(f"❌ Failed! Status: {res.status_code}, Response: {res.text}")
            return False
    except Exception as e:
        print(f"💥 Error testing key: {e}")
        return False

def test_full_cycle():
    print("🚀 Starting API Test Cycle...")

    # 0. Validate Keys
    import os
    keys_to_test = [
        os.getenv("HEARTSCAN_API_KEY", "pm_only_key_d9a8f7b3e1c2"), 
        "AIzaSyCVIULdgoK64ufalJouYeo_04yv-TY1lZ8"
    ]
    valid_key = None
    for k in keys_to_test:
        if test_math_api_direct(k):
            valid_key = k
            break
    
    if not valid_key:
        print("\n🛑 No valid Math API key found. Stopping test.")
        return

    print(f"\n💡 Use this key in Render/Vercel ENV: {valid_key}")

    # 1. Mock Raw Data
    mock_raw_data = {
        "az_data_array": [
            {"ax": 0.01, "ay": 0.02, "az": 9.81, "timestamp": i*10} 
            for i in range(200)
        ],
        "device": {
            "userAgent": "PyTest-Client",
            "platform": "Simulator"
        }
    }

    # 2. Step 1: Initialize Session (/api/init)
    print("\n--- Phase 1: Initializing Chat ---")
    print(f"Sending request to {BASE_URL}/init...")
    
    try:
        init_res = requests.post(f"{BASE_URL}/init", json={"observation": mock_raw_data})
        
        if init_res.status_code != 200:
            print(f"❌ Init failed with status {init_res.status_code}")
            print(f"Error: {init_res.text}")
            return

        init_data = init_res.json()
        session_id = init_data.get("session_id")
        ai_response = init_data.get("response")

        print(f"✅ Session Created: {session_id}")
        print(f"🤖 CardioAI: {ai_response}")

        # 3. Step 2: Chat (/api/chat)
        if session_id:
            print("\n--- Phase 2: Sending User Message ---")
            user_msg = "I feel some heart palpitations."
            print(f"👤 User: {user_msg}")
            
            chat_payload = {
                "message": user_msg,
                "history": [] 
            }
            
            chat_res = requests.post(f"{BASE_URL}/chat?session_id={session_id}", json=chat_payload)
            
            if chat_res.status_code != 200:
                print(f"❌ Chat failed with status {chat_res.status_code}")
                print(f"Error: {chat_res.text}")
                return
                
            chat_data = chat_res.json()
            print(f"🤖 CardioAI: {chat_data.get('response')}")
            print("\n✨ Test Cycle Completed Successfully!")

    except Exception as e:
        print(f"💥 An unexpected error occurred: {e}")

if __name__ == "__main__":
    test_full_cycle()
