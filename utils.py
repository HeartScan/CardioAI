import configparser
import os
from writerai import Writer
import numpy as np
from scipy.special import softmax


def get_client():    
    client = Writer(api_key=os.environ.get("WRITER_API_KEY"))
    return client


def get_settings(section='DEFAULT', variable='SYSTEM_PROMPT'):
    config = configparser.ConfigParser()
    config.read('./config.ini', encoding="utf-8")
    return config[section][variable]
    

def sec2hms(sec: float) -> str:
            h = int(sec // 3600)
            m = int((sec % 3600) // 60)
            s = int(sec % 60)
            return f"{h:02d}:{m:02d}:{s:02d}"


def mistake_holder(obs, th=5):
    if obs['episodes_count']<th:
        obs['episodes_count']=0
        obs['episodes_per_hour']=0
        obs['episodes_timestamps']=[]
    return obs


def filter_peaks(peaks_x: list, N: int=0) -> list:
    """
    Filters out peaks that are too close to each other. - ПОПАДАНИЕ В ЗОНУ РЕЛАКСАЦИИ

    Parameters
    ----------
    peaks : list
        A list of peak indices.
    N : int
        The minimum distance between two accepted peaks.

    Returns
    -------
    list
        A new list of filtered peak indices.
    """
    # if not peaks:
    #     return []
    peaks=[i['x'] for i in peaks_x]
    if N==0:
        N=np.diff(peaks).mean()/2

    filtered = [peaks[0]]
    for i in range(1, len(peaks)):
        if peaks[i] - filtered[-1] > N:
            filtered.append(peaks[i])
    return [{'x': i} for i in filtered]
    


def preprocess_obs(observation, fs = 100.0):
    """
    Возвращает подробную статистику по вариативности ЧСС:

      • instantaneous_bpm  – мгновенная ЧСС для каждого RR-интервала, bpm
      • bpm_deviation      – отклонение этой ЧСС от средней, bpm
      • avg_bpm            – средняя ЧСС, bpm
      • min_bpm / max_bpm  – минимальная и максимальная ЧСС, bpm
      • episodes_count     – число эпизодов, где bpm_deviation > σ
      • episodes_per_hour  – ожидаемое кол-во эпизодов в час
      • episodes_timestamps – список [start, end] интервалов (HH:MM:SS)

    Параметры
    ----------
    observation : dict
        Требуется ключ 'peaks': [{'x': int, 'y': float}, ...]
        Координаты 'x' заданы в отсчётах при fs = 100 Гц.
    """
    peaks = observation.get("peaks", [])

    # ------ !!!ATTENTION!!! ---------
    # Если на бэке не произведена фильтрация на предмет пиков, 
    # попавших в зону релаксации, мы должны сделать это здесь
    peaks=filter_peaks(peaks)

    # ------ подготовка базовых рядов ---------------------------------------  
    rr_intervals = [
        (peaks[i + 1]["x"] - peaks[i]["x"]) / fs
        for i in range(len(peaks) - 1)
    ]
    instantaneous_bpm = 60.0 / np.array(rr_intervals)


    # ------ статистика ЧСС ----------- 
    mean_bpm = np.mean(instantaneous_bpm)
    bpm_deviation = np.array(instantaneous_bpm)-mean_bpm 
       
    min_bpm = np.min(instantaneous_bpm)
    max_bpm = np.max(instantaneous_bpm)

    # ------ поиск эпизодов --------------------------------------------------
    #-------- !!!ATTENTION!!!----------------
    #-------- old one ----------
    # Порог – одно стандартное отклонение
    #sigma = np.std(bpm_deviation)
    #-------- new one ----------
    sigma = np.std(bpm_deviation)+np.std(bpm_deviation)*softmax(instantaneous_bpm).std()

    # Индексы интервалов, где отклонение превышает σ (только положит.)
    idx = np.where(np.abs(np.array(bpm_deviation))>sigma)[0]

    if idx.size:        
        # 2. Найти границы групп: разрыв > 1 означает новый эпизод
        breaks = np.where(np.diff(idx) > 1)[0] + 1
        groups = np.split(idx, breaks)         # → [array([3,4,5]), array([12,13]), array([20,21])]        

        episodes_timestamps = [
            [
                sec2hms(peaks[g[0]]["x"] / fs),        # начало
                sec2hms(peaks[g[-1] + 1]["x"] / fs)    # конец
            ]
            for g in groups
        ]
    else:
        episodes_timestamps = []

    episodes_count = len(episodes_timestamps)
    # Длительность наблюдения в минутах
    duration_min = (peaks[-1]["x"] - peaks[0]["x"]) / fs / 60.0 if len(peaks) > 1 else 0.0
    episodes_per_hour = (60.0 / duration_min) * episodes_count if duration_min > 0 else 0.0

    # ------ итог ------------------------------------------------------------
    return mistake_holder({
        "instantaneous_bpm": instantaneous_bpm.tolist(),
        "bpm_deviation": bpm_deviation.tolist(),
        "avg_bpm": mean_bpm.item(),
        "min_bpm": min_bpm.item(),
        "max_bpm": max_bpm.item(),
        "episodes_count": episodes_count,
        "episodes_per_hour": episodes_per_hour,
        "episodes_timestamps": episodes_timestamps,
    }, th=4)



# def preprocess_obs(observation):
#     return '''SCG data:\n 
#     {"avg_bpm": 72,"min_bpm": 60,
#     "max_bpm": 105,"episodes_count": 3,
#     "episodes_per_hour": 12.0,
#     "episodes_timestamps": [["09:12:03", "09:12:15"],["09:13:18", "09:13:24"], ["09:14:55", "09:15:05"],],}"'''
