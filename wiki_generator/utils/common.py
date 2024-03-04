import json
from functools import wraps


def load_request(wrapped):
    def decorator(f):
        @wraps(f)
        async def decorated_function(request, *args, **kwargs):
            try:
                request.data = await request.json()
            except json.decoder.JSONDecodeError:
                request.data = {}
            return await f(request, *args, **kwargs)

        return decorated_function

    return decorator(wrapped)


