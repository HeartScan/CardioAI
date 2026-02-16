# Пакет миграции логики обработки данных CardioAI

Этот пакет содержит всё необходимое для переноса математической логики анализа сердцебиения в ваш существующий API-сервис.

## Содержимое
- `processing_logic.py` — основные функции анализа (numpy/scipy).
- `requirements.txt` — необходимые зависимости.

## Инструкция по интеграции

### 1. Установка зависимостей
Добавьте в ваш `requirements.txt` следующие библиотеки:
```
numpy
scipy
```

### 2. Перенос кода
Скопируйте все функции из файла `processing_logic.py` в ваш проект. Вы можете импортировать их или вставить напрямую в файл с эндпоинтами.

### 3. Создание эндпоинта (FastAPI пример)

Добавьте новый эндпоинт в ваш API. Он должен принимать список пиков и возвращать обработанную статистику.

```python
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any
from processing_logic import preprocess_obs # предполагая, что файл лежит рядом

app = FastAPI()

class PreprocessPayload(BaseModel):
    peaks: List[Dict[str, Any]] # Ожидается формат: [{"x": 123}, {"x": 245}, ...]
    fs: float = 100.0           # Частота дискретизации

@app.post("/api/v1/preprocess-peaks")
async def handle_preprocess(payload: PreprocessPayload):
    # Подготавливаем данные для функции
    observation = {"peaks": payload.peaks}
    
    # Вызываем математическую логику
    results = preprocess_obs(observation, payload.fs)
    
    return results
```

## Как это работает
Функция `preprocess_obs` выполняет:
1. Фильтрацию пиков (удаление ложных срабатываний в зоне релаксации).
2. Расчет мгновенной ЧСС и вариабельности.
3. Поиск аномальных эпизодов (используя стандартное отклонение и Softmax).
4. Расчет частоты эпизодов в час и форматирование временных меток.
