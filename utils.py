import configparser
import os
from writerai import Writer


def get_client():    
    client = Writer(api_key=os.environ.get("WRITER_API_KEY"))
    return client


def get_settings(section='DEFAULT', variable='SYSTEM_PROMPT'):
    config = configparser.ConfigParser()
    config.read('./config.ini', encoding="utf-8")
    return config[section][variable]


def preprocess_obs(observation):
    return '''SCG data:\n 
    {"avg_bpm": 72,"min_bpm": 60,
    "max_bpm": 105,"episodes_count": 3,
    "episodes_per_hour": 12.0,
    "episodes_timestamps": [["09:12:03", "09:12:15"],["09:13:18", "09:13:24"], ["09:14:55", "09:15:05"],],}"'''