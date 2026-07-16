import time
import uuid
from datetime import datetime, timezone

from models.request import RCARequest
from services.cmdb_service import CMDBService
from services.database_health_service import DatabaseHealthService
from services.diagnosis_service import DiagnosisService
from services.remediation_service import RemediationService
from services.execution_service import ExecutionService
from services.verification_service import VerificationService
from services.incident_history_service import IncidentHistoryService
from utils.logger import (
    bind_context,
    log_start_banner, log_final_summary, log_failure_banner,
    log_step_header, log_step_start, log_step_success, log_step_failure,
    log_info, log_health_summary, log_diagnosis_summary,
    log_verification_result, log_execution_timeline,
    record_timing, DIVIDER
)
from utils.logger import logger


class DBFixAgent:

    def __init__(self):
        self.cmdb               = CMDBService()
        self.health_service     = DatabaseHealthService()
        self.diagnosis_service  = DiagnosisService()
        self.remediation_service = RemediationService()
        self.execution_service  = ExecutionService()
        self.verification_service = VerificationService()
        self.history_service    = IncidentHistoryService()

    def execute(self, request: RCARequest):
        ctx = bind_context(
            ticket_id=request.ticket_id,
            correlation_id=str(uuid.uuid4())
        )
        total_start = time.perf_counter()
        timestamp   = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        log_start_banner(
            ctx,
            ticket_id=request.ticket_id,
            application=request.application,
            technology=request.technology,
            correlation_id=ctx["correlation_id"],
            timestamp=timestamp
        )

        try:
            # ── STEP 01 — CMDB Business Application ──────────────────────────
            log_step_header(1, "CMDB — BUSINESS APPLICATION LOOKUP",
                            "Resolve the Business Application CI from ServiceNow CMDB")
            t0 = time.perf_counter()
            application = self.cmdb.get_business_application(request.application, ctx=ctx)
            record_timing(ctx, "CMDB Lookup", time.perf_counter() - t0)
            log_info(ctx, "Business Application resolved",
                     step="CMDB", sys_id=application["sys_id"],
                     name=application.get("name", request.application))

            # ── STEP 02 — CMDB Relationship ───────────────────────────────────
            log_step_header(2, "CMDB — DATABASE RELATIONSHIP LOOKUP",
                            "Discover the database CI linked to the Business Application")
            t0 = time.perf_counter()
            relationship = self.cmdb.get_database_relationship(application["sys_id"], ctx=ctx)
            record_timing(ctx, "Relationship Lookup", time.perf_counter() - t0)
            log_info(ctx, "Database relationship resolved",
                     step="CMDB", child_sys_id=relationship["child"]["value"])

            # ── STEP 03 — PostgreSQL Instance Discovery ───────────────────────
            log_step_header(3, "DISCOVER POSTGRESQL INSTANCE",
                            "Discover the PostgreSQL CI associated with the Business Application")
            t0 = time.perf_counter()
            database = self.cmdb.get_postgres_instance(relationship["child"]["value"], ctx=ctx)
            record_timing(ctx, "PostgreSQL Discovery", time.perf_counter() - t0)
            log_info(ctx, "PostgreSQL instance discovered",
                     step="CMDB", database=database["name"],
                     sys_id=database.get("sys_id", "N/A"))

            # ── STEP 04 — Database Health Read ────────────────────────────────
            log_step_header(4, "READ DATABASE HEALTH",
                            "Retrieve current health metrics from Neon PostgreSQL")
            t0 = time.perf_counter()
            health = self.health_service.get_database_health(database["name"], ctx=ctx)
            record_timing(ctx, "Database Health Read", time.perf_counter() - t0)
            initial_status = health.get("status", "UNKNOWN")
            log_health_summary(ctx, "DATABASE HEALTH SNAPSHOT", health)

            # ── STEP 05 — Diagnosis ───────────────────────────────────────────
            log_step_header(5, "DIAGNOSIS",
                            "Analyse health metrics and identify issues requiring remediation")
            t0 = time.perf_counter()
            issues = self.diagnosis_service.analyze(health)
            record_timing(ctx, "Diagnosis", time.perf_counter() - t0)
            log_diagnosis_summary(ctx, issues)

            # ── STEP 06 — Remediation Plan ────────────────────────────────────
            log_step_header(6, "GENERATE REMEDIATION PLAN",
                            "Look up remediation rules and build an action plan for each issue")
            t0 = time.perf_counter()
            actions = self.remediation_service.generate_plan(issues, ctx=ctx)
            record_timing(ctx, "Remediation Rule Lookup", time.perf_counter() - t0)
            logger.info(DIVIDER)
            logger.info(f"  REMEDIATION PLAN  ({len(actions)} action(s))")
            logger.info(DIVIDER)
            for i, a in enumerate(actions, 1):
                logger.info(f"  [{i}] Issue    : {a['issue']:<30}  "
                            f"Action: {a['action']}  Automated: {a['automated']}")
            logger.info(DIVIDER)

            # ── STEP 07 — Execute Remediation ─────────────────────────────────
            log_step_header(7, "EXECUTE REMEDIATION",
                            "Apply each remediation action against the target database")
            t0 = time.perf_counter()
            execution = self.execution_service.execute(actions, ctx=ctx)
            record_timing(ctx, "Execution", time.perf_counter() - t0)

            # ── STEP 08 — Verification ────────────────────────────────────────
            log_step_header(8, "POST-REMEDIATION VERIFICATION",
                            "Re-read database health to confirm all issues have been resolved")
            t0 = time.perf_counter()
            verification = self.verification_service.verify(database["name"], ctx=ctx)
            record_timing(ctx, "Verification", time.perf_counter() - t0)
            passed = verification.get("status") == "HEALTHY"
            log_verification_result(ctx, verification, passed)

            # ── STEP 09 — Save Incident History ───────────────────────────────
            log_step_header(9, "SAVE INCIDENT HISTORY",
                            "Persist remediation actions and outcomes to the audit trail")
            t0 = time.perf_counter()
            for action in actions:
                self.history_service.save(
                    ticket_id=request.ticket_id,
                    application=request.application,
                    action=action["action"],
                    status="SUCCESS",
                    ctx=ctx
                )
            record_timing(ctx, "Incident History", time.perf_counter() - t0)

            total_elapsed = time.perf_counter() - total_start

            log_execution_timeline(ctx, total_elapsed)

            log_final_summary(
                ctx,
                ticket_id=request.ticket_id,
                application=request.application,
                database=database["name"],
                problem_domain=request.problem_domain,
                initial_status=initial_status,
                final_status=verification.get("status", "UNKNOWN"),
                issues_found=len(issues),
                actions_executed=len(actions),
                verification="PASSED" if passed else "FAILED",
                total_elapsed=total_elapsed
            )

            return {
                "ticket_id":   request.ticket_id,
                "database":    database["name"],
                "issues_found": issues,
                "actions":     actions,
                "execution":   execution,
                "verification": verification
            }

        except Exception as e:
            total_elapsed = time.perf_counter() - total_start
            log_failure_banner(ctx, e, total_elapsed)
            raise
