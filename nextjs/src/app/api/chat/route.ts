import { NextResponse } from 'next/server';
import { SYSTEM_PROMPT } from './prompt';

export async function POST(req: Request) {
  try {
    const { message, history, observation } = await req.json();
    
    // We only keep the 'visible' conversation history (user and assistant messages)
    // and inject the secret system prompt and measurement data every time at the top.
    let fullMessages = [{ role: "system", content: SYSTEM_PROMPT }];

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
      
      // Inject measurement data as system context
      fullMessages.push({ 
        role: "system", 
        content: `User just performed a heart rhythm measurement. Results: ${JSON.stringify(mathData)}` 
      });
    }

    // Filter out any previous system messages from history to avoid duplicates
    const cleanHistory = history.filter((m: any) => m.role !== 'system');
    
    // Add the conversation history
    fullMessages = [...fullMessages, ...cleanHistory];

    // Add new user message if provided
    if (message) {
        fullMessages.push({ role: "user", content: message });
    }

    // Call Dr7.ai API
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
      throw new Error(`LLM API Error: ${llmRes.status}`);
    }

    const llmData = await llmRes.json();
    const aiResponse = llmData.choices[0].message.content;

    // We return only the clean history to the client
    const newHistory = [...cleanHistory];
    if (message) newHistory.push({ role: "user", content: message });
    newHistory.push({ role: "assistant", content: aiResponse });

    return NextResponse.json({
      response: aiResponse,
      history: newHistory
    });

  } catch (error: any) {
    console.error(error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
