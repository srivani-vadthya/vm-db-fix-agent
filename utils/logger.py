import logging
import time
import uuid
from contextlib import contextmanager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger("DBFixAgent")

BANNER = "=" * 70
DIVIDER = "-" * 70


def bind_context(ticket_id: str, correlation_id: str = None) -> dict:
    return {
        "ticket_id": ticket_id,
        "correlation_id": correlation_id or str(uuid.uuid4())
    }


def _prefix(ctx: dict) -> str:
    return f"[ticket={ctx['ticket_id']}] [corr={ctx['correlation_id']}]"


def log_banner(ctx: dict, title: str):
    logger.info(BANNER)
    logger.info(f"{_prefix(ctx)} {title}")
    logger.info(BANNER)


def log_divider(ctx: dict, title: str):
    logger.info(DIVIDER)
    logger.info(f"{_prefix(ctx)} {title}")
    logger.info(DIVIDER)


def log_step_start(ctx: dict, step: str, **details):
    detail_str = "  ".join(f"{k}={v}" for k, v in details.items())
    logger.info(f"{_prefix(ctx)} [START] {step}  {detail_str}".strip())


def log_step_success(ctx: dict, step: str, elapsed: float, **details):
    detail_str = "  ".join(f"{k}={v}" for k, v in details.items())
    logger.info(f"{_prefix(ctx)} [OK]    {step}  elapsed={elapsed:.3f}s  {detail_str}".strip())


def log_step_failure(ctx: dict, step: str, elapsed: float, error: Exception, will_retry: bool = False):
    fate = "RETRYING" if will_retry else "FAILING"
    logger.error(
        f"{_prefix(ctx)} [ERROR] {step}  elapsed={elapsed:.3f}s  "
        f"fate={fate}  error={type(error).__name__}: {error}"
    )


def log_info(ctx: dict, message: str, **details):
    detail_str = "  ".join(f"{k}={v}" for k, v in details.items())
    logger.info(f"{_prefix(ctx)} {message}  {detail_str}".strip())


@contextmanager
def timed_step(ctx: dict, step: str, **start_details):
    log_step_start(ctx, step, **start_details)
    t0 = time.perf_counter()
    try:
        yield
        elapsed = time.perf_counter() - t0
        log_step_success(ctx, step, elapsed)
    except Exception as e:
        elapsed = time.perf_counter() - t0
        log_step_failure(ctx, step, elapsed, e, will_retry=False)
        raise
