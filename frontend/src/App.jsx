import { useEffect, useRef, useState } from "react";

/**
 * Очень простой чат-клиент.
 * ⏳  На загрузке выполняет POST /api/init
 * 💬  Далее общается через POST /api/chat
 */
export default function App() {
  /** История сообщений [{role: 'assistant'|'user', text: string}] */
  const [history, setHistory] = useState([]);
  /** Текст в input */
  const [message, setMessage] = useState("");
  /** Блокируем ввод, пока ждём ответ сервера */
  const [busy, setBusy] = useState(false);
  const bottomRef = useRef(null); // автоскролл

  // ----- 1. Инициализация чата -----
  useEffect(() => {
    async function initChat() {
      try {
        setBusy(true);
        const res = await fetch("/api/init", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            // TODO: если нужно — подставьте реальные данные наблюдения
            observation: {
                          bpm: 74.8,
                          confidence: 0.93,
                          peaks: [
                            { x: 132, y: 0.87 },
                            { x: 247, y: 0.91 },
                            { x: 364, y: 0.88 },
                            { x: 480, y: 0.90 },
                            { x: 596, y: 0.85 },
                            { x: 713, y: 0.89 }
                          ],
                          peaksCount: 6,
                          quality_score: 0.78,
                          is_noisy: false,
                          processingTime: "128.42 ms"
                        }
          }),
        });

        if (!res.ok) throw new Error(`init_chat failed: ${res.status}`);
        const data = await res.json();

        // сервер возвращает { status, response, history? }
        setHistory((h) => [
          ...h,
          { role: "assistant", text: data.response ?? "🤖 (no response)" },
        ]);
      } catch (err) {
        console.error(err);
        alert("Не удалось инициализировать чат");
      } finally {
        setBusy(false);
      }
    }

    initChat();
  }, []);

  // автоскролл к последнему сообщению
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [history]);

  // ----- 2. Отправка пользовательского сообщения -----
  async function sendMessage() {
    if (!message.trim()) return;
    try {
      setBusy(true);
      // добавляем реплику пользователя локально
      setHistory((h) => [...h, { role: "user", text: message }]);
      setMessage("");

      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
      });

      if (!res.ok) throw new Error(`chat failed: ${res.status}`);
      const data = await res.json();

      setHistory((h) => [
        ...h,
        { role: "assistant", text: data.response ?? "🤖 (no response)" },
      ]);
    } catch (err) {
      console.error(err);
      alert("Ошибка при обращении к модели");
    } finally {
      setBusy(false);
    }
  }

  // отправка по Enter
  function handleKey(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  // ----- 3. UI -----
  return (
    <div className="chat-wrapper">
      <header>CardioAI Chat</header>

      <div className="chat-window">
        {history.map((m, i) => (
          <div key={i} className={`msg ${m.role}`}>
            {m.text}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      <form
        className="input-bar"
        onSubmit={(e) => {
          e.preventDefault();
          sendMessage();
        }}
      >
        <textarea
          placeholder="Ваше сообщение…"
          value={message}
          disabled={busy}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKey}
        />
        <button type="submit" disabled={busy || !message.trim()}>
          ⇧
        </button>
      </form>
    </div>
  );
}
