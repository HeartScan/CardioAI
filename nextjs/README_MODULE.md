# CardioAI Next.js Module Documentation

This module implements a stateless "AI Arrhythmologist" chat orchestrator using Next.js.

## Current Architecture Status

The project has been migrated to a modern **Stateless Architecture** suitable for Vercel deployment. It acts as an orchestrator between raw clinical data and AI interpretation.

### Core Components
1.  **Frontend (`src/app/page.tsx`)**:
    *   Manages the conversation history state.
    *   Sends the full history back to the server on every request (Stateless).
    *   Includes a Demo Button that selects a random clinical signal from `public/dataset.json`.
2.  **API Layer (`src/app/api/chat/route.ts`)**:
    *   **Orchestrator**: Receives requests, calls the external HeartScan Math API, then calls the Medical LLM API.
    *   **Valdidator**: Implements immediate response for invalid/low-quality data (`avg_bpm: 0`) without calling the expensive LLM.
    *   **Context Builder**: Dynamically builds the full AI prompt on every request using `prompt.ts` + clinical data + conversation history.
3.  **Prompt Engine (`src/app/api/chat/prompt.ts`)**:
    *   Contains the "AI Arrhythmologist" persona, clinical rules, and instructions for empathetic, human-like responses.

### Data Flow
1.  **Client** sends `observation` (az_data_array) + current `history`.
2.  **Server** calls `HeartScan API` -> receives math stats (avg_bpm, episodes).
3.  **Server** validates data. If bad -> returns instructions. If good -> calls `Dr7.ai API`.
4.  **LLM** generates response based on the hidden prompt and clinical stats.
5.  **Client** receives the response and updated history.

## Environment Variables (Required)
- `HEARTSCAN_API_KEY`: Key for the external Math analysis service.
- `DR7_API_KEY`: Key for the Medical LLM service (Dr7.ai).

## Clinical Dataset
The demo uses `public/dataset.json`, which was derived directly from `cardiolog_dataset.csv`. It contains 10 real clinical measurements (AO/AC/Anomalies) for testing purposes.

## Setup & Deployment
1.  **Local**: `cd nextjs && npm install && npm run dev`
2.  **Deployment**: Push to GitHub and connect to Vercel (set Root Directory to `nextjs`).
