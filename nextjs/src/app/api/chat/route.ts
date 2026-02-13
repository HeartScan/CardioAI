import { NextResponse } from 'next/server';

export async function POST(req: Request) {
  try {
    const { message, history } = await req.json();
    
    // Add user message to history
    const updatedHistory = [...history, { role: "user", content: message }];

    // Call Dr7.ai API
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
