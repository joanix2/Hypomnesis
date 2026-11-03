"""Certificates: the elaborated, annotated Core IR as JSON for an independent checker."""

from __future__ import annotations

from hypomnesis.certify.export import (
    CERTIFICATE_SCHEMA_ID,
    CERTIFICATE_VERSION,
    CertificateError,
    Json,
    export_certificate,
)
from hypomnesis.certify.load import load_definitions
from hypomnesis.session import Session


def session_certificate(session: Session) -> Json:
    """Certificate of everything elaborated in ``session``, prelude included."""
    return export_certificate(
        session.checker.types_by_qname.values(),
        session.definitions,
        program_start=session.prelude_definitions,
    )


__all__ = [
    "CERTIFICATE_SCHEMA_ID",
    "CERTIFICATE_VERSION",
    "CertificateError",
    "Json",
    "export_certificate",
    "load_definitions",
    "session_certificate",
]
