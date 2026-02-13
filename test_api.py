import requests
import json
import time

# --- CONFIGURATION ---
BASE_URL = "https://cardioai-pky1.onrender.com/api" # Your Render URL
# BASE_URL = "http://localhost:8000/api"           # Local testing

def test_full_cycle():
    print("🚀 Starting API Test Cycle...")
    
    # 1. Mock Raw Data (Accelerometer-like)
    # Since we don't have real raw data in files, we'll send a mock array
    # that your new HeartScan API should be able to process.
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
                "history": [] # In this stateless version, we could pass local history
            }
            
            # Pass session_id as a query param or cookie (server supports both)
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
