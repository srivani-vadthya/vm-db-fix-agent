import time
import uuid

from models.request import RCARequest
from services.cmdb_service import CMDBService
from services.database_health_service import DatabaseHealthService
from services.diagnosis_service import DiagnosisService
from services.remediation_service import RemediationService
from services.execution_service import ExecutionService
from services.verification_service import VerificationService
from services.incident_history_service import IncidentHistoryService
from utils.logger import (
    bind_context, log_banner, log_divider,
    log_step_start, log_step_success, log_step_failure,
    log_info, timed_step
)


class DBFixAgent:

    def __init__(self):
        self.cmdb = CMDBService()
        self.health_service = DatabaseHealthService()
        self.diagnosis_service = DiagnosisService()
        self.remediation_service = RemediationService()
        self.execution_service = ExecutionService()
        self.verification_service = VerificationService()
        self.history_service = IncidentHistoryService()

    def execute(self, request: RCARequest):
        ctx = bind_context(
            ticket_id=request.ticket_id,
            correlation_id=str(uuid.uuid4())
        )
        total_start = time.perf_counter()

        log_banner(ctx, f"DB FIX AGENT STARTED  application={request.application}")

        try:
            # ── CMDB: Business Application ──────────────────────────────────
            with timed_step(ctx, "CMDB.get_business_application", application=request.application):
                application = self.cmdb.get_business_application(request.application, ctx=ctx)
            log_info(ctx, "Business application resolved", sys_id=application["sys_id"])

            # ── CMDB: Database Relationship ──────────────────────────────────
            with timed_step(ctx, "CMDB.get_database_relationship", parent_sys_id=application["sys_id"]):
                relationship = self.cmdb.get_database_relationship(application["sys_id"], ctx=ctx)
            log_info(ctx, "Database relationship resolved", child_sys_id=relationship["child"]["value"])

            # ── CMDB: PostgreSQL Instance ────────────────────────────────────
            with timed_step(ctx, "CMDB.get_postgres_instance", child_sys_id=relationship["child"]["value"]):
                database = self.cmdb.get_postgres_instance(relationship["child"]["value"], ctx=ctx)
            log_info(ctx, "PostgreSQL instance resolved", database=database["name"])

            # ── Health Check ─────────────────────────────────────────────────
            with timed_step(ctx, "DatabaseHealthService.get_database_health", database=database["name"]):
                health = self.health_service.get_database_health(database["name"], ctx=ctx)
            log_info(ctx, "Health snapshot retrieved",
                     status=health.get("status"),
                     active_connections=health.get("active_connections"),
                     cpu_usage=health.get("cpu_usage"),
                     memory_usage=health.get("memory_usage"),
                     slow_queries=health.get("slow_queries"),
                     deadlocks=health.get("deadlocks"))

            # ── Diagnosis ────────────────────────────────────────────────────
            with timed_step(ctx, "DiagnosisService.analyze"):
                issues = self.diagnosis_service.analyze(health)
            log_info(ctx, "Diagnosis complete", issue_count=len(issues),
                     issues=[i["issue"] for i in issues])

            # ── Remediation Plan ─────────────────────────────────────────────
            with timed_step(ctx, "RemediationService.generate_plan", issue_count=len(issues)):
                actions = self.remediation_service.generate_plan(issues, ctx=ctx)
            log_info(ctx, "Remediation plan generated", action_count=len(actions),
                     actions=[a["action"] for a in actions])

            # ── Execution ────────────────────────────────────────────────────
            with timed_step(ctx, "ExecutionService.execute", action_count=len(actions)):
                execution = self.execution_service.execute(actions)
            log_info(ctx, "Execution complete", result=execution)

            # ── Verification ─────────────────────────────────────────────────
            with timed_step(ctx, "VerificationService.verify", database=database["name"]):
                verification = self.verification_service.verify(database["name"], ctx=ctx)
            log_info(ctx, "Post-remediation verification",
                     status=verification.get("status"),
                     active_connections=verification.get("active_connections"),
                     cpu_usage=verification.get("cpu_usage"),
                     memory_usage=verification.get("memory_usage"),
                     slow_queries=verification.get("slow_queries"),
                     deadlocks=verification.get("deadlocks"))

            # ── Incident History ─────────────────────────────────────────────
            log_divider(ctx, f"SAVING INCIDENT HISTORY  action_count={len(actions)}")
            for action in actions:
                with timed_step(ctx, "IncidentHistoryService.save",
                                action=action["action"], status="SUCCESS"):
                    self.history_service.save(
                        ticket_id=request.ticket_id,
                        application=request.application,
                        action=action["action"],
                        status="SUCCESS",
                        ctx=ctx
                    )

            total_elapsed = time.perf_counter() - total_start
            log_banner(ctx, f"DB FIX AGENT COMPLETED  total_elapsed={total_elapsed:.3f}s  "
                            f"database={database['name']}  issues_found={len(issues)}  "
                            f"actions_taken={len(actions)}  final_status={verification.get('status')}")

            return {
                "ticket_id": request.ticket_id,
                "database": database["name"],
                "issues_found": issues,
                "actions": actions,
                "execution": execution,
                "verification": verification
            }

        except Exception as e:
            total_elapsed = time.perf_counter() - total_start
            log_banner(ctx, f"DB FIX AGENT FAILED  total_elapsed={total_elapsed:.3f}s  "
                            f"error={type(e).__name__}: {e}")
            raise
