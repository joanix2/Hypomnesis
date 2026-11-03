import pytest

from hypomnesis.session import Session


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
