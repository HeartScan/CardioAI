'use client';

import { useEffect, useRef, useState } from "react";

interface Message {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

export default function App() {
  const [history, setHistory] = useState<Message[]>([]);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [dataset, setDataset] = useState<any[]>([]);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Load dataset on mount
  useEffect(() => {
    fetch('/dataset.json')
      .then(res => res.json())
      .then(data => setDataset(data))
      .catch(err => console.error("Failed to load dataset:", err));
  }, []);

  // Auto-scroll
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [history]);

  // Unified function to send messages or data
  async function callApi(userMessage: string | null, observation: any | null) {
    if (busy) return;
    try {
      setBusy(true);
      
      if (userMessage) {
        setHistory(prev => [...prev, { role: "user", content: userMessage }]);
        setMessage("");
      }

      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
            message: userMessage, 
            history: history,
            observation: observation 
        }),
      });

      if (!res.ok) throw new Error(`API failed: ${res.status}`);
      const data = await res.json();

      setHistory(data.history);
    } catch (err: any) {
      alert("Error: " + err.message);
    } finally {
      setBusy(false);
    }
  }

  const sendRandomMeasurement = () => {
    if (dataset.length === 0) {
        alert("Dataset not loaded yet");
        return;
    }
    const randomIndex = Math.floor(Math.random() * dataset.length);
    const item = dataset[randomIndex];
    
    console.log(`Sending measurement from file: ${item.filename}`);
    
    const observation = {
        az_data_array: item.az_data_array,
        device: { userAgent: navigator.userAgent, platform: navigator.platform }
    };
    callApi(null, observation);
  };

  function handleKey(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      callApi(message, null);
    }
  }

  return (
    <div className="chat-wrapper" style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
      <header style={{ fontSize: '24px', fontWeight: 'bold', marginBottom: '20px' }}>
        CardioAI Chat (Dataset Demo)
      </header>

      <div style={{ marginBottom: '10px', display: 'flex', gap: '10px' }}>
        <button 
          onClick={sendRandomMeasurement}
          style={{ padding: '8px 15px', backgroundColor: '#4caf50', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
          disabled={busy || dataset.length === 0}
        >
          🎲 Send Random Real Measurement ({dataset.length} available)
        </button>
        
        <button 
          onClick={() => setHistory([])}
          style={{ padding: '8px 15px', backgroundColor: '#f44336', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
          disabled={busy}
        >
          🗑️ Clear Chat
        </button>
      </div>

      <div className="chat-window" style={{ height: '500px', overflowY: 'auto', border: '1px solid #ccc', padding: '10px', marginBottom: '20px', backgroundColor: '#fff' }}>
        {history.length === 0 && (
            <div style={{ color: '#888', textAlign: 'center', marginTop: '100px' }}>
                No conversation yet. Click the green button to send real clinical data!
            </div>
        )}
        {history
          .filter(m => m.role !== "system")
          .map((m, i) => (
          <div key={i} className={`msg ${m.role}`} style={{ 
            marginBottom: '15px', 
            padding: '12px', 
            borderRadius: '12px',
            backgroundColor: m.role === 'user' ? '#e3f2fd' : '#f1f1f1',
            textAlign: m.role === 'user' ? 'right' : 'left',
            maxWidth: '80%',
            marginLeft: m.role === 'user' ? 'auto' : '0'
          }}>
            <div style={{ fontSize: '12px', color: '#666', marginBottom: '4px' }}>
                {m.role === 'user' ? 'You' : 'CardioAI'}
            </div>
            <div style={{ whiteSpace: 'pre-wrap' }}>{m.content}</div>
          </div>
        ))}
        {busy && <div className="msg assistant italic" style={{ color: '#888' }}>CardioAI is thinking...</div>}
        <div ref={bottomRef} />
      </div>

      <form className="input-bar" onSubmit={(e) => { e.preventDefault(); callApi(message, null); }} style={{ display: 'flex', gap: '10px' }}>
        <textarea
          placeholder="Type your message..."
          value={message}
          disabled={busy}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKey}
          style={{ flex: 1, padding: '12px', borderRadius: '8px', border: '1px solid #ccc', resize: 'none', height: '50px' }}
        />
        <button type="submit" disabled={busy || !message.trim()} style={{ 
            padding: '0 25px', 
            backgroundColor: '#2196f3', 
            color: 'white', 
            border: 'none', 
            borderRadius: '8px', 
            cursor: 'pointer',
            fontSize: '20px'
        }}>
          ⇧
        </button>
      </form>
    </div>
  );
}
