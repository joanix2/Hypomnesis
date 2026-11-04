"""The symbolic distribution must never depend on natural-language generation."""

import ast
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GENERATION_MODULES = {
    "hypomnesis_codegen",
    "jinja2",
    "sklearn",
    "ollama",
    "matplotlib",
    "scipy",
}


def test_core_has_no_generation_imports():
    for path in (ROOT / "src" / "hypomnesis").rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            names = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            assert not any(name.split(".")[0] in GENERATION_MODULES for name in names), path


def test_core_distribution_contains_no_generation_dependency_or_module():
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    requirements = [
        *project["dependencies"],
        *(r for group in project["optional-dependencies"].values() for r in group),
    ]
    for requirement in requirements:
        assert not any(
            name in requirement
            for name in ("codegen", "jinja2", "scikit-learn", "ollama", "matplotlib", "scipy")
        ), requirement
    assert "llm" not in project["optional-dependencies"]
    assert not (ROOT / "src" / "hypomnesis" / "llm").exists()
