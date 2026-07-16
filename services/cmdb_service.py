from clients.servicenow_client import ServiceNowClient
from utils.logger import log_step_start, log_step_success, log_step_failure
import time


class CMDBService:

    def __init__(self):
        self.client = ServiceNowClient()

    def get_business_application(self, application_name: str, ctx: dict = None):
        step = "CMDBService.get_business_application"
        t0 = time.perf_counter()
        try:
            result = self.client.get(
                table="cmdb_ci_business_app",
                query=f"name={application_name}",
                ctx=ctx
            )
            if not result:
                raise Exception(f"{application_name} not found.")
            if ctx:
                log_step_success(ctx, step, time.perf_counter() - t0, sys_id=result[0]["sys_id"])
            return result[0]
        except Exception as e:
            if ctx:
                log_step_failure(ctx, step, time.perf_counter() - t0, e)
            raise

    def get_database_relationship(self, parent_sys_id: str, ctx: dict = None):
        step = "CMDBService.get_database_relationship"
        t0 = time.perf_counter()
        try:
            result = self.client.get(
                table="cmdb_rel_ci",
                query=f"parent={parent_sys_id}",
                ctx=ctx
            )
            if not result:
                raise Exception("No relationship found.")
            if ctx:
                log_step_success(ctx, step, time.perf_counter() - t0,
                                 child_sys_id=result[0]["child"]["value"])
            return result[0]
        except Exception as e:
            if ctx:
                log_step_failure(ctx, step, time.perf_counter() - t0, e)
            raise

    def get_postgres_instance(self, child_sys_id: str, ctx: dict = None):
        step = "CMDBService.get_postgres_instance"
        t0 = time.perf_counter()
        try:
            result = self.client.get(
                table="cmdb_ci_db_postgresql_instance",
                query=f"sys_id={child_sys_id}",
                ctx=ctx
            )
            if not result:
                raise Exception("Database CI not found.")
            if ctx:
                log_step_success(ctx, step, time.perf_counter() - t0,
                                 database=result[0]["name"])
            return result[0]
        except Exception as e:
            if ctx:
                log_step_failure(ctx, step, time.perf_counter() - t0, e)
            raise
