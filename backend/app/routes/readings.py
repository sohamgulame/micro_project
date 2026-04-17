from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.reading import Reading
from app.models.reading_schema import (
    HistoryResponse,
    PredictionResponse,
    ReadingAnalysisResponse,
    ReadingCreate,
    ReadingResponse,
)
from app.services.ai_service import AIService, AIServiceError
from app.services.reading_service import ReadingService

router = APIRouter(prefix="/api/v1", tags=["Readings"])


def build_reading_response(reading: Reading) -> ReadingAnalysisResponse:
    reading_response = ReadingResponse.model_validate(reading)
    latest_prediction = reading.predictions[-1] if reading.predictions else None
    prediction_response = (
        PredictionResponse.model_validate(latest_prediction)
        if latest_prediction is not None
        else None
    )
    return ReadingAnalysisResponse(
        **reading_response.model_dump(), prediction=prediction_response
    )


@router.post(
    "/readings",
    response_model=ReadingAnalysisResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new IoT health reading",
)
def create_reading(
    payload: ReadingCreate, db: Session = Depends(get_db)
) -> ReadingAnalysisResponse:
    reading = ReadingService.create_reading(db, payload)

    try:
        analysis = AIService().analyze_health(payload)
    except AIServiceError as exc:
        analysis = AIService.build_fallback_analysis(payload, str(exc))

    ReadingService.create_prediction(db, reading.id, analysis)
    latest_reading = ReadingService.get_latest_reading(db)
    if latest_reading is None:
        raise HTTPException(status_code=500, detail="Stored reading could not be loaded.")
    return build_reading_response(latest_reading)


@router.get(
    "/latest",
    response_model=ReadingAnalysisResponse,
    summary="Get the latest health reading with prediction",
)
def get_latest_reading(db: Session = Depends(get_db)) -> ReadingAnalysisResponse:
    reading = ReadingService.get_latest_reading(db)
    if reading is None:
        raise HTTPException(status_code=404, detail="No readings found.")
    return build_reading_response(reading)


@router.get(
    "/history",
    response_model=HistoryResponse,
    summary="Get health reading history",
)
def get_reading_history(db: Session = Depends(get_db)) -> HistoryResponse:
    readings = ReadingService.get_all_readings(db)
    return HistoryResponse(readings=[build_reading_response(reading) for reading in readings])
