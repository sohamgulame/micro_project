import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from google import genai

from app.models.reading_schema import HealthAnalysis, ReadingCreate

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')


class AIServiceError(Exception):
    pass


class AIService:
    def __init__(self) -> None:
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        if not self.api_key:
            raise AIServiceError("GEMINI_API_KEY is not configured.")
        self.client = genai.Client(api_key=self.api_key)

    def analyze_health(self, data: ReadingCreate) -> HealthAnalysis:
        prompt = (
            "You are a clinical assistant AI.\n\n"
            f"Analyze:\nSpO2: {data.spo2}\n"
            f"Heart Rate: {data.heart_rate}\n"
            f"Temperature: {data.temperature}\n\n"
            "Return STRICT JSON with risk_level, conditions, explanation, and recommendation."
        )

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_json_schema": HealthAnalysis.model_json_schema(),
                },
            )
        except Exception as exc:
            raise AIServiceError(f"Gemini health analysis failed: {exc}") from exc

        response_text = (response.text or "").strip()
        if not response_text:
            raise AIServiceError("Gemini health analysis returned an empty response.")

        try:
            return HealthAnalysis.model_validate_json(response_text)
        except Exception:
            try:
                match = re.search(r"\{.*\}", response_text, re.DOTALL)
                if match is None:
                    raise ValueError("No JSON object found in Gemini response.")
                payload = json.loads(match.group(0))
                return HealthAnalysis.model_validate(payload)
            except Exception as exc:
                raise AIServiceError(f"Gemini health analysis returned invalid JSON: {response_text[:500]}") from exc

    @staticmethod
    def build_fallback_analysis(data: ReadingCreate, reason: str | None = None) -> HealthAnalysis:
        explanation = (
            "Automated AI explanation is temporarily unavailable. "
            f"Latest reading received: SpO2 {data.spo2}, heart rate {data.heart_rate}, "
            f"temperature {data.temperature} C."
        )
        if reason:
            explanation = f"{explanation} Reason: {reason}"

        return HealthAnalysis(
            risk_level="Review Needed",
            conditions=[
                {
                    "name": "Manual review suggested",
                    "confidence": 0.5,
                }
            ],
            explanation=explanation,
            recommendation="Recheck the sensors and review this reading manually.",
        )
