from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ReadingCreate(BaseModel):
    spo2: int = Field(..., ge=70, le=100, description="Blood oxygen saturation percentage")
    heart_rate: int = Field(..., ge=30, le=220, description="Heart rate in beats per minute")
    temperature: float = Field(
        ..., ge=30.0, le=45.0, description="Body temperature in Celsius"
    )


class ConditionPrediction(BaseModel):
    name: str
    confidence: float = Field(..., ge=0.0, le=1.0)


class HealthAnalysis(BaseModel):
    risk_level: str
    conditions: list[ConditionPrediction]
    explanation: str
    recommendation: str


class PredictionResponse(BaseModel):
    id: int
    reading_id: int
    risk_level: str
    conditions: list[ConditionPrediction]
    explanation: str

    model_config = ConfigDict(from_attributes=True)


class ReadingResponse(BaseModel):
    id: int
    spo2: int
    heart_rate: int
    temperature: float
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class ReadingAnalysisResponse(ReadingResponse):
    prediction: PredictionResponse | None = None


class HistoryResponse(BaseModel):
    readings: list[ReadingAnalysisResponse]
