"""Run the two-sensor simulated feedback scenario and retain its trace."""

import argparse
from pathlib import Path

from hypomnesis.engine.language import load_language
from hypomnesis.engine.procedure import render, run_procedure


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--panne", action="store_true")
    parser.add_argument("--sortie", type=Path, default=Path("demo/sortie/feedback"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    language = load_language(root / "demo/languages/ventilation")
    program = (root / "demo/programs/ventilation/salle_serveurs.hyp").read_text()
    report = run_procedure(
        language,
        program,
        mode="production",
        out_dir=args.sortie,
        environment={"panne": args.panne, "transport": "files"},
    )
    print(render(report))


if __name__ == "__main__":
    main()
