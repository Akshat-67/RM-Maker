import re
def apply_patch():
    with open("extractor.py", "r") as f:
        content = f.read()

    # Add tenacity to imports
    if "from tenacity" not in content:
        content = content.replace("import os\n", "import os\nfrom tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type\nfrom google.genai.errors import APIError\n")

    # Update raw_generate to use backoff
    new_raw_generate = """
    def raw_generate(self, prompt, model_name):
        \"\"\"Low-level single-prompt generation with key failover.\"\"\"
        if not self.api_keys:
            return None
        clean_name = model_name.replace("models/", "", 1) if model_name else model_name

        @retry(
            wait=wait_exponential(multiplier=1, min=4, max=10),
            stop=stop_after_attempt(3),
            retry=retry_if_exception_type(APIError)
        )
        def _call_api(client, name, contents):
            return client.models.generate_content(model=name, contents=contents)

        attempts = 0
        max_attempts = len(self.api_keys)
        while attempts < max_attempts:
            if not self.client:
                self._init_client()
            if not self.client:
                return None
            try:
                response = _call_api(self.client, clean_name, prompt)
                return response.text
            except Exception as e:
                print(f"[raw_generate] Key index {self.active_key_index} failed: {e}")
                self._rotate_key()
                attempts += 1
        print("[raw_generate] All API keys exhausted.")
        return None"""

    content = re.sub(r'    def raw_generate\(self, prompt, model_name\):.*?return None', new_raw_generate, content, flags=re.DOTALL | re.MULTILINE)

    with open("extractor.py", "w") as f:
        f.write(content)

apply_patch()
