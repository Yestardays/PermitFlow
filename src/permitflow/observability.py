import logging
import sys

from prometheus_client import Counter, Histogram
from pythonjsonlogger.json import JsonFormatter

REQUESTS = Counter("permitflow_requests_total", "Requests", ["kind", "status"])
LATENCY = Histogram("permitflow_request_duration_seconds", "Request latency", ["kind"])
JIRA_SUBMISSIONS = Counter("permitflow_jira_submissions_total", "Jira submissions", ["status"])


def configure_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level.upper())
