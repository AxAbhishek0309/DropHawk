import os
import requests
from config.settings import settings

class LLMClient:
    def __init__(self, api_key=None, provider=None):
        self.api_key = api_key or settings["LLM_API_KEY"]
        self.provider = provider or os.getenv("LLM_PROVIDER", "gemini")
        self.groq_endpoint = os.getenv("GROQ_API_ENDPOINT", "https://api.groq.com/v1/logic")
        self.gemini_endpoint = os.getenv("GEMINI_API_ENDPOINT", "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent")

    def summarize(self, text):
        """
        Use Gemini for review analysis, comparison, and subjective judgments.
        """
        return self._summarize_gemini(text)

    def run_logic(self, prompt):
        """
        Use Groq for logic-heavy, fast tasks like decision trees or price-based conditions.
        """
        return self._run_groq(prompt)

    def _summarize_gemini(self, text):
        # Real Gemini API call (adjust as needed for your API)
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            data = {
                "contents": [{"parts": [{"text": text}]}]
            }
            response = requests.post(self.gemini_endpoint, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            # Parse Gemini response (adjust if needed)
            return result["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            return f"Gemini error: {e}"

    def _run_groq(self, prompt):
        # Real Groq API call (adjust as needed for your API)
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            data = {"prompt": prompt}
            response = requests.post(self.groq_endpoint, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            # Parse Groq response (adjust if needed)
            return result.get("result", "")
        except Exception as e:
            return f"Groq error: {e}" 