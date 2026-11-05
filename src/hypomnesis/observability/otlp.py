"""Network restrictions shared by the explicitly configured local exporters."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from urllib.parse import urlsplit

if TYPE_CHECKING:
    from requests import Session


def validate_endpoint(endpoint: str) -> None:
    url = urlsplit(endpoint)
    _ = url.port
    if (
        url.scheme not in ("http", "https")
        or url.hostname not in ("localhost", "127.0.0.1", "::1")
        or url.username is not None
        or url.password is not None
        or url.query
        or url.fragment
    ):
        raise ValueError("OTLP endpoint must be an explicit local HTTP(S) URL")


def local_session() -> Session:
    from requests import HTTPError, Session

    class LocalSession(Session):
        def request(self, *args: Any, **kwargs: Any) -> Any:
            kwargs["allow_redirects"] = False
            response = super().request(*args, **kwargs)
            if 300 <= response.status_code < 400:
                raise HTTPError(
                    f"OTLP collector redirect refused (HTTP {response.status_code})",
                    response=response,
                )
            return response

    session = LocalSession()
    session.trust_env = False
    return session
