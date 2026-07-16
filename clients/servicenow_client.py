import time
import requests
from config.settings import settings
from utils.logger import logger


class ServiceNowClient:

    def __init__(self):
        self.base_url = settings.SN_INSTANCE
        self.auth = (settings.SN_USERNAME, settings.SN_PASSWORD)
        self.headers = {"Accept": "application/json"}

    def get(self, table: str, query: str = "", ctx: dict = None):
        url = f"{self.base_url}/api/now/table/{table}"
        params = {"sysparm_query": query} if query else {}
        prefix = f"[ticket={ctx['ticket_id']}] [corr={ctx['correlation_id']}]" if ctx else "[no-ctx]"

        logger.info(f"{prefix} [ServiceNow.GET] table={table}  query={query}")
        t0 = time.perf_counter()
        try:
            response = requests.get(
                url, auth=self.auth, headers=self.headers, params=params
            )
            elapsed = time.perf_counter() - t0
            response.raise_for_status()
            result = response.json()["result"]
            logger.info(
                f"{prefix} [ServiceNow.GET] [OK]  table={table}  "
                f"status={response.status_code}  records={len(result)}  elapsed={elapsed:.3f}s"
            )
            return result
        except Exception as e:
            elapsed = time.perf_counter() - t0
            logger.error(
                f"{prefix} [ServiceNow.GET] [ERROR]  table={table}  "
                f"elapsed={elapsed:.3f}s  error={type(e).__name__}: {e}"
            )
            raise
