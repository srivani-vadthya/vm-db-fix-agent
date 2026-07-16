import time
import psycopg2
from psycopg2.extras import RealDictCursor
from config.settings import settings
from utils.logger import logger


def _summarize(query: str) -> str:
    return " ".join(query.split())[:120]


class PostgreSQLClient:

    def __init__(self, ctx: dict = None):
        self._ctx = ctx
        prefix = self._prefix()
        logger.info(f"{prefix} [PostgreSQL] Establishing connection  host=<redacted>")
        t0 = time.perf_counter()
        try:
            self.connection = psycopg2.connect(
                settings.DATABASE_URL, cursor_factory=RealDictCursor
            )
            elapsed = time.perf_counter() - t0
            logger.info(f"{prefix} [PostgreSQL] Connection established  elapsed={elapsed:.3f}s")
        except Exception as e:
            elapsed = time.perf_counter() - t0
            logger.error(f"{prefix} [PostgreSQL] Connection failed  elapsed={elapsed:.3f}s  error={type(e).__name__}: {e}")
            raise

    def _prefix(self) -> str:
        if self._ctx:
            return f"[ticket={self._ctx['ticket_id']}] [corr={self._ctx['correlation_id']}]"
        return "[no-ctx]"

    def fetch_one(self, query: str, params=None):
        summary = _summarize(query)
        prefix = self._prefix()
        logger.info(f"{prefix} [PostgreSQL.fetch_one] query=\"{summary}\"")
        t0 = time.perf_counter()
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                result = cursor.fetchone()
            elapsed = time.perf_counter() - t0
            logger.info(f"{prefix} [PostgreSQL.fetch_one] [OK]  found={'yes' if result else 'no'}  elapsed={elapsed:.3f}s")
            return result
        except Exception as e:
            elapsed = time.perf_counter() - t0
            logger.error(f"{prefix} [PostgreSQL.fetch_one] [ERROR]  elapsed={elapsed:.3f}s  error={type(e).__name__}: {e}")
            raise

    def fetch_all(self, query: str, params=None):
        summary = _summarize(query)
        prefix = self._prefix()
        logger.info(f"{prefix} [PostgreSQL.fetch_all] query=\"{summary}\"")
        t0 = time.perf_counter()
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                result = cursor.fetchall()
            elapsed = time.perf_counter() - t0
            logger.info(f"{prefix} [PostgreSQL.fetch_all] [OK]  rows={len(result)}  elapsed={elapsed:.3f}s")
            return result
        except Exception as e:
            elapsed = time.perf_counter() - t0
            logger.error(f"{prefix} [PostgreSQL.fetch_all] [ERROR]  elapsed={elapsed:.3f}s  error={type(e).__name__}: {e}")
            raise

    def execute(self, query: str, params=None):
        summary = _summarize(query)
        prefix = self._prefix()
        logger.info(f"{prefix} [PostgreSQL.execute] query=\"{summary}\"")
        t0 = time.perf_counter()
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
            self.connection.commit()
            elapsed = time.perf_counter() - t0
            logger.info(f"{prefix} [PostgreSQL.execute] [OK]  elapsed={elapsed:.3f}s")
        except Exception as e:
            elapsed = time.perf_counter() - t0
            logger.error(f"{prefix} [PostgreSQL.execute] [ERROR]  elapsed={elapsed:.3f}s  error={type(e).__name__}: {e}")
            raise
