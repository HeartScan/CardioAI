# API Documentation: CardioAI

This document describes the API for communicating with the CardioAI backend.

## Base URL
The backend is currently configured to run on port `8000` by default.
In production, the base URL will be provided by the hosting platform (e.g., Render).

## Endpoints

### 1. Chat (canonical)
**Endpoint:** `POST /api/chat`

Used to send a user message and get a response from the AI.

**Request Body:**
```json
{
  "message": "What do these results mean?",
  "history": [
    { "role": "user", "content": "..." },
    { "role": "assistant", "content": "..." }
  ],
  "observation": {
    "...": "raw SCG payload (optional)"
  }
}
```

**Response:**
```json
{
  "response": "Based on your heart rate of 74.8 bpm...",
  "history": [
    { "role": "user", "content": "..." },
    { "role": "assistant", "content": "..." }
  ]
}
```

## Integration Steps for Frontend
1. Conduct measurement using the SCG module.
2. Send the measurement payload as `observation` to `/api/chat`.
3. Display the returned `response`.
4. Continue the conversation by sending `message` + `history` to `/api/chat`.
