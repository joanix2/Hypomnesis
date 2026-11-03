"""Generic procedure « constrained design » (M3), configured by an M2 manifest.

    request (M1 record) ─ known fields ──▶ observed facts
                        └ None fields ───▶ unknowns ─▶ estimators (M2 functions)
                                                       ─▶ constraint problem (M2 function
                                                          returning Problem.problem)
                                                       ─▶ solver, solution re-checked
    validator (M2 function)  ─▶ verdict      derived values (M2 functions)
    actions (M2 command builders + adapters) ─▶ dispatcher (contract, permission, mode)
    observations ─▶ revision of everything that depended on an estimate

Nothing here names a domain: fields come from the M1 request, functions and
adapters from the M2 manifest. Each conclusion enters the knowledge base with
its provenance, so the report explains it.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from hypomnesis.backends import z3_solver
from hypomnesis.effects.dispatcher import Dispatcher, Outcome
from hypomnesis.engine.bridge import to_json, to_problem
from hypomnesis.engine.language import Language, LanguageError
from hypomnesis.epistemics.knowledge import KnowledgeBase
from hypomnesis.observability.trace import Tracer
from hypomnesis.runtime.values import RecordValue, Value, Variant, iter_list


@dataclass
class DesignReport:
    language: str
    program: str
    kb: KnowledgeBase
    tracer: Tracer
    steps: list[tuple[str, str]] = field(default_factory=list)
    commands: list[Outcome] = field(default_factory=list)
    verdict: str = ""
    revision: list[str] = field(default_factory=list)
    explanation_before: list[str] = field(default_factory=list)
    validity_key: str = ""

    def step(self, name: str, detail: str) -> None:
        self.steps.append((name, detail))

    def to_json(self) -> dict[str, Any]:
        kb = self.kb
        return {
            "language": self.language,
            "program": self.program,
            "steps": [{"step": s, "detail": d} for s, d in self.steps],
            "verdict": self.verdict,
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
            "revision": self.revision,
            "explanation_before_revision": self.explanation_before,
            "journal": [
                {"seq": e.seq, "kind": e.kind, "key": e.key, "detail": e.detail} for e in kb.journal
            ],
            "trace": self.tracer.export(),
        }


def _plain(value: Value) -> Any:
    return to_json(value)


def run_design(
    language: Language,
    program: str,
    *,
    estimator: str | None = None,
    mode: str = "dry-run",
    out_dir: Path = Path("sortie"),
    permissions: frozenset[str] | None = None,
    observations: dict[str, float] | None = None,
) -> DesignReport:
    proc = language.procedure
    if proc["kind"] != "constrained-design":
        raise LanguageError(f"{language.name} n'utilise pas la procédure constrained-design")
    tracer, kb = Tracer(), KnowledgeBase()
    report = DesignReport(language.name, program, kb, tracer)
    prefix = proc["request"]
    report.validity_key = f"{prefix}.valide"

    with tracer.span("hypomnesis.run", langage=language.name, mode=mode):
        with tracer.span("language.typecheck"):
            language.load_program(program)
        request = language.session.value(prefix)
        if not isinstance(request, RecordValue):
            raise LanguageError(f"`{prefix}` doit être un record")
        report.step("programme", f"{language.session.type_of(prefix)} (langage {language.name})")

        # Connu / inconnu
        unknown: list[str] = []
        for name, value in request.fields:
            key = f"{prefix}.{name}"
            if isinstance(value, Variant) and value.tag == "None":
                kb.unknown(key, "non précisé dans le programme")
                unknown.append(name)
            else:
                plain = _plain(
                    value.arg if isinstance(value, Variant) and value.tag == "Some" else value
                )
                kb.observe(key, plain, "programme M1")
        known = len(request.fields) - len(unknown)
        report.step(
            "connaissances", f"connus : {known}, inconnus : {', '.join(unknown) or 'aucun'}"
        )

        # Champs estimables (manifeste) : les fonctions du langage reçoivent la demande
        # puis la valeur de chacun d'eux, connue, estimée ou résolue, dans cet ordre.
        values: dict[str, float] = {}
        for name in proc["estimators"]:  # ordre du manifeste, complété ci-dessous
            known_value = name not in unknown
            values[name] = float(kb.value(f"{prefix}.{name}")) if known_value else float("nan")
        for name in unknown:
            choices = proc["estimators"].get(name)
            if not choices:
                raise LanguageError(f"aucun estimateur déclaré pour {name}")
            spec = (
                next((e for e in choices if e["id"] == estimator), choices[0])
                if estimator
                else choices[0]
            )
            with tracer.span("estimator.predict", plugin=spec["id"], version=spec["version"]):
                guess = float(language.function(spec["function"])(request))
            origin = f"estimateur {spec['id']} v{spec['version']} ({spec['function']})"
            kb.estimate(f"{prefix}.{name}.estimation", guess, origin, spec["confidence"])
            report.step(
                "estimation", f"{name} ≈ {guess} — {origin}, confiance {spec['confidence']}"
            )
            values[name] = guess
        if unknown:
            problem = to_problem(language.function(proc["problem"])(request, *values.values()))
            with tracer.span(
                "solver.solve", solver=z3_solver.NAME, contraintes=len(problem.constraints)
            ) as span:
                solution = z3_solver.solve(problem)
                span.attributes["status"] = solution.status
            if solution.status != "sat":
                report.step(
                    "résolution",
                    f"aucune solution ne satisfait les contraintes du langage ({solution.status})",
                )
                report.verdict = "Impossible"
                return _finish(report, out_dir)
            if solution.violations:
                raise RuntimeError(
                    f"solution du solveur refusée par la vérification : {solution.violations}"
                )
            premises = [f"{prefix}.{n}" for n, v in request.fields if n not in unknown]
            for name in unknown:
                values[name] = float(solution.assignment[name])
                kb.derive(
                    f"{prefix}.{name}",
                    values[name],
                    f"résolu par {solution.solver} ({proc['problem']}), solution revérifiée",
                    [*premises, f"{prefix}.{name}.estimation"],
                )
            report.step(
                "résolution",
                ", ".join(f"{n} = {values[n]}" for n in unknown)
                + " (contraintes satisfaites, vérifié)",
            )

        _validate(language, report, request, values)
        if report.verdict == "Valide":
            _act(language, report, request, values, mode, out_dir, permissions)

        if observations:
            report.explanation_before = (
                kb.explain(report.validity_key) if report.validity_key in kb.facts else []
            )
            _revise(language, report, request, values, observations)
    return _finish(report, out_dir)


def _premises(report: DesignReport, request: RecordValue) -> list[str]:
    prefix = report.validity_key.rsplit(".", 1)[0]
    return [f"{prefix}.{name}" for name, _ in request.fields]


def _validate(
    language: Language, report: DesignReport, request: RecordValue, values: dict[str, float]
) -> None:
    proc, kb, prefix = language.procedure, report.kb, report.validity_key.rsplit(".", 1)[0]
    args = [request, *values.values()]
    premises = [p for p in _premises(report, request) if p in kb.facts]
    for name, function in proc.get("derived", {}).items():
        value = _plain(language.function(function)(*args))
        kb.derive(f"{prefix}.{name}", value, function, premises)
    with report.tracer.span("validator.check", regles=proc["validator"]):
        errors = [str(e) for e in iter_list(language.function(proc["validator"])(*args))]
    report.verdict = "Valide" if not errors else "Invalide"
    kb.derive(
        report.validity_key,
        not errors,
        f"{proc['validator']} → {errors or 'aucune violation'}",
        premises,
    )
    detail = report.verdict + (f" : {'; '.join(errors)}" if errors else "")
    report.step("validation", detail)


def _act(language, report, request, values, mode, out_dir, permissions) -> None:
    actions = language.procedure.get("actions", [])
    if not actions:
        return
    default_permissions = {f"actuator:{a['actuator']}" for a in actions}
    dispatcher = Dispatcher(
        language.schemas,
        default_permissions if permissions is None else set(permissions),
        mode,
        on_transition=_trace_transition(report.tracer),
    )
    for action in actions:
        dispatcher.register(language.adapter(action["adapter"])(out_dir))
        build = language.function(action["command"])
        for variant in action.get("variants") or [None]:
            args = [request, *values.values()] + ([variant] if variant is not None else [])
            payload = to_json(build(*args))
            with report.tracer.span(
                "actuator.execute", actionneur=action["actuator"], variante=variant
            ):
                outcome = dispatcher.dispatch(dispatcher.command(action["actuator"], payload))
            report.commands.append(outcome)
    report.step("actions", ", ".join(f"{o.command.id} {o.state}" for o in report.commands))


def _trace_transition(tracer: Tracer):
    def record(command, state: str, detail: str) -> None:
        with tracer.span(f"command.{state.lower()}", command=command.id, detail=detail):
            pass

    return record


def _revise(language, report, request, values, observations) -> None:
    kb, prefix = report.kb, report.validity_key.rsplit(".", 1)[0]
    invalidated: list[str] = []
    with report.tracer.span("observer.verify", grandeurs=",".join(observations)):
        for name, measured in observations.items():
            estimate = f"{prefix}.{name}.estimation"
            sources = [s.id for s in kb.sources_of(estimate)] if estimate in kb.facts else []
            kb.observe(f"{prefix}.{name}.mesure", measured, "observation ultérieure (mesure)")
            for source in sources:
                invalidated += kb.retract_source(source, "remplacée par une mesure")
            kb.derive(f"{prefix}.{name}", measured, "mesure directe", [f"{prefix}.{name}.mesure"])
            values[name] = measured
    report.revision = invalidated
    report.step("révision", f"{observations} ; invalidés : {', '.join(invalidated) or 'aucun'}")
    _validate(language, report, request, values)


def _finish(report: DesignReport, out_dir: Path) -> DesignReport:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "rapport.json").write_text(
        json.dumps(report.to_json(), indent=2, ensure_ascii=False, default=str), encoding="utf-8"
    )
    return report


def render(report: DesignReport) -> str:
    kb = report.kb
    out = [f"Langage {report.language} — programme M1 :"]
    out += ["  " + line for line in report.program.strip().splitlines()]
    out += ["", "Étapes :"]
    out += [f"  {i}. {name:<14} {detail}" for i, (name, detail) in enumerate(report.steps, 1)]
    if report.explanation_before:
        out += ["", "Avant l'observation, la validité reposait sur une estimation :"]
        out += ["  " + line for line in report.explanation_before]
    if report.validity_key in kb.facts:
        title = "Après l'observation" if report.explanation_before else "Pourquoi cette conclusion"
        out += ["", f"{title} (provenance) :"] + [
            "  " + line for line in kb.explain(report.validity_key)
        ]
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
