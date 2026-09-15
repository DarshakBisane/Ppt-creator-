"""Request and correlation ID middleware."""

import re
import uuid
from collections.abc import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from backend.app.logging_config import request_id_ctx

# Strict regex to ensure client-supplied request IDs are safe and bounded
REQUEST_ID_REGEX = re.compile(r"^[a-zA-Z0-9_\-]{1,64}$")
REQUEST_ID_HEADER = "X-Request-ID"


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Middleware to assign or validate request IDs for every HTTP request."""

    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]) -> Response:
        incoming_id = request.headers.get(REQUEST_ID_HEADER)

        if incoming_id and REQUEST_ID_REGEX.match(incoming_id):
            request_id = incoming_id
        else:
            request_id = str(uuid.uuid4())

        # Set request state and logging context
        request.state.request_id = request_id
        token = request_id_ctx.set(request_id)

        try:
            response = await call_next(request)
            response.headers[REQUEST_ID_HEADER] = request_id
            return response
        finally:
            request_id_ctx.reset(token)
