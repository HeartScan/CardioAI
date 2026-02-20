<div align="center">
  <h1>CardioAI: MedGemma-Powered Clinical Support</h1>
  <p>
    <b>An advanced clinical support system leveraging Google's MedGemma for structured seismocardiography (SCG) analysis and agentic medical workflows.</b>
  </p>
  <p>
    <a href="#-medgemma--agentic-workflow">MedGemma Workflow</a> •
    <a href="#-key-features">Key Features</a> •
    <a href="#-tech-stack">Tech Stack</a> •
    <a href="#-getting-started">Getting Started</a>
  </p>
</div>

---

**CardioAI** is a groundbreaking clinical support system designed for the Google competition. It demonstrates the power of **MedGemma** in making primary cardiac diagnostics accessible. By capturing seismocardiograms (SCG) via smartphone accelerometers, CardioAI provides a non-invasive, AI-orchestrated platform for preliminary heart rhythm assessment and structured clinical decision-making.

## 🧠 MedGemma & Agentic Workflow

At the core of CardioAI is **Google's MedGemma** (hosted via Dr7.ai), which transforms raw signal data into actionable clinical intelligence through a structured agentic workflow. This is not just a chat interface; it's a diagnostic assistant that follows professional medical protocols:

1.  **Structured Interpretation:** MedGemma analyzes mathematical signal features (BPM, episodes, anomalies) to provide a clinical-grade assessment.
2.  **Clinical Triage & Logic:** The model acts as an agent, performing triage based on the captured data and initiating targeted follow-up questions to refine its analysis.
3.  **Clinician Notes:** Automatically generates structured professional summaries for healthcare providers, facilitating faster and more accurate reviews.
4.  **Patient-Centric Explanation:** Translates complex SCG findings into clear, understandable language for the patient, aligned with **HAI-DEF** (Human-Centered AI Design Framework) principles for transparency and trust.

---

## ✨ Key Features

- **MedGemma AI Orchestration:** Structured medical reasoning and agentic diagnostic workflows.
- **Real-Time SCG Data Capture:** Direct browser-based accelerometer recording using modern Web APIs.
- **On-Device History & Storage:** Seamless Local Storage integration for instant review of past measurements without server dependency.
- **Professional Signal Visualization:**
  - **Standard View:** Interactive zoomed chart with a full-signal overview for precise navigation.
  - **Split View (High-Res):** Multi-chart sequential analysis for deep dives into cardiac mechanical activity.
  - **Mobile-First Design:** Fully optimized for touch-based clinical environments.

## 🛠️ Tech Stack

| Area | Technology | Purpose |
| :--- | :--- | :--- |
| **AI Engine** | [**Google MedGemma**](https://ai.google.dev/gemma) | Primary intelligence for structured medical analysis and agentic workflow. |
| **Backend** | [**FastAPI**](https://fastapi.tiangolo.com/) | High-performance Python orchestration layer for AI and signal processing. |
| **Frontend** | [**Next.js**](https://nextjs.org/) (React) | Mobile-first, responsive interface with Server-Side Rendering. |
| **Visualization**| [**uPlot**](https://github.com/leeoniya/uPlot) | Memory-efficient charting engine for high-frequency medical signals. |
| **UI/UX** | [**shadcn/ui**](https://ui.shadcn.com/) & [**Radix**](https://www.radix-ui.com/) | Accessible, Human-Centered unstyled components. |

## 🏁 Getting Started

### Prerequisites
- Python 3.8+ | Node.js 18.17+

### Startup
1.  **Backend:** `cd cardioai_backend && pip install -r requirements.txt && python main.py`
2.  **Frontend:** `cd cardioai_frontend && npm install && npm run dev`

---

## 📚 Educational Resources & Open Source

### Seismocardiography (SCG)
*   **[What is SCG?](https://heartscan.app/about-scg)** — Capturing cardiac mechanical work (valves, contraction) via accelerometry.
*   **[Interpretation Guide](https://heartscan.app/primary-care-guide)** — Visual patterns for PAC, PVC, and AFib.

### Open Source Initiative
*   **[OpenSCG](https://github.com/HeartScan/openSCG)** — Transforming any smartphone into a clinical seismocardiography sensor.

---
*Disclaimer: This application is for demonstration and research purposes only. It is not a certified medical device and does not replace professional medical consultation.*
