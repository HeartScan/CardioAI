# CardioAI

Веб-приложение-чат-бот для первичного анализа записи сердечного ритма (SCG / ECG).  
**Бэкенд** — FastAPI, **LLM-клиент** — WriterAI, **фронтенд** — React + Vite.

---

## 1 . Структура репозитория

```text
cardioai/
│
├── server.py          ── FastAPI-роуты (/api/init, /api/chat)
├── controller.py      ── слой Controller (логика диалога)
├── chat_model.py      ── WriterChatSession (обёртка LLM)
├── utils.py           ── вспомогательные функции
├── config.ini         ── SYSTEM_PROMPT и прочие настройки
├── requirements.txt
│
└── frontend/          ── React-SPA
    ├── vite.config.js ── proxy на бекенд
    ├── src/
    │   ├── App.jsx
    │   └── main.jsx
    └── package.json
```

---

## 2 . Требования

| ПО                | Минимальная версия |
|-------------------|--------------------|
| **Python**        | ≥ 3.9              |
| **Node.js / npm** | ≥ 18 / 9           |
| **WriterAI API**  | действующий ключ   |

---

## 3 . Переменные окружения

Создайте файл **`.env`** в корневой директории:

```dotenv
WRITER_API_KEY="YOUR_WRITER_KEY"
```

Файл автоматически загружается библиотекой `python-dotenv` или
передаётся Uvicorn через `--env-file`.

---

## 4 . Быстрый запуск (режим разработки)

### 4 .1 Backend

```bash
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn server:app --reload --env-file .env          # http://localhost:8000
```

### 4 .2 Frontend

```bash
cd frontend
npm install
npm run dev                                          # http://localhost:5173
```

> В `frontend/vite.config.js` уже настроен proxy, поэтому запросы к `/api/*`
> автоматически перенаправляются на порт 8000.

---

## 5 . Сборка production-версии

```bash
# фронтенд
cd frontend
npm run build            # сборка в frontend/dist
cd ..

# бекенд
uvicorn server:app --host 0.0.0.0 --port 8000 --env-file .env
```

_Статические файлы `dist/` можно обслуживать nginx или `StaticFiles` FastAPI._

---

## 6 . Архитектура MVC

| Слой        | Файл / директория      | Описание                             |
|-------------|------------------------|--------------------------------------|
| **Model**   | `chat_model.py`        | `WriterChatSession` — работа с LLM   |
| **Controller** | `controller.py`     | логика диалога, история сообщений    |
| **View**    | `frontend/src`         | React-SPA                            |

REST-эндпоинты:

| Метод | URL          | Назначение                                       |
|-------|--------------|--------------------------------------------------|
| POST  | `/api/init`  | передаёт наблюдение, возвращает первый ответ LLM |
| POST  | `/api/chat`  | отправка пользовательского сообщения             |

