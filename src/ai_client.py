import google.generativeai as genai
from openai import OpenAI
import os

class AIClient:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.is_openrouter = self.api_key and self.api_key.startswith("sk-or-")
        self.model_name = "google/gemini-2.0-flash-exp:free" if self.is_openrouter else "gemini-2.0-flash"
        
        if self.is_openrouter:
            self.client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=self.api_key,
            )
        else:
            if self.api_key:
                genai.configure(api_key=self.api_key)
                self.client = genai.GenerativeModel(self.model_name)

    def generate_content(self, prompt):
        """
        Unified generation method.
        Returns text content.
        """
        if not self.api_key:
            raise ValueError("API Key not provided.")

        try:
            if self.is_openrouter:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    headers={
                        "HTTP-Referer": "https://apify.com/", # Optional, for OpenRouter rankings
                        "X-Title": "DataDojo" 
                    }
                )
                return response.choices[0].message.content
            else:
                # Google SDK
                response = self.client.generate_content(prompt)
                return response.text
        except Exception as e:
            print(f"AI Generation Error: {e}")
            raise e
