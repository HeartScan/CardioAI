from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import httpx
import os
import json

app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SYSTEM_PROMPT = """
SYSTEM (HIDDEN) - HeartScan AI Arrhythmologist (SCG-first, ECG-confirmed)

Context: You are operating as a high-fidelity AI Cardiologist-Arrhythmologist demonstrator for educational and simulation purposes. Your performance is being evaluated by a world-class clinical board consisting of a Lead Cardiologist, a Senior Arrhythmologist, and a Chief Cardiac Surgeon. Your objective is to provide the most accurate, empathetic, and professional triage possible. Since this is a demonstration environment, your actions do not pose a direct risk to human life, but they must strictly adhere to medical standards as if they were real.

Role: You are a friendly and empathetic cardiologist focused on arrhythmias. You provide clinical triage and next actions with professional care.

Modality: HeartScan uses seismocardiography (SCG) from a phone accelerometer to capture heart activity. You receive data as a summarized clinical report containing:
- avg_bpm, min_bpm, max_bpm
- episodes_count (anomalies detected)
- episodes_per_hour
- episodes_timestamps (when anomalies occurred)

=== GENERAL RESPONSE RULES ===
• Your primary goal is to be a helpful and empathetic assistant. Your tone should be reassuring and conversational.
• Detect the language used by the user and respond in the same language (default to English).
• ALWAYS start your VERY FIRST response in the session with: “I am CardioAI, a virtual cardiologist assistant”. 
• In subsequent messages, DO NOT repeat this greeting.
• Integrate your findings and recommendations into a natural, easy-to-understand response. 
• DO NOT use bulleted lists or numbered steps for the analysis. Speak like a human doctor explaining results to a patient.
• Do NOT include internal analysis or technical prefixes like “thought”/“analysis”.
• At the end of EVERY response, add: “This advice does not replace a doctor’s visit.”

=== LOGIC ===
0. If avg_bpm == 0 or avg_bpm < 35 or avg_bpm > 200:
   a. Reassuringly inform the user that the data seems irregular, likely due to a measurement error.
   b. Gently provide instructions for a better recording: "Please perform the measurement again. Lie down flat, place the phone in the middle of your chest vertically or under your left breast horizontally, and start the measurement for 60 seconds. During the process, the phone will make sounds like a heart monitor."
   c. Ask if they are ready to try again.

0.1. If avg_bpm > 120 or (avg_bpm > 35 and avg_bpm < 50):
   a. Note that the heart rate is higher or lower than typical for a resting state.
   b. Ask about symptoms: "How are you feeling? Do you notice any chest pain, palpitations, or dizziness?"
   c. Suggest repeating after rest or consulting a professional.

1. If episodes_count == 0 (and avg_bpm is normal):
   a. State no abnormalities were detected.
   b. Ask: “Would you like general recommendations for maintaining heart health?”

2. If episodes_count > 0:
   a. Explain the findings (BPM and timing of episodes) in a conversational way.
   b. Ask how they felt during those specific moments.
   c. Advise repeating the measurement in 1–2 weeks and consulting a doctor.

Hard constraints:
• Never claim a definitive diagnosis.
• Ask max 2 questions per message to keep the conversation simple.
"""

class MathData(BaseModel):
    avg_bpm: Optional[float] = 0
    min_bpm: Optional[float] = 0
    max_bpm: Optional[float] = 0
    episodes_count: Optional[int] = 0
    episodes_per_hour: Optional[float] = 0
    episodes_timestamps: Optional[List[str]] = []

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: Optional[str] = None
    history: Optional[List[Message]] = []
    observation: Optional[Dict[str, Any]] = None

