import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from openai import OpenAIError

from app.models.reading_schema import ConditionPrediction, HealthAnalysis, ReadingCreate

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')


class AIServiceError(Exception):
    pass


class AIService:
    def __init__(self) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None

    def analyze_health(self, data: ReadingCreate) -> HealthAnalysis:
        if not self.client:
            return self._fallback_analysis(data)

        prompt = (
            "You are a clinical assistant AI.\n\n"
            f"Analyze:\nSpO2: {data.spo2}\n"
            f"Heart Rate: {data.heart_rate}\n"
            f"Temperature: {data.temperature}\n\n"
            "Return STRICT JSON:\n"
            "{\n"
            '  "risk_level": "...",\n'
            '  "conditions": [{"name":"...", "confidence":0-1}],\n'
            '  "explanation": "...",\n'
            '  "recommendation": "..."\n'
            "}"
        )

        try:
            response = self.client.responses.parse(
                model=self.model,
                input=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                text_format=HealthAnalysis,
            )
        except OpenAIError:
            return self._fallback_analysis(data)

        analysis = response.output_parsed
        if analysis is None:
            return self._fallback_analysis(data)

        return analysis

    def _fallback_analysis(self, data: ReadingCreate) -> HealthAnalysis:
        conditions: list[ConditionPrediction] = []
        explanations: list[str] = []
        risk_level = "low"

        if data.spo2 < 90:
            risk_level = "high"
            conditions.append(ConditionPrediction(name="Possible hypoxemia", confidence=0.91))
            explanations.append("SpO2 is critically below the expected healthy range.")
        elif data.spo2 < 95:
            risk_level = "medium"
            conditions.append(ConditionPrediction(name="Low oxygen saturation", confidence=0.72))
            explanations.append("SpO2 is slightly below the preferred range.")

        if data.heart_rate > 120:
            risk_level = "high"
            conditions.append(ConditionPrediction(name="Tachycardia", confidence=0.82))
            explanations.append("Heart rate is significantly elevated.")
        elif data.heart_rate < 50:
            risk_level = "medium" if risk_level == "low" else risk_level
            conditions.append(ConditionPrediction(name="Bradycardia", confidence=0.74))
            explanations.append("Heart rate is below the usual resting range.")

        if data.temperature >= 38.0:
            risk_level = "high" if data.temperature >= 39.0 else "medium" if risk_level == "low" else risk_level
            conditions.append(ConditionPrediction(name="Fever", confidence=0.79))
            explanations.append("Temperature is above normal body temperature.")
        elif data.temperature < 35.0:
            risk_level = "high" if data.temperature < 34.0 else "medium" if risk_level == "low" else risk_level
            conditions.append(ConditionPrediction(name="Possible hypothermia", confidence=0.77))
            explanations.append("Temperature is below normal body temperature.")

        if not conditions:
            conditions.append(ConditionPrediction(name="Stable vitals", confidence=0.88))
            explanations.append("SpO2, heart rate, and temperature are within expected ranges.")

        recommendation = (
            "Continue monitoring and consult a clinician if symptoms worsen or readings remain abnormal."
            if risk_level != "low"
            else "Maintain routine monitoring and hydration."
        )

        return HealthAnalysis(
            risk_level=risk_level,
            conditions=conditions,
            explanation=" ".join(explanations),
            recommendation=recommendation,
        )
