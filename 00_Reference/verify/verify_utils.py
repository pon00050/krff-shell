"""Shared helper for verification scripts."""
import os
from pathlib import Path
from dotenv import load_dotenv


def get_dart():
    import OpenDartReader as _odr
    load_dotenv()
    api_key = os.environ.get("DART_API_KEY")
    if not api_key:
        raise EnvironmentError("DART_API_KEY not set in .env")
    return _odr(api_key)


RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)
