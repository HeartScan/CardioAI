# CardioAI Product Test Harness (tests/)

Автономная система продуктового тестирования для демонстрации связки:
- Кардиолог — Dr7 (медицинская LLM, настройки в `cardioai_backend/config.ini`, ключи через ENV);
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
DR7_API_KEY="YOUR_DR7_KEY"
OPENAI_API_KEY="YOUR_OPENAI_KEY"
```

Ключи читаются только из переменных окружения.

## Запуск

- Все сценарии:
```bash
python tests/run.py --all
```

- Один сценарий:
```bash
python tests/run.py --scenario tests/scenarios/smoker_52f.json
```

- Прогнать первые N **наблюдений** из `peaks.pkl` (например, первые 100 для быстрого теста):
```bash
python tests/run.py --all --N 100
# или для одного сценария
python tests/run.py --scenario tests/scenarios/smoker_52f.json --N 100
```

- (Опционально) Ограничить число **пиков** внутри каждого наблюдения:
```bash
python tests/run.py --all --N 100 --peaksN 200
```

- Сгенерировать отчёт повторно (без выполнения):
```bash
python tests/run.py --report tests/runs/<run_folder>
```

## Структура

- `tests/run.py` — оркестратор: загрузка сценариев, запуск диалога, оценка, отчёт.
- `tests/providers/writer_adapter.py` — обёртка для LLM, повторяющая пайплайн: системный промпт из `cardioai_backend/config.ini`, первый ход `SCG data:\n{...}`.
- `tests/providers/openai_adapter.py` — клиент OpenAI Chat Completions API на официальном OpenAI SDK.
- `tests/prompts/*.txt` — системные промпты пациента и критика.
- `tests/scenarios/*.json` — сценарии пациентов (профили и ссылки на `tests/peaks.pkl`).
- `tests/report/render.py` — генерация `report.md` из JSON-логов.
- `tests/config.json` — параметры моделей/температур, лимиты ходов, директория результатов.

## Замечания

- Для расчёта метрик используется `cardioai_backend.scg.processing.preprocess_obs(...)` на основе `tests/peaks.pkl` (или указанных в сценарии пиков).
- Если ответ критика невалидный JSON, он сохраняется как `evaluation.json` с полем `raw` и ошибкой `non_json_response`.