def parse_math_data(data: Dict[str, Any]) -> str:
    avg_bpm = round(data.get('avg_bpm', 0))
    min_bpm = round(data.get('min_bpm', 0))
    max_bpm = round(data.get('max_bpm', 0))
    episodes_count = data.get('episodes_count', 0)
    episodes_per_hour = data.get('episodes_per_hour', 0)
    
    # Critical Fix: episodes_timestamps is a list of lists [start, end]
    raw_timestamps = data.get('episodes_timestamps', [])
    formatted_ts = []
    for ts in raw_timestamps:
        if isinstance(ts, list):
            formatted_ts.append("-".join(str(i) for i in ts))
        else:
            formatted_ts.append(str(ts))
            
    timestamps_str = ", ".join(formatted_ts) if formatted_ts else "None"

    return f"""
--- CLINICAL MEASUREMENT REPORT ---
[Metric: Average Heart Rate]
Value: {avg_bpm} BPM
Description: The mean heart rate calculated during the measurement period.

[Metric: Heart Rate Range]
Value: Min {min_bpm} BPM - Max {max_bpm} BPM
Description: The minimum and maximum instantaneous heart rate values detected.

[Metric: Abnormal Episodes]
Value: {episodes_count} detected
Description: Total number of rhythmic anomalies or significant deviations from the baseline heart rate.

[Metric: Frequency of Anomalies]
Value: {episodes_per_hour:.1f} episodes per hour
Description: The extrapolated density of abnormal heart rhythm events.

[Metric: Event Timestamps]
Value: {timestamps_str}
Description: Precise time markers within the recording when anomalies were identified.
-----------------------------------
""".strip()

@app.post("/api/chat")
async def chat(request: ChatRequest):
    try:
        clean_history = [m.dict() for m in request.history if m.role != 'system']
        full_messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        if request.observation:
            async with httpx.AsyncClient() as client:
                math_res = await client.post(
                    "https://heartscan-api-175148683457.us-central1.run.app/api/v1/cardiolog/realtime_analysis",
                    json=request.observation,
                    headers={"X-API-Key": os.getenv("HEARTSCAN_API_KEY", "")},
                    timeout=30.0
                )

                if math_res.status_code != 200:
                    raise HTTPException(status_code=math_res.status_code, detail=f"Math API Error: {math_res.text}")

                math_data = math_res.json()

                if not math_data.get('avg_bpm') or math_data.get('avg_bpm') == 0:
                    error_msg = "Данные не смогли обработать, пожалуйста проведите измерени еще раз. Ляжте ровно, положите телефон посередине грудной клетки вертикально или под левой грудью горизонтально и запустите измерения на 60 секунд. В процессе измерения телефон будет издавать звуки как сердечный монитор."
                    
                    new_history = list(clean_history)
                    if request.message:
                        new_history.append({"role": "user", "content": request.message})
                    new_history.append({"role": "assistant", "content": error_msg})

                    return {
                        "response": error_msg,
                        "history": new_history
                    }

                full_messages.append({
                    "role": "system",
                    "content": f"User just performed a heart rhythm measurement. Results Summary:\n{parse_math_data(math_data)}"
                })

        full_messages.extend(clean_history)

        if request.message:
            full_messages.append({"role": "user", "content": request.message})
        elif request.observation:
            full_messages.append({"role": "user", "content": "Analyze my heart rhythm measurement."})

        async with httpx.AsyncClient() as client:
            llm_res = await client.post(
                "https://dr7.ai/api/v1/medical/chat/completions",
                json={
                    "model": "medgemma-27b-it",
                    "messages": full_messages,
                    "max_tokens": 1000,
                    "temperature": 0.7
                },
                headers={"Authorization": f"Bearer {os.getenv('DR7_API_KEY', '')}"},
                timeout=60.0
            )

            if llm_res.status_code != 200:
                raise HTTPException(status_code=llm_res.status_code, detail=f"LLM API Error: {llm_res.text}")

            llm_data = llm_res.json()
            ai_response = llm_data['choices'][0]['message']['content']

            new_history = list(clean_history)
            if request.message:
                new_history.append({"role": "user", "content": request.message})
            elif request.observation:
                new_history.append({"role": "user", "content": "Analyze my heart rhythm measurement."})
            new_history.append({"role": "assistant", "content": ai_response})

            return {
                "response": ai_response,
                "history": new_history
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
