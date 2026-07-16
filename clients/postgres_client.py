import time
import psycopg2
from psycopg2.extras import RealDictCursor
from config.settings import settings
from utils.logger import logger, log_db_lookup, log_db_result, log_step_failure


class PostgreSQLClient:

    def __init__(self, ctx: dict = None):
        self._ctx = ctx
        logger.info("[PostgreSQL] Establishing connection to Neon PostgreSQL  host=<redacted>")
        t0 = time.perf_counter()
        try:
            self.connection = psycopg2.connect(
                settings.DATABASE_URL, cursor_factory=RealDictCursor
            )
            elapsed = time.perf_counter() - t0
            logger.info(f"[PostgreSQL] Connection established  elapsed={elapsed * 1000:.0f}ms")
        except Exception as e:
            elapsed = time.perf_counter() - t0
            logger.error(f"[PostgreSQL] Connection FAILED  elapsed={elapsed * 1000:.0f}ms  "
                         f"error={type(e).__name__}: {e}")
            raise

    def fetch_one(self, query: str, params=None, operation: str = "fetch_one",
                  ctx: dict = None, issue_code: str = None):
        active_ctx = ctx or self._ctx
        if active_ctx:
            log_db_lookup(active_ctx, operation=operation, issue_code=issue_code)
        t0 = time.perf_counter()
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                result = cursor.fetchone()
            elapsed = time.perf_counter() - t0
            if active_ctx:
                log_db_result(active_ctx, operation=operation,
                              result="FOUND" if result else "NOT FOUND",
                              elapsed=elapsed)
            return result
        except Exception as e:
            elapsed = time.perf_counter() - t0
            if active_ctx:
                log_step_failure(active_ctx, f"PostgreSQL/{operation}", elapsed, e)
            raise

    def fetch_all(self, query: str, params=None, operation: str = "fetch_all",
                  ctx: dict = None):
        active_ctx = ctx or self._ctx
        if active_ctx:
            log_db_lookup(active_ctx, operation=operation)
        t0 = time.perf_counter()
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                result = cursor.fetchall()
            elapsed = time.perf_counter() - t0
            if active_ctx:
                log_db_result(active_ctx, operation=operation,
                              result=f"{len(result)} row(s)", elapsed=elapsed)
            return result
        except Exception as e:
            elapsed = time.perf_counter() - t0
            if active_ctx:
                log_step_failure(active_ctx, f"PostgreSQL/{operation}", elapsed, e)
            raise

    def execute(self, query: str, params=None, operation: str = "execute",
                ctx: dict = None):
        active_ctx = ctx or self._ctx
        if active_ctx:
            log_db_lookup(active_ctx, operation=operation)
        t0 = time.perf_counter()
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
            self.connection.commit()
            elapsed = time.perf_counter() - t0
            if active_ctx:
                log_db_result(active_ctx, operation=operation,
                              result="COMMITTED", elapsed=elapsed)
        except Exception as e:
            elapsed = time.perf_counter() - t0
            if active_ctx:
                log_step_failure(active_ctx, f"PostgreSQL/{operation}", elapsed, e)
            raise
