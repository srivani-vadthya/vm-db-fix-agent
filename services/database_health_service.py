import time
from clients.postgres_client import PostgreSQLClient
from utils.logger import log_step_success, log_step_failure


class DatabaseHealthService:

    def __init__(self):
        self.db = PostgreSQLClient()

    def get_database_health(self, database_name: str, ctx: dict = None):
        step = "DatabaseHealthService.get_database_health"
        t0 = time.perf_counter()
        try:
            result = self.db.fetch_one(
                """
                SELECT a.app_name, d.*
                FROM database_health d
                JOIN applications a ON a.app_id = d.app_id
                WHERE LOWER(REPLACE(a.app_name,' ','_')) = %s
                """,
                (database_name.lower(),)
            )
            if ctx:
                log_step_success(ctx, step, time.perf_counter() - t0,
                                 database=database_name,
                                 found="yes" if result else "no")
            return result
        except Exception as e:
            if ctx:
                log_step_failure(ctx, step, time.perf_counter() - t0, e)
            raise
