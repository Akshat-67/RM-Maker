import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_gemini_api_keys():
    """
    Discovers available Gemini API keys from environment variables.
    Looks for GEMINI_API_KEY_1, GEMINI_API_KEY_2, etc.
    Also falls back to a single GEMINI_API_KEY if present.
    Returns a list of unique, non-empty API keys.
    """
    keys = []

    # Check for numbered keys
    i = 1
    while True:
        key = os.getenv(f"GEMINI_API_KEY_{i}")
        if key is not None:
            if key.strip():
                keys.append(key.strip())
            i += 1
        else:
            # If we didn't find GEMINI_API_KEY_i, stop searching numbered keys
            break

    # Also check the base GEMINI_API_KEY as a fallback if people just use that
    base_key = os.getenv("GEMINI_API_KEY")
    if base_key and base_key.strip():
        keys.append(base_key.strip())

    # Remove duplicates while preserving order
    unique_keys = list(dict.fromkeys(keys))

    return unique_keys

# Exported default key list
DEFAULT_GEMINI_API_KEYS = get_gemini_api_keys()

NVIDIA_NIM_API_KEY = os.getenv("NVIDIA_NIM_API_KEY", "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")
NVIDIA_OCR_API_KEY = os.getenv("NVIDIA_OCR_API_KEY", "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")
CASE_INBOX_DIR = os.getenv("CASE_INBOX_DIR", "cases_inbox")


def get_nvidia_api_key() -> str:
    """Return the NVIDIA API key from the environment.

    Checks ``NVIDIA_API_KEY`` first, then falls back to ``NVIDIA_NIM_API_KEY``.

    Raises:
        RuntimeError: If no NVIDIA API key is configured.
    """
    key = os.getenv('NVIDIA_API_KEY') or NVIDIA_NIM_API_KEY
    if not key:
        logging.error('NVIDIA API key environment variable is missing')
        raise RuntimeError('NVIDIA API key not set')
    return key


