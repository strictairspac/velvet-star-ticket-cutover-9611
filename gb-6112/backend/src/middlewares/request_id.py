from uuid import uuid4


async def request_id(request, call_next):
    identity = uuid4().hex
    request.state.request_id = identity
    response = await call_next(request)
    response.headers["X-Request-ID"] = identity
    return response
