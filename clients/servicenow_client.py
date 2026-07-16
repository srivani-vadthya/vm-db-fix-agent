import time
import requests
from config.settings import settings
from utils.logger import log_servicenow_request, log_servicenow_response, log_step_failure


class ServiceNowClient:

    def __init__(self):
        self.base_url = settings.SN_INSTANCE
        self.auth     = (settings.SN_USERNAME, settings.SN_PASSWORD)
        self.headers  = {"Accept": "application/json"}

    def get(self, table: str, query: str = "", ctx: dict = None):
        url    = f"{self.base_url}/api/now/table/{table}"
        params = {"sysparm_query": query} if query else {}

        if ctx:
            log_servicenow_request(ctx, method="GET", table=table, query=query)

        t0 = time.perf_counter()
        try:
            response = requests.get(
                url, auth=self.auth, headers=self.headers, params=params
            )
            elapsed = time.perf_counter() - t0
            response.raise_for_status()
            result = response.json()["result"]
            if ctx:
                log_servicenow_response(ctx, table=table,
                                        status=response.status_code,
                                        records=len(result),
                                        elapsed=elapsed)
            return result
        except Exception as e:
            elapsed = time.perf_counter() - t0
            if ctx:
                log_step_failure(ctx, f"ServiceNow.GET/{table}", elapsed, e)
            raise
