from __future__ import annotations

import configparser
import os
from pathlib import Path
from typing import Optional


def _backend_dir() -> Path:
    return Path(__file__).resolve().parent


def _read_ini(path: Path) -> configparser.ConfigParser:
    cfg = configparser.ConfigParser()
    if path.exists():
        cfg.read(str(path), encoding="utf-8")
    return cfg


def get_secret(variable: str, section: str = "DEFAULT", fallback: str = "") -> str:
    """
    Read a secret from environment variables first, then fallback to `secrets.ini`
    located next to the backend package.
    """
    env_val = os.environ.get(variable)
    if env_val:
        return env_val.strip()
    try:
        # 1) Prefer backend-local secrets.ini
        cfg = _read_ini(_backend_dir() / "secrets.ini")
        if section in cfg and variable in cfg[section]:
            return str(cfg[section].get(variable, fallback=fallback)).strip()
        if "DEFAULT" in cfg and variable in cfg["DEFAULT"]:
            return str(cfg["DEFAULT"].get(variable, fallback=fallback)).strip()

        # 2) Backward-compat: allow repo-root secrets.ini
        cfg_root = _read_ini(_backend_dir().parent / "secrets.ini")
        if section in cfg_root and variable in cfg_root[section]:
            return str(cfg_root[section].get(variable, fallback=fallback)).strip()
        if "DEFAULT" in cfg_root and variable in cfg_root["DEFAULT"]:
            return str(cfg_root["DEFAULT"].get(variable, fallback=fallback)).strip()
        return fallback
    except Exception:
        return fallback


def get_config(variable: str, section: str = "DEFAULT", fallback: str = "") -> str:
    """
    Read a config value from `config.ini` located next to the backend package.
    """
    try:
        cfg = _read_ini(_backend_dir() / "config.ini")
        if section in cfg and variable in cfg[section]:
            return str(cfg[section].get(variable, fallback=fallback)).strip()
        if "DEFAULT" in cfg and variable in cfg["DEFAULT"]:
            return str(cfg["DEFAULT"].get(variable, fallback=fallback)).strip()
        return fallback
    except Exception:
        return fallback


def get_config_float(variable: str, section: str = "DEFAULT", fallback: float = 0.0) -> float:
    v = get_config(variable, section=section, fallback=str(fallback))
    try:
        return float(v)
    except Exception:
        return float(fallback)


def get_config_int(variable: str, section: str = "DEFAULT", fallback: int = 0) -> int:
    v = get_config(variable, section=section, fallback=str(fallback))
    try:
        return int(float(v))
    except Exception:
        return int(fallback)


def try_get_config_text(variable: str, section: str = "DEFAULT") -> Optional[str]:
    v = get_config(variable, section=section, fallback="")
    return v if v.strip() else None

