"""Explicit Lean-checker discovery and bounded, fail-closed certificate checking."""

from __future__ import annotations

import math
import os
import shutil
import subprocess
from pathlib import Path


class CertificationError(ValueError):
    pass


def checker_path(explicit: Path | None = None) -> Path:
    if explicit is not None:
        candidate = explicit.resolve()
    else:
        installed = shutil.which("hypomnesis-check")
        candidate = (
            Path(installed)
            if installed
            else Path(__file__).resolve().parents[3] / "formal/.lake/build/bin/hypomnesis-check"
        )
    if not candidate.is_file() or not os.access(candidate, os.X_OK):
        raise CertificationError(
            f"vérificateur Lean introuvable ou non exécutable : {candidate}; "
            "construire formal avec lake build hypomnesis-check ou fournir --checker"
        )
    return candidate


def check_certificate(
    path: Path, *, checker: Path | None = None, timeout_seconds: float = 30.0
) -> str:
    if (
        isinstance(timeout_seconds, bool)
        or not math.isfinite(timeout_seconds)
        or timeout_seconds <= 0
    ):
        raise CertificationError("le délai du vérificateur doit être positif et fini")
    executable = checker_path(checker)
    try:
        result = subprocess.run(
            [str(executable), "check", str(path.resolve())],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise CertificationError(f"délai du vérificateur dépassé ({timeout_seconds}s)") from exc
    except (OSError, UnicodeError) as exc:
        raise CertificationError(f"échec du vérificateur : {exc}") from exc
    if result.returncode:
        label = {
            1: "certificat rejeté par le typage Lean",
            2: "programme hors du fragment Lean",
            3: "certificat mal formé pour Lean",
        }.get(result.returncode, "échec du vérificateur Lean")
        detail = (result.stderr or result.stdout).strip()
        raise CertificationError(f"{label} (code {result.returncode}) : {detail}")
    return result.stdout.strip()
