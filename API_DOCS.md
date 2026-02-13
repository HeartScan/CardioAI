# API Documentation: CardioAI

This document describes the API for communicating with the CardioAI backend.

## Base URL
The backend is currently configured to run on port `8000` by default.
In production, the base URL will be provided by the hosting platform (e.g., Render).

## Endpoints

### 1. Initialize Chat
**Endpoint:** `POST /api/init`

Used to start a new chat session and provide the measurement data (observation).

**Request Body:**
```json
{
  "observation": {
    "bpm": 74.8,
    "confidence": 0.93,
    "peaks": [
      { "x": 132, "y": 0.87 },
      { "x": 247, "y": 0.91 }
    ],
    "peaksCount": 6,
    "quality_score": 0.78,
    "is_noisy": false,
    "processingTime": "128.42 ms"
  }
}
```
*Note: The `observation` field can contain any JSON data returned by your SCG measurement module.*

**Response:**
```json
{
  "status": "initialized",
  "response": "Hello, I am CardioAI...",
  "history": [...]
}
```

### 2. Send Message
**Endpoint:** `POST /api/chat`

Used to send a user message and get a response from the AI.

**Request Body:**
```json
{
  "message": "What do these results mean?"
}
```

**Response:**
```json
{
  "response": "Based on your heart rate of 74.8 bpm...",
  "history": [...]
}
```

## Integration Steps for Frontend
1. Conduct measurement using the SCG module.
2. Format the result as a JSON object.
3. Send this object to `/api/init`.
4. Use the returned `response` to display the first AI message.
5. Continue the conversation using the `/api/chat` endpoint.
