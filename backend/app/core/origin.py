"""Same-origin protection for cookie-authenticated mutations."""

from urllib.parse import urlsplit

from fastapi import Request

SAFE = frozenset({"GET", "HEAD", "OPTIONS"})


def allowed_origin(request: Request, origins: frozenset[str]) -> bool:
    supplied = request.headers.getlist("origin")
    if supplied:
        return len(supplied) == 1 and supplied[0] in origins
    referers = request.headers.getlist("referer")
    if len(referers) != 1:
        return False
    try:
        url = urlsplit(referers[0])
    except ValueError:
        return False
    return bool(url.netloc) and f"{url.scheme}://{url.netloc}" in origins
