from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
import json
import os
import re

from app.models.reading_schema import HealthAnalysis, ReadingCreate

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')


class AIServiceError(Exception):
    pass


class AIService:
    def __init__(self) -> None:
        self.api_key = os.getenv("NVIDIA_API_KEY") or os.getenv("GEMINI_API_KEY")
        self.model = os.getenv("NVIDIA_MODEL", "openai/gpt-oss-20b")
        if not self.api_key:
            raise AIServiceError("NVIDIA_API_KEY is not configured.")
        self.client = OpenAI(
            base_url=os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1"),
            api_key=self.api_key,
        )

    def analyze_health(self, data: ReadingCreate) -> HealthAnalysis:
        system_prompt = "You are a clinical assistant AI. Return only strict JSON."
        user_prompt = (
            f"Analyze:\nSpO2: {data.spo2}\n"
            f"Heart Rate: {data.heart_rate}\n"
            f"Temperature: {data.temperature}\n\n"
            "Return STRICT JSON with this schema:\n"
            '{"risk_level":"...","conditions":[{"name":"...","confidence":0-1}],'
            '"explanation":"...","recommendation":"..."}'
        )

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=1,
                top_p=1,
                max_tokens=4096,
                stream=False,
            )
        except Exception as exc:
            raise AIServiceError(f"NVIDIA health analysis failed: {exc}") from exc

        response_text = (
            completion.choices[0].message.content if completion.choices else None
        )
        response_text = (response_text or "").strip()
        if not response_text:
            raise AIServiceError("NVIDIA health analysis returned an empty response.")

        try:
            return HealthAnalysis.model_validate_json(response_text)
        except Exception:
            try:
                match = re.search(r"\{.*\}", response_text, re.DOTALL)
                if match is None:
                    raise ValueError("No JSON object found in NVIDIA response.")
                payload = json.loads(match.group(0))
                return HealthAnalysis.model_validate(payload)
            except Exception as exc:
                raise AIServiceError(f"NVIDIA health analysis returned invalid JSON: {response_text[:500]}") from exc

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
