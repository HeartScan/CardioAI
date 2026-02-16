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
"[externals]/fs [external] (fs, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("fs", () => require("fs"));

module.exports = mod;
}),
"[externals]/path [external] (path, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("path", () => require("path"));

module.exports = mod;
}),
"[project]/src/app/api/chat/prompt.ts [app-route] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "SYSTEM_PROMPT",
    ()=>SYSTEM_PROMPT
]);
const SYSTEM_PROMPT = `
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
`;
}),
"[project]/src/app/api/chat/route.ts [app-route] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "POST",
    ()=>POST
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$server$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/server.js [app-route] (ecmascript)");
var __TURBOPACK__imported__module__$5b$externals$5d2f$fs__$5b$external$5d$__$28$fs$2c$__cjs$29$__ = __turbopack_context__.i("[externals]/fs [external] (fs, cjs)");
var __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__ = __turbopack_context__.i("[externals]/path [external] (path, cjs)");
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$app$2f$api$2f$chat$2f$prompt$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/src/app/api/chat/prompt.ts [app-route] (ecmascript)");
;
;
;
;
function parseMathData(data) {
    const avgBpm = Math.round(data.avg_bpm || 0);
    const minBpm = Math.round(data.min_bpm || 0);
    const maxBpm = Math.round(data.max_bpm || 0);
    const episodesCount = data.episodes_count || 0;
    const episodesPerHour = data.episodes_per_hour || 0;
    const episodesTimestamps = data.episodes_timestamps || [];
    return `
--- CLINICAL MEASUREMENT REPORT ---
[Metric: Average Heart Rate]
Value: ${avgBpm} BPM
Description: The mean heart rate calculated during the measurement period.

[Metric: Heart Rate Range]
Value: Min ${minBpm} BPM - Max ${maxBpm} BPM
Description: The minimum and maximum instantaneous heart rate values detected.

[Metric: Abnormal Episodes]
Value: ${episodesCount} detected
Description: Total number of rhythmic anomalies or significant deviations from the baseline heart rate.

[Metric: Frequency of Anomalies]
Value: ${episodesPerHour.toFixed(1)} episodes per hour
Description: The extrapolated density of abnormal heart rhythm events.

[Metric: Event Timestamps]
Value: ${episodesTimestamps.length > 0 ? episodesTimestamps.join(', ') : 'None'}
Description: Precise time markers within the recording when anomalies were identified.
-----------------------------------
`.trim();
}
async function POST(req) {
    try {
        const { message, history, observation } = await req.json();
        // Filter out any previous system messages from history to avoid duplicates
        const cleanHistory = (history || []).filter((m)=>m.role !== 'system');
        // We only keep the 'visible' conversation history (user and assistant messages)
        // and inject the secret system prompt and measurement data every time at the top.
        let fullMessages = [
            {
                role: "system",
                content: __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$app$2f$api$2f$chat$2f$prompt$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["SYSTEM_PROMPT"]
            }
        ];
        // If new measurement data provided, we add it as a fresh system context
        if (observation) {
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
            console.log("Math Data received:", mathData);
            // Validation logic: if math data is invalid, return instructions without calling LLM
            if (!mathData.avg_bpm || mathData.avg_bpm === 0) {
                const errorMsg = "Данные не смогли обработать, пожалуйста проведите измерени еще раз. Ляжте ровно, положите телефон посередине грудной клетки вертикально или под левой грудью горизонтально и запустите измерения на 60 секунд. В процессе измерения телефон будет издавать звуки как сердечный монитор.";
                const newHistory = [
                    ...cleanHistory
                ];
                if (message) newHistory.push({
                    role: "user",
                    content: message
                });
                newHistory.push({
                    role: "assistant",
                    content: errorMsg
                });
                return __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$server$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["NextResponse"].json({
                    response: errorMsg,
                    history: newHistory
                });
            }
            // Inject measurement data as system context
            fullMessages.push({
                role: "system",
                content: `User just performed a heart rhythm measurement. Results Summary:\n${parseMathData(mathData)}`
            });
        }
        // Add the conversation history
        fullMessages = [
            ...fullMessages,
            ...cleanHistory
        ];
        // Add new user message if provided
        if (message) {
            fullMessages.push({
                role: "user",
                content: message
            });
        } else if (observation) {
            // If it's a new measurement without a user message, 
            // we can add a placeholder to trigger the AI analysis response
            fullMessages.push({
                role: "user",
                content: "Analyze my heart rhythm measurement."
            });
        }
        // Call Dr7.ai API
        // Log to file instead of console to keep console clean
        const logDir = __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].join(process.cwd(), 'logs');
        if (!__TURBOPACK__imported__module__$5b$externals$5d2f$fs__$5b$external$5d$__$28$fs$2c$__cjs$29$__["default"].existsSync(logDir)) __TURBOPACK__imported__module__$5b$externals$5d2f$fs__$5b$external$5d$__$28$fs$2c$__cjs$29$__["default"].mkdirSync(logDir);
        const logFile = __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].join(logDir, 'llm_requests.log');
        const logEntry = `\n--- ${new Date().toISOString()} ---\n` + JSON.stringify(fullMessages, null, 2) + '\n';
        __TURBOPACK__imported__module__$5b$externals$5d2f$fs__$5b$external$5d$__$28$fs$2c$__cjs$29$__["default"].appendFileSync(logFile, logEntry);
        const llmRes = await fetch("https://dr7.ai/api/v1/medical/chat/completions", {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${process.env.DR7_API_KEY}`
            },
            body: JSON.stringify({
                model: "medgemma-27b-it",
                messages: fullMessages,
                max_tokens: 1000,
                temperature: 0.7
            })
        });
        if (!llmRes.ok) {
            const errorText = await llmRes.text();
            console.error(`LLM API Error ${llmRes.status}:`, errorText);
            throw new Error(`LLM API Error: ${llmRes.status} - ${errorText}`);
        }
        const llmData = await llmRes.json();
        __TURBOPACK__imported__module__$5b$externals$5d2f$fs__$5b$external$5d$__$28$fs$2c$__cjs$29$__["default"].appendFileSync(logFile, `\n--- Dr7.ai Response ---\n` + JSON.stringify(llmData, null, 2) + '\n');
        if (!llmData.choices || !llmData.choices[0] || !llmData.choices[0].message) {
            console.error("Unexpected Dr7.ai response structure:", llmData);
            throw new Error("Invalid response from Dr7.ai");
        }
        const aiResponse = llmData.choices[0].message.content;
        // We return only the clean history to the client
        const newHistory = [
            ...cleanHistory
        ];
        if (message) {
            newHistory.push({
                role: "user",
                content: message
            });
        } else if (observation) {
            newHistory.push({
                role: "user",
                content: "Analyze my heart rhythm measurement."
            });
        }
        newHistory.push({
            role: "assistant",
            content: aiResponse
        });
        return __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$server$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["NextResponse"].json({
            response: aiResponse,
            history: newHistory
        });
    } catch (error) {
        console.error(error);
        const errorMessage = error instanceof Error ? error.message : 'Internal Server Error';
        return __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$server$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["NextResponse"].json({
            error: errorMessage
        }, {
            status: 500
        });
    }
}
}),
];

//# sourceMappingURL=%5Broot-of-the-server%5D__db8764ef._.js.map