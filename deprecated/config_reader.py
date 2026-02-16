import configparser
import os
from pathlib import Path

def _repo_root() -> Path:
    return Path(__file__).resolve().parent

def _read_ini(path: Path) -> configparser.ConfigParser:
    cfg = configparser.ConfigParser()
    if path.exists():
        cfg.read(str(path), encoding="utf-8")
    return cfg

def get_secret(variable: str, section: str = "DEFAULT", fallback: str = "") -> str:
    """Read a secret from environment variables first, then fallback to `secrets.ini`."""
    env_val = os.environ.get(variable)
    if env_val:
        return env_val.strip()
    try:
        cfg = _read_ini(_repo_root() / "secrets.ini")
        if section in cfg and variable in cfg[section]:
            return str(cfg[section].get(variable, fallback=fallback)).strip()
        if "DEFAULT" in cfg and variable in cfg["DEFAULT"]:
            return str(cfg["DEFAULT"].get(variable, fallback=fallback)).strip()
        return fallback
    except Exception:
        return fallback

def get_config(variable: str, section: str = "DEFAULT", fallback: str = "") -> str:
    """Read a config value from `config.ini`."""
    try:
        cfg = _read_ini(_repo_root() / "config.ini")
        if section in cfg and variable in cfg[section]:
            return str(cfg[section].get(variable, fallback=fallback)).strip()
        if "DEFAULT" in cfg and variable in cfg["DEFAULT"]:
            return str(cfg["DEFAULT"].get(variable, fallback=fallback)).strip()
        return fallback
    except Exception:
        return fallback
