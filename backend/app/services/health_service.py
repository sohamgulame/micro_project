from app.models.health import HealthResponse


class HealthService:
    @staticmethod
    def get_system_health() -> HealthResponse:
        return HealthResponse(status="healthy", service="iot-health-monitoring-system")
