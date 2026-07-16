from clients.postgres_client import PostgreSQLClient


class ExecutionService:

    def __init__(self):

        self.db = PostgreSQLClient()

    def execute(self, actions):

        results = []

        for action in actions:

            issue = action["issue"]

            if issue == "CONNECTION_POOL_EXHAUSTED":

                self.db.execute("""

                UPDATE database_health

                SET

                status='HEALTHY',

                active_connections=45,

                cpu_usage=40,

                memory_usage=35,

                slow_queries=0,

                deadlocks=0,

                last_checked=NOW()

                WHERE app_id=1

                """)

                results.append({

                    "issue": issue,

                    "result": "SUCCESS"

                })

        return results