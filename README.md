# CardioAI

**CardioAI** is a demonstration web application that leverages Artificial Intelligence for primary heart rhythm analysis based on Seismocardiography (SCG). The application transforms a smartphone into a diagnostic tool capable of capturing subtle chest vibrations caused by cardiac activity.

---

## 📂 Project Structure

The project is divided into two main parts:

*   **`cardioai_backend/`**: A **FastAPI**-based backend. It handles data orchestration and communicates with the Math API (signal analysis) and the Dr7 API (medical LLM model).
*   **`cardioai_frontend/`**: A **Next.js**-based frontend. It provides a chat interface, real-time accelerometer data capture, and visualization of the measurement process.

---

## ⚙️ Environment Setup

To run the application, you need to configure environment variables. Each folder (`cardioai_backend` and `cardioai_frontend`) contains an `.env.example` file that can be used as a template.

### 🐍 Backend (`cardioai_backend/.env`)
| Variable | Description |
| :--- | :--- |
| `HEARTSCAN_API_KEY` | API key for the HeartScan Math API to analyze SCG signals. |
| `DR7_API_KEY` | API key for Dr7.ai to access the medical LLM. |
| `PORT` | Port on which the server will run (default is 8000). |

### Backend config (`cardioai_backend/config.ini`)

- The **system prompt** is stored in `cardioai_backend/config.ini` (`[DEFAULT] SYSTEM_PROMPT`).
- Dr7/HeartScan endpoints and LLM parameters are also configurable there.

### Secrets

- Set `HEARTSCAN_API_KEY` / `DR7_API_KEY` via environment variables (recommended for both local dev and production).

### ⚛️ Frontend (`cardioai_frontend/.env`)
| Variable | Description |
| :--- | :--- |
| `CARDIOAI_BACKEND_URL` | The URL of your deployed backend (e.g., on Render). |

---

## 🚀 Local Startup

### 1. Start the Backend
```bash
cd cardioai_backend
python -m venv venv
source venv/bin/activate  # For Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### 2. Start the Frontend
```bash
cd cardioai_frontend
npm install
npm run dev
```

---

## 🌍 Deployment (Production)

### Backend (Render)
1. Create a new **Web Service** on Render.com.
2. Root Directory: (leave empty, or set to the repository root).
3. Build Command: `pip install -r cardioai_backend/requirements.txt`.
4. Start Command: `python -m cardioai_backend.main`.
5. Add the API keys in the **Environment Variables** section.

### Frontend (Vercel)
1. Create a new project on Vercel.com.
2. Specify the Root Directory: `cardioai_frontend`.
3. Framework Preset: `Next.js`.
4. Add `CARDIOAI_BACKEND_URL` to the Environment Variables.
5. Click **Deploy**.

---

## 📚 Resources and Technologies

### Seismocardiography (SCG)
*   **[What is SCG?](https://heartscan.app/about-scg)** — A detailed explanation of capturing cardiac mechanical vibrations using an accelerometer. Unlike ECG (electrical signals), SCG measures the mechanical work of the heart (valve opening/closing, ventricular contraction).
*   **[Interpretation Guide](https://heartscan.app/primary-care-guide)** — A practical visual guide to SCG waveforms for primary care physicians. It helps in recognizing patterns (PAC, PVC, Atrial Fibrillation) based on mechanical signals.

### Open Source
*   **[OpenSCG](https://github.com/HeartScan/openSCG)** — An open-source infrastructure project aiming to turn any smartphone into a seismocardiography sensor, removing hardware cost barriers in telemedicine.

---
*Disclaimer: This application is intended for educational and demonstration purposes only and does not replace a visit to a doctor.*
