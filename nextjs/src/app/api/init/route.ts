import { NextResponse } from 'next/server';

export async function POST(req: Request) {
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
    const systemPrompt = `You are CardioAI, a virtual cardiologist assistant operating in a remote pre-triage mode... (etc)`; // Simplified for now
    const messages = [
      { role: "system", content: systemPrompt },
      { role: "system", content: `Measurement Results: ${JSON.stringify(mathData)}` }
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

    return NextResponse.json({
      status: "initialized",
      response: aiResponse,
      history: messages // Return history so client can send it back
    });

  } catch (error: any) {
    console.error(error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
