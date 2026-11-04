"""Enregistrer puis relire les échanges des périphériques simulés."""

from __future__ import annotations

import argparse
from pathlib import Path

from hypomnesis.effects.transports import FileTransport, MemoryTransport, replay
from hypomnesis.engine.language import load_language
from hypomnesis.engine.procedure import run_procedure


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    language = load_language(root / "demo/languages/ventilation")
    program = (root / "demo/programs/ventilation/salle_serveurs.hyp").read_text(encoding="utf-8")
    previous = set((args.output / "scenarios").glob("*.jsonl"))
    report = run_procedure(
        language,
        program,
        mode="production",
        out_dir=args.output,
        environment={"transport": "files"},
    )
    if report.stopped or any(o.state != "Completed" for o in report.commands):
        raise RuntimeError(
            f"scénario interrompu : {report.stopped or report.to_json()['commands']}"
        )
    paths = set((args.output / "scenarios").glob("*.jsonl")) - previous
    if len(paths) != 1:
        raise RuntimeError(f"un seul scénario attendu, trouvé : {paths}")
    path = paths.pop()
    target = MemoryTransport(language.schemas)
    count = replay(FileTransport(path, language.schemas), target)
    recorded = FileTransport(path, language.schemas)
    for _ in range(count):
        if target.receive() != recorded.receive():
            raise RuntimeError("le rejeu diffère de l'enregistrement")
    print(f"{count} messages rejoués à l'identique : {path}")


if __name__ == "__main__":
    main()
