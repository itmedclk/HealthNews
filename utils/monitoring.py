import os
from typing import Optional

import sentry_sdk


def init_sentry(dsn: Optional[str] = None, environment: str = "production") -> None:
    """Initialize Sentry error monitoring if DSN is provided."""
    dsn = dsn or os.getenv("SENTRY_DSN", "")
    if not dsn:
        return
    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        traces_sample_rate=0.0,
    )
