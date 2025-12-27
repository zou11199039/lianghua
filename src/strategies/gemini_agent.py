# -*- coding: utf-8 -*-

# Make the optional dependency on google.generativeai lazy so test collection
# and environments without the package installed don't fail on import.
try:
    import google.generativeai as genai

    _HAS_GENAI = True
except Exception:
    genai = None
    _HAS_GENAI = False


class GeminiAgent:

    def __init__(self, api_key=None, model_name="gemini-2.0-flash-exp"):
        if not _HAS_GENAI:
            # Keep object usable but LLM calls will return None and warn.
            self.model = None
            if api_key:
                print(
                    "Warning: 'google.generativeai' not installed. "
                    "Gemini features unavailable."
                )
            return

        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(model_name)
        else:
            self.model = None
            print(
                "Warning: Gemini API Key not provided. "
                "LLM features disabled."
            )

    def analyze_market(self, news_text, market_data_summary):
        """
        Send market context to Gemini and get trading advice.
        """
        if not self.model:
            return None

        prompt = f"""
        You are a senior quantitative trader.
        Analyze the following market data and recent news.

        [Market Data Summary]
        {market_data_summary}

[Recent News]
        {news_text}

        Task:
        1. Analyze the sentiment (Bullish/Bearish/Neutral).
        2. Identify top 3 potential sectors or stocks.
        3. Provide a risk score (0-10, 10 is highest risk).

Output format (JSON):
        {{
            "sentiment": "...",
            "top_picks": ["stocks/sectors"],
            "risk_score": 5,
            "reasoning": "..."
        }}
        """

        try:
            response = self.model.generate_content(prompt)
            # Simple cleanup to ensure JSON parsing
            # if model outputs markdown code blocks
            text = (
                response.text.replace("```json", "").replace("```", "").strip()
            )
            return text
        except Exception as e:
            print(f"Gemini API Error: {e}")
            return None
