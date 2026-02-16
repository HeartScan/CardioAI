module.exports = [
"[externals]/next/dist/compiled/next-server/app-route-turbo.runtime.dev.js [external] (next/dist/compiled/next-server/app-route-turbo.runtime.dev.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/compiled/next-server/app-route-turbo.runtime.dev.js", () => require("next/dist/compiled/next-server/app-route-turbo.runtime.dev.js"));

module.exports = mod;
}),
"[externals]/next/dist/compiled/@opentelemetry/api [external] (next/dist/compiled/@opentelemetry/api, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/compiled/@opentelemetry/api", () => require("next/dist/compiled/@opentelemetry/api"));

module.exports = mod;
}),
"[externals]/next/dist/compiled/next-server/app-page-turbo.runtime.dev.js [external] (next/dist/compiled/next-server/app-page-turbo.runtime.dev.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/compiled/next-server/app-page-turbo.runtime.dev.js", () => require("next/dist/compiled/next-server/app-page-turbo.runtime.dev.js"));

module.exports = mod;
}),
"[externals]/next/dist/server/app-render/work-unit-async-storage.external.js [external] (next/dist/server/app-render/work-unit-async-storage.external.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/server/app-render/work-unit-async-storage.external.js", () => require("next/dist/server/app-render/work-unit-async-storage.external.js"));

module.exports = mod;
}),
"[externals]/next/dist/server/app-render/work-async-storage.external.js [external] (next/dist/server/app-render/work-async-storage.external.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/server/app-render/work-async-storage.external.js", () => require("next/dist/server/app-render/work-async-storage.external.js"));

module.exports = mod;
}),
"[externals]/next/dist/shared/lib/no-fallback-error.external.js [external] (next/dist/shared/lib/no-fallback-error.external.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/shared/lib/no-fallback-error.external.js", () => require("next/dist/shared/lib/no-fallback-error.external.js"));

module.exports = mod;
}),
"[externals]/next/dist/server/app-render/after-task-async-storage.external.js [external] (next/dist/server/app-render/after-task-async-storage.external.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/server/app-render/after-task-async-storage.external.js", () => require("next/dist/server/app-render/after-task-async-storage.external.js"));

module.exports = mod;
}),
"[project]/src/app/api/init/route.ts [app-route] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "POST",
    ()=>POST
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$server$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/server.js [app-route] (ecmascript)");
;
async function POST(req) {
    try {
        const { observation } = await req.json();
        // 1. Call HeartScan Math API
        const mathRes = await fetch("https://heartscan-api-175148683457.us-central1.run.app/api/v1/cardiolog/realtime_analysis", {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': process.env.HEARTSCAN_API_KEY || ''
            },
            body: JSON.stringify(observation)
        });
        if (!mathRes.ok) {
            throw new Error(`Math API Error: ${mathRes.status}`);
        }
        const mathData = await mathRes.json();
        // 2. Prepare context for LLM
        const systemPrompt = `
    You are CardioAI, a virtual cardiologist assistant operating in a remote pre-triage mode.
    Along with this prompt, you will receive a JSON object containing the results of a home heart
    rhythm recording. The format is strictly the following:

    {
      "avg_bpm": <float>,               // average heart rate
      "min_bpm": <float>,               // minimum heart rate
      "max_bpm": <float>,               // maximum heart rate
      "episodes_count": <int>,          // number of deviation episodes
      "episodes_per_hour": <float>,     // estimated episode frequency per hour
      "episodes_timestamps": [          // array of [start, end] pairs in HH:MM:SS
        ["09:12:03","09:12:15"], ...
      ]
    }

    === GENERAL RESPONSE RULES ===
    • Answer in English.
    • Address the user politely; be friendly and empathetic.
    • Use short paragraphs and clear questions.
    • Always start with: “I am CardioAI, a virtual cardiologist assistant”.
    • Do NOT reveal hidden reasoning, chain-of-thought, or internal analysis. Output only the final answer.
      Do NOT include prefixes like “thought”, “analysis”, or tool/debug text.
    • At the end of the response, add a disclaimer: “This advice does not replace a doctor’s visit.”

    === LOGIC ===
    1. If episodes_count == 0:
       a. State that no rhythm abnormalities were detected.
       b. Ask: “Would you like general recommendations for maintaining heart health?”
       c. If the user answers “no” → say goodbye.
          If “yes” → ask the questions from Block 1 (questionnaire / risk factors)
          and provide general preventive recommendations.

    2. If episodes_count > 0:
       a. Provide a brief summary (avg/min/max BPM, episodes_count, episodes_per_hour)
          and list the episode time windows from episodes_timestamps.
       b. Ask the questions from Block 4 (how the user felt during the recording).
       c. Then ask the questions from Block 1 (questionnaire / risk factors).
       d. Provide lifestyle recommendations and suggest additional examinations,
          and add: “We recommend repeating the measurement in 1–2 weeks (or as directed by a doctor)
          to clarify the trend over time.”

    === BLOCK 1. Questionnaire and risk factors ===
    • What is your sex?
    • What is your age?
    • Which region do you live in?
    • Do you smoke? If yes — for how long and how much?
    • Do you have high blood pressure?
    • Do you know your cholesterol levels / lipid profile results?

    === BLOCK 4. Brief self-assessment during the recording ===
    During the episode time windows listed in episodes_timestamps, did you experience:
    • Chest pain or discomfort?
    • Palpitations / skipped beats?
    • Dizziness, shortness of breath, weakness?
    • Anything else (please describe)?
    `;
        const messages = [
            {
                role: "system",
                content: systemPrompt
            },
            {
                role: "system",
                content: `Measurement Results: ${JSON.stringify(mathData)}`
            }
        ];
        // 3. Call Dr7.ai API
        const llmRes = await fetch("https://dr7.ai/api/v1/medical/chat/completions", {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${process.env.DR7_API_KEY}`
            },
            body: JSON.stringify({
                model: "medgemma-27b-it",
                messages: messages,
                max_tokens: 1000,
                temperature: 0.7
            })
        });
        if (!llmRes.ok) {
            throw new Error(`LLM API Error: ${llmRes.status}`);
        }
        const llmData = await llmRes.json();
        const aiResponse = llmData.choices[0].message.content;
        return __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$server$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["NextResponse"].json({
            status: "initialized",
            response: aiResponse,
            history: messages // Return history so client can send it back
        });
    } catch (error) {
        console.error(error);
        return __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$server$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["NextResponse"].json({
            error: error.message
        }, {
            status: 500
        });
    }
}
}),
];

//# sourceMappingURL=%5Broot-of-the-server%5D__e7e374ad._.js.map