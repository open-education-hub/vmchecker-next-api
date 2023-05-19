from typing import Any, Dict, Union

import sentry_sdk
from django.conf import settings
from sentry_sdk.integrations.django import DjangoIntegration


def traces_sampler(ctx: Dict[str, Any]) -> Union[float, int, bool]:
    # Other kinds of transactions don't have a URL
    url = ""

    if ctx["parent_sampled"] is not None:
        # If this transaction has a parent, we usually want to sample it
        # if and only if its parent was sampled.
        return ctx["parent_sampled"]
    operation = ctx["transaction_context"]["op"]
    if "wsgi_environ" in ctx:
        # Get the URL for WSGI requests
        url = ctx["wsgi_environ"].get("PATH_INFO", "")
    elif "asgi_scope" in ctx:
        # Get the URL for ASGI requests
        url = ctx["asgi_scope"].get("path", "")

    if operation == "http.server":
        # Conditions only relevant to operation "http.server"
        if url.startswith("/api/v1/health"):
            return 0  # Don't trace any of these transactions
    return 0.1  # Trace 10% of other transactions


def initialize():
    if settings.SENTRY_SDK_DSN:
        sentry_sdk.init(
            dsn=settings.SENTRY_SDK_DSN,
            integrations=[
                DjangoIntegration(),
            ],
            traces_sampler=traces_sampler,
            send_default_pii=True,
        )
