import time
import re
import json
import logging
from google import genai
from google.genai import types
from google.genai.errors import APIError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AIClient")

class AIClient:
    def __init__(self, api_keys=None):
        self.api_keys = api_keys or []
        self.active_key_index = 0
        self.client = None
        self._init_client()

    def _init_client(self):
        if self.api_keys and self.active_key_index < len(self.api_keys):
            key = self.api_keys[self.active_key_index]
            self.client = genai.Client(api_key=key)
        else:
            self.client = None

    def _rotate_key(self):
        if not self.api_keys:
            return False
        self.active_key_index = (self.active_key_index + 1) % len(self.api_keys)
        logger.warning(f"[FAILOVER] Rotating Gemini API key to index {self.active_key_index}...")
        self._init_client()
        return True

    def list_models(self):
        if not self.client:
            self._init_client()
        if not self.client:
            return ["gemini-2.5-flash"]
        try:
            models_list = self.client.models.list()
            valid_models = []
            for m in models_list:
                try:
                    if m.name:
                        valid_models.append(m.name)
                except Exception as e:
                    logger.debug(f"Error accessing model name: {e}")
            for fb in ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-1.5-flash", "gemini-1.5-pro"]:
                if fb not in valid_models:
                    valid_models.append(fb)
            return valid_models
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-1.5-flash", "gemini-1.5-pro"]

    def generate_json(self, system_instruction, user_prompt, response_schema=None, model="gemini-2.5-flash", max_retries=5, initial_backoff=2):
        if not self.client:
            self._init_client()
        if not self.client:
            raise ValueError("No API keys provided or client not initialized.")

        retries = 0
        backoff = initial_backoff
        last_error = None

        while retries <= max_retries:
            try:
                config_kwargs = {}
                if system_instruction:
                    config_kwargs["system_instruction"] = system_instruction
                
                if response_schema:
                    config_kwargs["response_mime_type"] = "application/json"
                    config_kwargs["response_schema"] = response_schema

                config = types.GenerateContentConfig(**config_kwargs)

                response = self.client.models.generate_content(
                    model=model,
                    contents=user_prompt,
                    config=config
                )

                raw_text = response.text
                if not raw_text:
                    raise ValueError("Empty response received from LLM model.")

                if response_schema:
                    clean_text = raw_text.strip()
                    if clean_text.startswith("```"):
                        m = re.match(r"^```(?:json)?\s*(.*?)\s*```$", clean_text, re.DOTALL | re.IGNORECASE)
                        if m:
                            clean_text = m.group(1).strip()
                    try:
                        return json.loads(clean_text)
                    except json.JSONDecodeError as je:
                        logger.error(f"Failed to parse JSON response: {clean_text}")
                        raise je
                return {"text": raw_text}

            except APIError as api_err:
                last_error = api_err
                logger.error(f"Gemini API Error (attempt {retries + 1}/{max_retries + 1}): {api_err}")
                if self._rotate_key():
                    retries += 1
                    time.sleep(1)
                    continue
                else:
                    logger.warning(f"No key rotation available. Backing off for {backoff} seconds...")
                    time.sleep(backoff)
                    backoff *= 2
                    retries += 1
            except Exception as e:
                last_error = e
                logger.error(f"Unexpected error in generate_json: {e}")
                time.sleep(backoff)
                backoff *= 2
                retries += 1

        raise last_error or RuntimeError("Max retries exceeded during text generation.")

    def generate_text(self, contents, model="gemini-2.5-flash", system_instruction=None, max_retries=5):
        res = self.generate_json(
            system_instruction=system_instruction,
            user_prompt=contents,
            model=model,
            max_retries=max_retries
        )
        return res.get("text", "")
