"""Host-selected contractual plugins; the M1 source never changes."""

import argparse
import json
from pathlib import Path

from hypomnesis.backends.python import PythonBackend
from hypomnesis.contracts.codec import TypeCodec
from hypomnesis.engine.language import Language, load_language
from hypomnesis.engine.procedure import run_procedure
from hypomnesis.engine.registry import ExtensionRegistry
from hypomnesis.session import Session

ROOT = Path(__file__).resolve().parents[2]
LANGUAGE = ROOT / "demo/languages/mecanique"
PROGRAM = ROOT / "demo/programs/mecanique/plaque_plugins.hyp"
PLUGINS = LANGUAGE / "plugins"


def configure(config: Path) -> tuple[Language, PythonBackend]:
    language = load_language(LANGUAGE, execute=False)
    for type_, identifier in (
        ("Plaque.demande", "thickness-demand"),
        ("float", "thickness-estimate"),
    ):
        schema = TypeCodec(language.session.checker, type_).schema
        schema["$id"] = f"https://schemas.example.org/mechanics/{identifier}/1.0.0"
        language.schemas.add(schema)
    manifest = json.loads(config.read_text(encoding="utf-8"))
    registry = ExtensionRegistry([manifest], schemas=language.schemas)
    extension = registry.prepare(manifest["id"], language.session.checker)
    if manifest["role"] != "Estimator" or manifest["signature"] != {
        "input": "Plaque.demande",
        "output": "float",
    }:
        raise ValueError("expected an Estimator with signature Plaque.demande -> float")
    backend = PythonBackend(extension)
    natives = language.session.natives.copy()
    backend.register(natives, "thickness.estimate")
    provider = f"{manifest['id']}@{manifest['version']}"
    natives.register("thickness.provider", 1, lambda _: provider)
    session = Session(natives)
    for source in language.plan.source_files():
        session.load_program(source.program)
    language.session = session
    return language, backend


def run_substitution(config: Path, out_dir: Path, *, mode: str = "dry-run"):
    language, backend = configure(config)
    report = run_procedure(
        language, PROGRAM.read_text(encoding="utf-8"), mode=mode, out_dir=out_dir
    )
    return {
        **report.to_json(),
        "estimator_plugin": backend.extension.manifest,
        "plugin_trace": backend.tracer.export(),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path, help="manifeste du fournisseur, sans changer le M1")
    parser.add_argument("--out", type=Path, default=ROOT / "demo/sortie/substitution")
    parser.add_argument("--mode", choices=("dry-run", "simulate", "production"), default="dry-run")
    args = parser.parse_args(argv)
    print(json.dumps(run_substitution(args.config, args.out, mode=args.mode), ensure_ascii=False))


if __name__ == "__main__":
    main()
