# CardioAI Product Test Harness (tests/)

Автономная система продуктового тестирования для демонстрации связки:
- Кардиолог — Writer Palmyra (через существующий `WriterChatSession` и `config.ini`);
- Пациент — ChatGPT (OpenAI Chat Completions API);
- Критик — ChatGPT (оценка по рубрике).

Результаты диалога, метаданные и оценка сохраняются в `tests/runs/<scenario>_<timestamp>/`.

## Подготовка

1) Установите зависимости (корневые `requirements.txt` достаточно):
```bash
pip install -r requirements.txt
```

2) Переменные окружения:
- В корне `.env` или в `tests/.env` укажите:
```dotenv
WRITER_API_KEY="YOUR_WRITER_KEY"
OPENAI_API_KEY="YOUR_OPENAI_KEY"
```

## Запуск

- Все сценарии:
```bash
python tests/run.py --all
```

- Один сценарий:
```bash
python tests/run.py --scenario tests/scenarios/smoker_52f.json
```

- Ограничить число пиков из `peaks.pkl` (например, первые 100 для быстрого теста):
```bash
python tests/run.py --all --N 100
# или для одного сценария
python tests/run.py --scenario tests/scenarios/smoker_52f.json --N 100
```

- Сгенерировать отчёт повторно (без выполнения):
```bash
python tests/run.py --report tests/runs/<run_folder>
```

## Структура

- `tests/run.py` — оркестратор: загрузка сценариев, запуск диалога, оценка, отчёт.
- `tests/providers/writer_adapter.py` — обёртка Writer на базе существующего `WriterChatSession`, максимально повторяющая прод-пайплайн (системный промпт из `config.ini`, первый ход `SCG data:\n{...}`).
- `tests/providers/openai_adapter.py` — минимальный клиент OpenAI Chat Completions API на stdlib.
- `tests/prompts/*.txt` — системные промпты пациента и критика.
- `tests/scenarios/*.json` — сценарии пациентов (профили и ссылки на `tests/peaks.pkl`).
- `tests/report/render.py` — генерация `report.md` из JSON-логов.
- `tests/config.json` — параметры моделей/температур, лимиты ходов, директория результатов.

## Замечания

- Для расчёта метрик используется `utils.preprocess_obs(...)` на основе `tests/peaks.pkl` (или указанных в сценарии пиков), полностью совпадая с прод-логикой.
- Если ответ критика невалидный JSON, он сохраняется как `evaluation.json` с полем `raw` и ошибкой `non_json_response`.


