from sqlalchemy import desc
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from app.models.reading import Prediction, Reading
from app.models.reading_schema import HealthAnalysis, ReadingCreate


class DatabaseOperationError(Exception):
    pass


class ReadingService:
    @staticmethod
    def create_reading(db: Session, payload: ReadingCreate) -> Reading:
        reading = Reading(**payload.model_dump())

        try:
            db.add(reading)
            db.commit()
            db.refresh(reading)
            return reading
        except SQLAlchemyError as exc:
            db.rollback()
            raise DatabaseOperationError("Failed to store reading in the database.") from exc

    @staticmethod
    def create_prediction(
        db: Session, reading_id: int, analysis: HealthAnalysis
    ) -> Prediction:
        prediction = Prediction(
            reading_id=reading_id,
            risk_level=analysis.risk_level,
            conditions=[condition.model_dump() for condition in analysis.conditions],
            explanation=analysis.explanation,
        )

        try:
            db.add(prediction)
            db.commit()
            db.refresh(prediction)
            return prediction
        except SQLAlchemyError as exc:
            db.rollback()
            raise DatabaseOperationError("Failed to store prediction in the database.") from exc

    @staticmethod
    def get_latest_reading(db: Session) -> Reading | None:
        return (
            db.query(Reading)
            .options(selectinload(Reading.predictions))
            .order_by(desc(Reading.timestamp), desc(Reading.id))
            .first()
        )

    @staticmethod
    def get_all_readings(db: Session) -> list[Reading]:
        return (
            db.query(Reading)
            .options(selectinload(Reading.predictions))
            .order_by(desc(Reading.timestamp), desc(Reading.id))
            .all()
        )
