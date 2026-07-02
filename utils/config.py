import os
import logging

def get_nvidia_api_key() -> str:
    """Return the NVIDIA API key from the environment.

    Raises:
        RuntimeError: If the ``NVIDIA_API_KEY`` environment variable is not set.
    """
    key = os.getenv('NVIDIA_API_KEY')
    if not key:
        logging.error('NVIDIA_API_KEY environment variable is missing')
        raise RuntimeError('NVIDIA_API_KEY not set')
    return key
