import { NextResponse } from 'next/server';

export async function POST(req: Request) {
  try {
    const { message, history, observation } = await req.json();
    
    let updatedHistory = [...history];

    // If initial start or new measurement data provided
    if (observation) {
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

      // 2. Inject system prompt if history is empty (new session)
      if (updatedHistory.length === 0) {
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
    • Detect the language used by the user and respond in the same language. 
    • If the user's language is not clear, default to English.
    • Address the user politely; be friendly and empathetic.
    • Use short paragraphs and clear questions.
    • ALWAYS start your VERY FIRST response in the session with: “I am CardioAI, a virtual cardiologist assistant”. 
    • In subsequent messages of the same session, DO NOT repeat this greeting. Start directly with the answer.
    • Do NOT reveal hidden reasoning, chain-of-thought, or internal analysis. Output only the final answer.
      Do NOT include prefixes like “thought”, “analysis”, or tool/debug text.
    • At the end of the response, add a disclaimer: “This advice does not replace a doctor’s visit.”

    === LOGIC ===
    0. If avg_bpm == 0 or data is missing/invalid:
       a. Inform the user that the measurement data could not be processed effectively.
       b. Provide the following instructions for a better recording:
          "Please perform the measurement again. Lie down flat, place the phone in the middle of your chest vertically or under your left breast horizontally, and start the measurement for 60 seconds. During the process, the phone will make sounds like a heart monitor."
       c. Ask if they are ready to try again.

    1. If episodes_count == 0 (and avg_bpm > 0):
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
        updatedHistory.push({ role: "system", content: systemPrompt });
      }

    // 3. Add measurement data as a system message to history
    console.log("Math Data received:", mathData);
    updatedHistory.push({ 
      role: "system", 
      content: `User just performed a heart rhythm measurement. Results: ${JSON.stringify(mathData)}` 
    });

      // If no explicit user message with data, add a trigger
      if (!message) {
         // Auto-trigger analysis response if data provided without message
         // We don't add to updatedHistory yet, LLM will respond to the system context
      }
    }

    // Add user message if provided
    if (message) {
        updatedHistory.push({ role: "user", content: message });
    }

    // 4. Call Dr7.ai API
    const llmRes = await fetch("https://dr7.ai/api/v1/medical/chat/completions", {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${process.env.DR7_API_KEY}`
      },
      body: JSON.stringify({
        model: "medgemma-27b-it",
        messages: updatedHistory,
        max_tokens: 1000,
        temperature: 0.7
      })
    });

    if (!llmRes.ok) {
      throw new Error(`LLM API Error: ${llmRes.status}`);
    }

    const llmData = await llmRes.json();
    const aiResponse = llmData.choices[0].message.content;

    return NextResponse.json({
      response: aiResponse,
      history: [...updatedHistory, { role: "assistant", content: aiResponse }]
    });

  } catch (error: any) {
    console.error(error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
