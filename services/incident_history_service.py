import time
from clients.postgres_client import PostgreSQLClient
from utils.logger import log_step_success, log_step_failure


class IncidentHistoryService:

    def __init__(self):
        self.db = PostgreSQLClient()

    def save(self, ticket_id: str, application: str, action: str, status: str, ctx: dict = None):
        step = "IncidentHistoryService.save"
        t0 = time.perf_counter()
        try:
            self.db.execute(
                """
                INSERT INTO incident_history (ticket_id, application, action_taken, status)
                VALUES (%s, %s, %s, %s)
                """,
                (ticket_id, application, action, status)
            )
            if ctx:
                log_step_success(ctx, step, time.perf_counter() - t0,
                                 action=action, status=status)
        except Exception as e:
            if ctx:
                log_step_failure(ctx, step, time.perf_counter() - t0, e)
            raise
