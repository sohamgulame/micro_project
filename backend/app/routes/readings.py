from fastapi import APIRouter, Depends, Header, HTTPException, status
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
from app.services.ai_service import AIService
from app.services.auth_service import AuthService, get_current_user, get_optional_current_user
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
    payload: ReadingCreate,
    db: Session = Depends(get_db),
    user=Depends(get_optional_current_user),
    x_device_key: str | None = Header(default=None),
) -> ReadingAnalysisResponse:
    resolved_user = user
    if resolved_user is None and x_device_key:
        resolved_user = AuthService.get_user_by_device_key(db, x_device_key)

    reading = ReadingService.create_reading(
        db,
        payload,
        user_id=resolved_user.id if resolved_user else None,
    )
    analysis = AIService().analyze_health(payload)
    ReadingService.create_prediction(db, reading.id, analysis)

    if resolved_user:
        latest_reading = ReadingService.get_latest_reading(db, resolved_user.id)
    else:
        latest_reading = reading

    if latest_reading is None:
        raise HTTPException(status_code=500, detail="Stored reading could not be loaded.")
    return build_reading_response(latest_reading)


@router.get(
    "/latest",
    response_model=ReadingAnalysisResponse,
    summary="Get the latest health reading with prediction",
)
def get_latest_reading(user=Depends(get_current_user), db: Session = Depends(get_db)) -> ReadingAnalysisResponse:
    reading = ReadingService.get_latest_reading(db, user.id)
    if reading is None:
        raise HTTPException(status_code=404, detail="No readings found for this user.")
    return build_reading_response(reading)


@router.get(
    "/history",
    response_model=HistoryResponse,
    summary="Get health reading history",
)
def get_reading_history(user=Depends(get_current_user), db: Session = Depends(get_db)) -> HistoryResponse:
    readings = ReadingService.get_all_readings(db, user.id)
    return HistoryResponse(readings=[build_reading_response(reading) for reading in readings])
