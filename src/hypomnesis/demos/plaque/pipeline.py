"""Démonstrateur MVP (cahier des charges §16.2) : une plaque de bout en bout.

    « Crée une plaque de 120 × 80 mm, estime son épaisseur, vérifie sa validité
      et exporte sa géométrie. »

Chaque étape utilise une couche du framework :

1. transcription de la demande en programme Hypomnesis typé (`Plaque.demande`) ;
2. connaissances : dimensions observées, épaisseur inconnue (métavariable) ;
3. estimation par un estimateur interchangeable (support « estimé ») ;
4. résolution : problème construit à partir des constantes du DSL, résolu par Z3,
   solution **revérifiée** indépendamment du solveur ;
5. validation par les règles écrites dans le DSL ;
6. commande d'export contrôlée (contrat, permission, contraintes, mode) ;
7. rapport : chaque conclusion expliquée par sa provenance, journal et traces ;
8. révision optionnelle : une mesure de l'épaisseur remplace l'estimation.

Le domaine (`domaine.hyp`) et ses contrats sont un exemple d'instance M2 : le
noyau n'en sait rien.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from fractions import Fraction
from importlib.resources import files
from pathlib import Path
from typing import Any

from hypomnesis.backends import z3_solver
from hypomnesis.contracts.registry import SchemaRegistry
from hypomnesis.effects.dispatcher import Actuator, Dispatcher, Outcome
from hypomnesis.epistemics.knowledge import KnowledgeBase
from hypomnesis.ir.problem import Constraint, Problem, Variable
from hypomnesis.observability.trace import Tracer
from hypomnesis.runtime.values import Variant, iter_list, show
from hypomnesis.session import Session

DOMAIN = files("hypomnesis.demos.plaque")
EXPORT_SCHEMA = "https://schemas.example.org/hypomnesis/geometry.export/1.0.0"
EXPORT_RESULT_SCHEMA = "https://schemas.example.org/hypomnesis/geometry.export.result/1.0.0"
EXPORT_PERMISSION = "actuator:geometry.export"


# ------------------------------------------------------------- transcription


class TranscriptionError(ValueError):
    pass


@dataclass(frozen=True)
class Transcription:
    program: str
    transcriber: str


def transcribe(request: str) -> Transcription:
    """Transcripteur déterministe (règles), substituable par un LLM (HYP-081).

    Produit un programme Hypomnesis ; c'est le vérificateur de types, pas le
    transcripteur, qui décide s'il est acceptable (§14.3).
    """
    dims = re.search(r"(\d+(?:[.,]\d+)?)\s*[x×*]\s*(\d+(?:[.,]\d+)?)\s*mm", request)
    if not dims:
        raise TranscriptionError("dimensions « L × H mm » introuvables dans la demande")
    width, height = (float(g.replace(",", ".")) for g in dims.groups())
    thickness = re.search(r"épaisseur (?:de )?(\d+(?:[.,]\d+)?)\s*mm", request)
    text = request.lower()
    actions = [
        name
        for name, words in (
            ("Estimer", ("estime",)),
            ("Verifier", ("vérifie", "valide")),
            ("Exporter", ("export",)),
        )
        if any(w in text for w in words)
    ]
    epaisseur = f"Some {float(thickness.group(1).replace(',', '.'))!r}" if thickness else "None"
    program = (
        "let demande = {\n"
        f"  Plaque.actions = [{'; '.join('Plaque.' + a for a in actions)}];\n"
        f"  largeur = {width!r};\n"
        f"  hauteur = {height!r};\n"
        f"  epaisseur = {epaisseur};\n"
        "}\n"
    )
    return Transcription(program, "règles (déterministe, sans LLM)")


# ---------------------------------------------------------------- estimators


@dataclass(frozen=True)
class Estimator:
    id: str
    version: str
    confidence: float

    def estimate(self, width: float, height: float) -> float:
        if self.id == "regle":  # épaisseur ≈ petit côté / 25
            return round(min(width, height) / 25, 2)
        area = width * height  # abaque par surface
        return 2.0 if area < 5_000 else 3.0 if area < 15_000 else 5.0

    @property
    def origin(self) -> str:
        return f"estimateur {self.id} v{self.version}"


ESTIMATORS = {
    "regle": Estimator("regle", "1", 0.6),
    "abaque": Estimator("abaque", "1", 0.7),
}


# -------------------------------------------------------------------- export


def export_actuator(out_dir: Path) -> Actuator:
    out_dir = out_dir.resolve()

    def constraints(payload: Mapping[str, Any]) -> list[str]:
        target = (out_dir / payload["path"]).resolve()
        problems = []
        if out_dir not in target.parents:
            problems.append("chemin hors du répertoire de sortie")
        if not payload["path"].endswith("." + payload["format"]):
            problems.append("extension différente du format")
        return problems

    def execute(payload: Mapping[str, Any]) -> dict[str, Any]:
        part = payload["part"]
        path = out_dir / payload["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        if payload["format"] == "json":
            text = json.dumps(part, indent=2, ensure_ascii=False)
        else:
            w, h = part["width_mm"], part["height_mm"]
            text = (
                f'<svg xmlns="http://www.w3.org/2000/svg" width="{w + 20}mm" height="{h + 20}mm" '
                f'viewBox="-10 -10 {w + 20} {h + 20}">\n'
                f'  <rect x="0" y="0" width="{w}" height="{h}" fill="none" stroke="black"/>\n'
                f'  <text x="{w / 2}" y="{h / 2}" text-anchor="middle" font-size="6">'
                f"{part['name']} {w}×{h}×{part['thickness_mm']} mm</text>\n</svg>\n"
            )
        path.write_text(text, encoding="utf-8")
        return {"status": "written", "path": str(path), "bytes": len(text.encode())}

    return Actuator(
        id="geometry.export",
        permission=EXPORT_PERMISSION,
        command_schema=EXPORT_SCHEMA,
        result_schema=EXPORT_RESULT_SCHEMA,
        execute=execute,
        constraints=constraints,
        simulate=lambda p: {"status": "simulated", "path": p["path"]},
    )


def schema_registry() -> SchemaRegistry:
    registry = SchemaRegistry.with_builtin_schemas()
    for name in ("geometry.export-1.0.0.json", "geometry.export.result-1.0.0.json"):
        registry.add(json.loads(DOMAIN.joinpath(name).read_text(encoding="utf-8")))
    return registry


# ------------------------------------------------------------------ pipeline


@dataclass
class Report:
    request: str
    transcription: Transcription
    kb: KnowledgeBase
    tracer: Tracer
    steps: list[tuple[str, str]] = field(default_factory=list)
    commands: list[Outcome] = field(default_factory=list)
    verdict: str = ""
    revision: list[str] = field(default_factory=list)
    #: Explication de la validité avant révision (support « estimé »).
    explanation_before: list[str] = field(default_factory=list)

    def step(self, name: str, detail: str) -> None:
        self.steps.append((name, detail))

    def to_json(self) -> dict[str, Any]:
        kb = self.kb
        return {
            "request": self.request,
            "program": self.transcription.program,
            "transcriber": self.transcription.transcriber,
            "steps": [{"step": s, "detail": d} for s, d in self.steps],
            "knowledge": {
                key: {
                    "value": f.value,
                    "method": f.method,
                    "support": kb.support(key).label,
                    "confidence": round(kb.confidence(key), 3),
                    "sources": [s.origin for s in kb.sources_of(key)],
                }
                for key, f in kb.facts.items()
            },
            "unknowns": {k: u.description for k, u in kb.unknowns.items()},
            "commands": [
                {"id": o.command.id, "states": o.states, "result": o.result} for o in self.commands
            ],
            "verdict": self.verdict,
            "revision": self.revision,
            "explanation_before_revision": self.explanation_before,
            "journal": [
                {"seq": e.seq, "kind": e.kind, "key": e.key, "detail": e.detail} for e in kb.journal
            ],
            "trace": self.tracer.export(),
        }


def run(
    request: str,
    *,
    estimator: str = "regle",
    mode: str = "dry-run",
    out_dir: Path = Path("sortie-plaque"),
    masse_max: float = 0.5,
    permissions: frozenset[str] = frozenset({EXPORT_PERMISSION}),
    mesure: float | None = None,
) -> Report:
    tracer = Tracer()
    kb = KnowledgeBase()
    transcription = transcribe(request)
    report = Report(request, transcription, kb, tracer)

    with tracer.span("hypomnesis.run", domaine="plaque", mode=mode):
        # 1. Transcription et typage
        with tracer.span("llm.transcribe", transcripteur=transcription.transcriber):
            pass
        with tracer.span("language.typecheck"):
            session = Session()
            session.load(DOMAIN.joinpath("domaine.hyp").read_text(encoding="utf-8"))
            binding = session.load(transcription.program).bindings[0]
        report.step("programme", f"{binding.type} — transcription par {transcription.transcriber}")
        demande = session.value("demande")
        width = demande.get("largeur")
        height = demande.get("hauteur")
        wants = {a.tag for a in iter_list(demande.get("actions"))}

        # 2. Connaissances : observé / inconnu
        kb.observe("plaque.largeur", width, "demande utilisateur")
        kb.observe("plaque.hauteur", height, "demande utilisateur")
        given = demande.get("epaisseur")
        if given.tag == "Some":
            kb.observe("plaque.epaisseur", given.arg, "demande utilisateur")
        else:
            kb.unknown("plaque.epaisseur", "non précisée dans la demande")
        report.step("connaissances", f"largeur {width} mm, hauteur {height} mm (observées)")

        # 3. Estimation
        if "plaque.epaisseur" in kb.unknowns and "Estimer" in wants:
            est = ESTIMATORS[estimator]
            with tracer.span("estimator.predict", plugin=est.id, version=est.version):
                guess = est.estimate(width, height)
            kb.estimate("plaque.epaisseur_estimee", guess, est.origin, est.confidence)
            report.step("estimation", f"{guess} mm par {est.origin} (confiance {est.confidence})")

            # 4. Résolution : constantes lues dans le DSL, solution revérifiée
            problem = plate_problem(session, width, height, masse_max, guess)
            with tracer.span("solver.solve", solver=z3_solver.NAME) as span:
                solution = z3_solver.solve(problem)
                span.attributes["status"] = solution.status
            if solution.status != "sat":
                report.step(
                    "résolution", f"aucune épaisseur ne satisfait les règles ({solution.status})"
                )
                report.verdict = "Impossible"
                return report
            if solution.violations:  # le certificat de Z3 ne passe pas la vérification
                raise RuntimeError(f"solution Z3 refusée : {solution.violations}")
            t = float(solution.assignment["epaisseur"])
            kb.derive(
                "plaque.epaisseur",
                t,
                "résolu par Z3 au plus près de l'estimation, solution revérifiée",
                ["plaque.largeur", "plaque.hauteur", "plaque.epaisseur_estimee"],
            )
            report.step(
                "résolution", f"{t} mm (épaisseur standard la plus proche respectant les règles)"
            )

        # 5. Validation par les règles du DSL
        if "Verifier" in wants and "plaque.epaisseur" in kb.facts:
            validate(session, kb, report, masse_max)

        # 6. Export contrôlé
        if "Exporter" in wants and report.verdict == "Valide":
            dispatcher = Dispatcher(
                schema_registry(), set(permissions), mode, on_transition=_trace_transition(tracer)
            )
            dispatcher.register(export_actuator(out_dir))
            for fmt in ("svg", "json"):
                payload = export_payload(kb, fmt)
                with tracer.span("actuator.execute", actuator="geometry.export", format=fmt):
                    command = dispatcher.command("geometry.export", payload)
                    outcome = dispatcher.dispatch(command)
                report.commands.append(outcome)
            report.step("export", ", ".join(f"{o.command.id} {o.state}" for o in report.commands))

        # 7. Révision : une mesure arrive
        if mesure is not None:
            if "plaque.valide" in kb.facts:
                report.explanation_before = kb.explain("plaque.valide")
            revise(session, kb, report, masse_max, mesure)

    if report.commands or mode == "production":
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "rapport.json").write_text(
            json.dumps(report.to_json(), indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )
    return report


def plate_problem(
    session: Session, width: float, height: float, masse_max: float, guess: float
) -> Problem:
    """Problème « épaisseur » construit à partir des constantes du domaine Hypomnesis."""
    density = Fraction(str(session.value("Plaque.densite_acier")))
    t_min = Fraction(str(session.value("Plaque.epaisseur_min")))
    slender = Fraction(str(session.value("Plaque.elancement_max")))
    choices = tuple(
        Fraction(str(x)) for x in iter_list(session.value("Plaque.epaisseurs_standard"))
    )
    w, h = Fraction(str(width)), Fraction(str(height))
    return Problem(
        variables=(Variable("epaisseur", lower=t_min, choices=choices),),
        constraints=(
            # petit côté / épaisseur ≤ élancement max  ⇔  élancement max · e ≥ petit côté
            Constraint("élancement", (("epaisseur", slender),), ">=", min(w, h)),
            # largeur · hauteur · densité · e ≤ masse max
            Constraint("masse", (("epaisseur", w * h * density),), "<=", Fraction(str(masse_max))),
        ),
        target=("epaisseur", Fraction(str(guess))),
        description="épaisseur standard la plus proche de l'estimation, respectant les règles",
    )


def validate(session: Session, kb: KnowledgeBase, report: Report, masse_max: float) -> None:
    t = kb.value("plaque.epaisseur")
    with report.tracer.span("validator.check", regles="Plaque.verifier"):
        verdict = session.eval(f"Plaque.verifier {masse_max!r} (Plaque.plaque_de demande {t!r})")
        mass = session.eval(f"Plaque.masse (Plaque.plaque_de demande {t!r})").value
    premises = ["plaque.largeur", "plaque.hauteur", "plaque.epaisseur"]
    kb.derive("plaque.masse_kg", round(mass, 4), "Plaque.masse (règle du domaine)", premises)
    value: Variant = verdict.value
    report.verdict = "Valide" if value.tag == "Valide" else "Invalide"
    kb.derive(
        "plaque.valide", report.verdict == "Valide", f"Plaque.verifier → {show(value)}", premises
    )
    report.step("validation", f"{show(value)} (masse {mass:.3f} kg ≤ {masse_max} kg requis)")


def revise(
    session: Session, kb: KnowledgeBase, report: Report, masse_max: float, mesure: float
) -> None:
    with report.tracer.span("observer.verify", grandeur="épaisseur"):
        estimate_sources = [
            s.id
            for key in ("plaque.epaisseur_estimee",)
            if key in kb.facts
            for s in kb.sources_of(key)
        ]
        kb.observe("plaque.epaisseur_mesuree", mesure, "mesure au pied à coulisse (capteur simulé)")
        invalidated: list[str] = []
        for source in estimate_sources:
            invalidated += kb.retract_source(source, "remplacée par une mesure")
        kb.derive("plaque.epaisseur", mesure, "mesure directe", ["plaque.epaisseur_mesuree"])
    report.revision = invalidated
    report.step("révision", f"mesure {mesure} mm ; invalidés : {', '.join(invalidated) or 'aucun'}")
    validate(session, kb, report, masse_max)


def export_payload(kb: KnowledgeBase, fmt: str) -> dict[str, Any]:
    return {
        "command_id": f"export-{fmt}",
        "part": {
            "name": "plaque",
            "width_mm": kb.value("plaque.largeur"),
            "height_mm": kb.value("plaque.hauteur"),
            "thickness_mm": kb.value("plaque.epaisseur"),
        },
        "format": fmt,
        "path": f"plaque.{fmt}",
    }


def _trace_transition(tracer: Tracer):
    def record(command, state: str, detail: str) -> None:
        with tracer.span(f"command.{state.lower()}", command=command.id, detail=detail):
            pass

    return record


# ------------------------------------------------------------------ rendu


def render(report: Report) -> str:
    kb = report.kb
    out = [f"Demande : « {report.request} »", ""]
    out.append("Programme Hypomnesis (typé par le vérificateur) :")
    out += ["  " + line for line in report.transcription.program.strip().splitlines()]
    out += ["", "Étapes :"]
    out += [f"  {i}. {name:<14} {detail}" for i, (name, detail) in enumerate(report.steps, 1)]
    if report.explanation_before:
        out += ["", "Avant la mesure, la validité reposait sur une estimation :"]
        out += ["  " + line for line in report.explanation_before]
    if "plaque.valide" in kb.facts:
        title = "Après la mesure" if report.explanation_before else "Pourquoi cette conclusion"
        out += ["", f"{title} (provenance) :"]
        out += ["  " + line for line in kb.explain("plaque.valide")]
    if report.commands:
        out += ["", "Commandes :"]
        for o in report.commands:
            out.append(f"  {o.command.id} : " + " → ".join(s for s, _ in o.states))
            if o.state == "Rejected":
                out.append(f"     motif : {o.states[-1][1]}")
            if o.result:
                out.append(f"     résultat : {o.result}")
    out += ["", "Traces :"] + ["  " + line for line in report.tracer.tree()]
    return "\n".join(out)
