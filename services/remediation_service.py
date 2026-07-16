import time
from clients.postgres_client import PostgreSQLClient
from utils.logger import log_info, log_step_success, log_step_failure


class RemediationService:

    def __init__(self):
        self.db = PostgreSQLClient()

    def generate_plan(self, issues: list, ctx: dict = None):
        step = "RemediationService.generate_plan"
        t0 = time.perf_counter()
        actions = []
        try:
            for issue in issues:
                if ctx:
                    log_info(ctx, f"Looking up remediation rule", issue_code=issue["issue"])
                rule = self.db.fetch_one(
                    "SELECT * FROM remediation_rules WHERE issue_code=%s",
                    (issue["issue"],)
                )
                if rule:
                    actions.append({
                        "issue": issue["issue"],
                        "action": rule["action"],
                        "automated": rule["automated"]
                    })
                    if ctx:
                        log_info(ctx, "Remediation rule matched",
                                 issue_code=issue["issue"],
                                 action=rule["action"],
                                 automated=rule["automated"])
                else:
                    if ctx:
                        log_info(ctx, "No remediation rule found", issue_code=issue["issue"])

            if ctx:
                log_step_success(ctx, step, time.perf_counter() - t0,
                                 issues_in=len(issues), actions_out=len(actions))
            return actions
        except Exception as e:
            if ctx:
                log_step_failure(ctx, step, time.perf_counter() - t0, e)
            raise
