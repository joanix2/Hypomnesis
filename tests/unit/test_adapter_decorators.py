"""Explicit, local runtime discovery of Python I/O endpoints."""

import pytest

from hypomnesis.engine.adapters import AdapterRegistry, environment, sensor
from hypomnesis.engine.errors import LanguageError
from hypomnesis.engine.language import load_language
from hypomnesis.engine.procedure import run_procedure


def module(tmp_path, text):
    path = tmp_path / "io.py"
    path.write_text(text)
    return AdapterRegistry.load(tmp_path, ["io.py"])


def test_decorators_preserve_functions_and_register_no_global_state():
    def fn(env, identifier):
        return env, identifier

    assert sensor("s")(fn) is fn
    assert fn(1, "s") == (1, "s")
    assert AdapterRegistry().identifiers("sensor") == []
    with pytest.raises(LanguageError, match="plusieurs"):
        environment(fn)


def test_all_endpoint_roles_are_discovered_only_in_explicit_modules(tmp_path):
    registry = module(
        tmp_path,
        """
from hypomnesis.engine.adapters import sensor, actuator, environment, transcriber
@environment
def env(options, out):
    return options
@sensor("s")
def read(env, identifier):
    return env[identifier]
@actuator("a")
def factory(env):
    return env
@transcriber
def translate(text):
    return "let x = 1"
""",
    )
    assert registry.get("sensor", "s")({"s": 42}, "s") == 42
    assert registry.get("environment")({"key": "value"}, tmp_path) == {"key": "value"}
    assert registry.get("transcriber")("request") == "let x = 1"
    assert registry.identifiers("actuator") == ["a"]
    with pytest.raises(LanguageError, match="non déclaré"):
        registry.get("sensor", "unknown")


def test_dataclass_environment_and_function_aliases_use_normal_python_semantics(tmp_path):
    registry = module(
        tmp_path,
        """
from __future__ import annotations
from dataclasses import dataclass
from hypomnesis.engine.adapters import environment, sensor
@environment
@dataclass
class Env:
    options: dict
    out: object
@sensor("s")
def read(env, identifier):
    return env.options[identifier]
alias = read
""",
    )
    env = registry.get("environment")({"s": 42}, tmp_path)
    assert registry.get("sensor", "s")(env, "s") == 42


@pytest.mark.parametrize(
    "text, message",
    [
        ("def undecorated(): pass", "aucun adaptateur"),
        (
            'from hypomnesis.engine.adapters import sensor\n@sensor("s")\ndef read(): pass',
            "signature incompatible",
        ),
        (
            "from hypomnesis.engine.adapters import sensor\n"
            '@sensor("s")\nasync def read(a, b): pass',
            "asynchrone",
        ),
        (
            'from hypomnesis.engine.adapters import sensor\n@sensor("s")\ndef a(x, y): pass\n'
            '@sensor("s")\ndef b(x, y): pass',
            "dupliqué",
        ),
    ],
)
def test_invalid_endpoints_are_explicit_errors(tmp_path, text, message):
    with pytest.raises(LanguageError, match=message):
        module(tmp_path, text)


def test_imports_do_not_implicitly_grant_or_register_python_io(tmp_path):
    dependency = tmp_path / "base"
    dependency.mkdir()
    (dependency / "langage.hyp").write_text(
        'language base = { version = "1"; adapters = ["io.py"] }'
    )
    (dependency / "io.py").write_text('raise RuntimeError("must not import")')
    root = tmp_path / "root"
    root.mkdir()
    (root / "langage.hyp").write_text(
        'language root = { version = "1"; imports = ["../base"]; '
        'procedure = { kind = "program"; entry = "main" } }'
    )
    report = run_procedure(load_language(root), "let main = Effect.return 42", out_dir=tmp_path)
    assert report.result == 42


def test_factory_result_must_match_decorated_identifier(tmp_path):
    (tmp_path / "langage.hyp").write_text(
        'language test = { version = "1"; adapters = ["io.py"]; '
        'procedure = { kind = "program"; entry = "main" } }'
    )
    (tmp_path / "io.py").write_text(
        "from hypomnesis.engine.adapters import actuator\n"
        '@actuator("a")\ndef factory(env): return None'
    )
    with pytest.raises(LanguageError, match="fabrique d'actionneur incompatible"):
        run_procedure(load_language(tmp_path), "let main = Effect.return ()", out_dir=tmp_path)
