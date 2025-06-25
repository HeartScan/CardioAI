# CardioAI

Веб‑ориентированный чат‑бот для анализа наблюдений сердечного ритма.

## Запуск backend

```bash
pip install fastapi uvicorn writerai python-dotenv
uvicorn server:app --reload
```

## Запуск frontend

```bash
cd frontend
npm install
npm run dev
```

## Архитектура

- **Model** – класс `WriterChatSession` в `chat_model.py` инициализирует LLM.
- **Controller** – класс `Controller` в `controller.py` обрабатывает диалог.
- **View** – React‑интерфейс в директории `frontend`.

Фронтенд общается с сервером через REST‑эндпоинты `/api/init` и `/api/chat`.
