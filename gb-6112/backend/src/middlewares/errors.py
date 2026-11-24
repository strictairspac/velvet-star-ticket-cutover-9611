import logging
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


async def catch_errors(request, call_next):
    try:
        response = await call_next(request)
    except Exception:
        diagnostic = getattr(request.state, "request_id", "")
        logger.exception("Unhandled request error %s", diagnostic)
        response = JSONResponse({"detail": "服务处理失败，请稍后重试", "request_id": diagnostic}, status_code=500)
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response
