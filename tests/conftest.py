import os
import shutil
from pathlib import Path

import pytest

from hypomnesis.session import Session


def require_lake() -> str:
    lake = shutil.which("lake") or str(Path.home() / ".elan/bin/lake")
    if not Path(lake).is_file():
        if os.environ.get("HYPOMNESIS_REQUIRE_LEAN") == "1":
            pytest.fail("lake missing; Lean model checks are mandatory")
        pytest.skip("lake not installed; executable models are mandatory in proofs CI")
    return lake


@pytest.fixture(scope="session")
def lean_lake() -> str:
    return require_lake()


@pytest.fixture(scope="session")
def _prelude_session() -> Session:
    return Session()


@pytest.fixture
def session() -> Session:
    """A fresh session with the prelude loaded (parsing the prelude once)."""
    return Session()


def run(source: str) -> dict[str, str]:
    """Load ``source`` in a fresh session; map each binding name to its rendering."""
    result = Session().load(source)
    return {b.display_name: b.render() for b in result.bindings}
