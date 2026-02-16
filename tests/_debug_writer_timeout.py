import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(REPO_ROOT))

def main() -> None:
    # Legacy file name kept; now tests HuggingFace OpenAI-compatible endpoint connectivity.
    # Secrets/config are loaded from secrets.ini/config.ini via utils helpers.
    from openai import OpenAI  # type: ignore
    from utils import get_config, get_secret

    t0 = time.time()
    base_url = get_config("BASE_URL", section="HF")
    if base_url.endswith("/"):
        base_url = base_url[:-1]
    if base_url and not base_url.endswith("/v1"):
        base_url = base_url + "/v1"
    model = get_config("MODEL", section="HF", fallback="med-gemma")
    token = get_secret("HF_TOKEN")
    client = OpenAI(api_key=token, base_url=base_url)
    try:
        client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "ping"}],
            timeout=10.0,
        )
        print("OK", time.time() - t0)
    except Exception as e:
        print("ERR_TYPE", type(e).__name__)
        print("ERR", str(e)[:300])
        print("ELAPSED", time.time() - t0)


if __name__ == "__main__":
    main()


