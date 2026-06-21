from fastapi import Request

async def calculate_request_size(request: Request) -> int:
    request_line_size = len(request.method) + len(str(request.url)) + len("HTTP/1.1") + 4
    headers_size = sum(len(k) + len(v) + 4 for k, v in request.headers.items()) + 2
    body = await request.body()
    body_size = len(body)
    return request_line_size + headers_size + body_size
