import re
def apply_patch():
    with open("extractor.py", "r") as f:
        content = f.read()

    new_extract_with_ai = """
        while attempts < max_attempts:
            if not self.client:
                self._init_client()
            if not self.client:
                return {"error": "Gemini API Client Initialization Failed"}

            @retry(
                wait=wait_exponential(multiplier=1, min=4, max=10),
                stop=stop_after_attempt(3),
                retry=retry_if_exception_type(APIError)
            )
            def _call_api_with_retry(client, model, contents):
                return client.models.generate_content(model=model, contents=contents)

            try:
                final_contents = contents + [types.Part.from_text(text=prompt)]
                response = _call_api_with_retry(self.client, selected_model, final_contents)
                match = re.search(r'\\{.*\\}', response.text, re.DOTALL)
                if match:
                    data = json.loads(match.group(0))
                    return self._normalize_response(data, expected_borrowers, expected_loans,
                                                    expected_witnesses, borrower_hints, witness_hints,
                                                    doc_type=doc_type, expected_sellers=expected_sellers,
                                                    expected_buyers=expected_buyers, seller_hints=seller_hints,
                                                    buyer_hints=buyer_hints)
                return {"error": "AI returned non-JSON response", "raw": response.text}
            except Exception as e:
                last_error = str(e)
                print(f"[FAILOVER WARNING] Gemini extraction failed with key index {self.active_key_index}: {last_error}")
                self._rotate_key()
                attempts += 1
"""

    content = re.sub(r'        while attempts < max_attempts:.*?attempts \+= 1', new_extract_with_ai, content, flags=re.DOTALL | re.MULTILINE)

    with open("extractor.py", "w") as f:
        f.write(content)

apply_patch()
