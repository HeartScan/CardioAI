import requests
import json

def test_cardioai_backend():
    url = "https://cardioai-backend-vfvl.onrender.com/api/chat"
    payload = {
        "message": "Hello! Can you hear me? This is a test from CardioAI developer.",
        "history": []
    }
    headers = {
        "Content-Type": "application/json"
    }

    print(f"--- Starting Backend Test ---")
    print(f"Target URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print("Sending request... (this may take 30-60 seconds if the model is loading)")

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=90)
        
        print(f"\nResponse status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("\n✅ SUCCESS!")
            print(f"CardioAI Response: {data.get('response')}")
            # print(f"History state: {len(data.get('history', []))} messages")
        else:
            print("\n❌ FAILED")
            print(f"Error details: {response.text}")
            
    except requests.exceptions.Timeout:
        print("\n❌ FAILED: Request timed out. Render or the LLM API might be slow.")
    except Exception as e:
        print(f"\n❌ FAILED: An unexpected error occurred: {str(e)}")

    print(f"\n--- Test Finished ---")

if __name__ == "__main__":
    test_cardioai_backend()
