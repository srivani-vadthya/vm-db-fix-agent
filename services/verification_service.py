import time
from services.database_health_service import DatabaseHealthService
from utils.logger import log_step_success, log_step_failure


class VerificationService:

    def __init__(self):
        self.health = DatabaseHealthService()

    def verify(self, database_name: str, ctx: dict = None):
        step = "VerificationService.verify"
        t0 = time.perf_counter()
        try:
            health = self.health.get_database_health(database_name, ctx=ctx)
            result = {
                "status": health["status"],
                "active_connections": health["active_connections"],
                "cpu_usage": health["cpu_usage"],
                "memory_usage": health["memory_usage"],
                "slow_queries": health["slow_queries"],
                "deadlocks": health["deadlocks"]
            }
            if ctx:
                log_step_success(ctx, step, time.perf_counter() - t0,
                                 status=result["status"],
                                 active_connections=result["active_connections"])
            return result
        except Exception as e:
            if ctx:
                log_step_failure(ctx, step, time.perf_counter() - t0, e)
            raise
