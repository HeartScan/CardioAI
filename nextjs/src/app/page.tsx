'use client';

import { useEffect, useRef, useState } from "react";

interface Message {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

export default function App() {
  /** Full history for stateless backend */
  const [history, setHistory] = useState<Message[]>([]);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  // ----- 1. Initialize Chat -----
  useEffect(() => {
    async function initChat() {
      try {
        setBusy(true);
        const res = await fetch("/api/init", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            observation: {
                az_data_array: [
                    {"ax": 0.01, "ay": -0.02, "az": 9.81, "timestamp": Date.now()}
                    // Real data should be many points
                ],
                device: { userAgent: navigator.userAgent, platform: navigator.platform }
            }
          }),
        });

        if (!res.ok) throw new Error(`init failed: ${res.status}`);
        const data = await res.json();

        // Save full history from server
        setHistory(data.history);
      } catch (err) {
        console.error(err);
      } finally {
        setBusy(false);
      }
    }

    initChat();
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [history]);

  // ----- 2. Send Message -----
  async function sendMessage() {
    if (!message.trim() || busy) return;
    try {
      setBusy(true);
      const userMessage = message;
      setMessage("");

      // Optimistic update
      const updatedHistory: Message[] = [...history, { role: "user", content: userMessage }];
      setHistory(updatedHistory);

      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
            message: userMessage, 
            history: history // Send full history back
        }),
      });

      if (!res.ok) throw new Error(`chat failed: ${res.status}`);
      const data = await res.json();

      // Update with full history from server (syncs states)
      setHistory(data.history);
    } catch (err) {
      console.error(err);
    } finally {
      setBusy(false);
    }
  }

  function handleKey(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  return (
    <div className="chat-wrapper" style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
      <header style={{ fontSize: '24px', fontWeight: 'bold', marginBottom: '20px' }}>
        CardioAI Chat (Stateless Next.js)
      </header>

      <div className="chat-window" style={{ height: '400px', overflowY: 'auto', border: '1px solid #ccc', padding: '10px', marginBottom: '20px' }}>
        {history
          .filter(m => m.role !== "system")
          .map((m, i) => (
          <div key={i} className={`msg ${m.role}`} style={{ 
            marginBottom: '10px', 
            padding: '10px', 
            borderRadius: '8px',
            backgroundColor: m.role === 'user' ? '#e3f2fd' : '#f5f5f5',
            textAlign: m.role === 'user' ? 'right' : 'left'
          }}>
            <strong>{m.role === 'user' ? 'You' : 'CardioAI'}:</strong> {m.content}
          </div>
        ))}
        {busy && <div className="msg assistant italic">Thinking...</div>}
        <div ref={bottomRef} />
      </div>

      <form className="input-bar" onSubmit={(e) => { e.preventDefault(); sendMessage(); }} style={{ display: 'flex', gap: '10px' }}>
        <textarea
          placeholder="Type your message..."
          value={message}
          disabled={busy}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKey}
          style={{ flex: 1, padding: '10px', borderRadius: '4px', border: '1px solid #ccc' }}
        />
        <button type="submit" disabled={busy || !message.trim()} style={{ padding: '10px 20px', cursor: 'pointer' }}>
          ⇧
        </button>
      </form>
    </div>
  );
}
