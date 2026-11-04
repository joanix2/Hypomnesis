"""Interpreter of effect values (M3): runs a procedure written in Hypomnesis.

An M1 (or M2) program describes a procedure as a value of type ``'a Effect.t``
(standard library). This interpreter is the only place where its operations
are performed:

* ``Observe`` reads a sensor declared by the language, validates the message
  (envelope, then contract) and records an **observed** fact — the only way a
  generated procedure gets that support;
* ``Act`` goes through the dispatcher: contract, permission, business
  constraints, mode (simulate, dry-run, production);
* ``Solve`` calls the solver and re-checks its solution;
* ``Record`` stores trusted host-program claims, or conservatively hypotheses
  in generated mode (premises must still exist);
* ``Retract`` withdraws the source of a fact and invalidates what depended on it;
* ``Note`` adds a line to the report.

Each step continues with the program's own continuation. The number of steps is
bounded (§11). Nothing here names a domain.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import Any

from hypomnesis.backends import z3_solver
from hypomnesis.effects.dispatcher import Actuator, Command, Dispatcher, Outcome, Payload
from hypomnesis.effects.permissions import PermissionPolicy
from hypomnesis.engine.bridge import BridgeError, solution_value, to_problem
from hypomnesis.engine.language import Language, LanguageError
from hypomnesis.epistemics.knowledge import KnowledgeBase
from hypomnesis.language.errors import EvaluationError
from hypomnesis.observability.trace import Tracer
from hypomnesis.runtime.json import data_to_json, json_to_data
from hypomnesis.runtime.natives import to_json_value
from hypomnesis.runtime.values import UNIT, Value, Variant, from_iterable, iter_list

Json = Any


def json_to_python(v: Variant) -> Json:
    """``Json.t`` → Python."""
    return json_to_data(v)


def python_to_json(x: Json) -> Variant:
    """Python → ``Json.t``."""
    return data_to_json(x)


def _some(v: Value) -> Variant:
    return Variant("Some", v, 1)


NONE = Variant("None", None, 0)


def trace_actuator(action: Actuator, tracer: Tracer) -> Actuator:
    """Trace actual execution, not simulation, permission checks or pure continuations."""

    def execute(payload: Payload) -> dict[str, Any]:
        with tracer.span("actuator.execute", actionneur=action.id):
            return action.execute(payload)

    return replace(action, execute=execute)


@dataclass
class ProcedureReport:
    language: str
    program: str
    kb: KnowledgeBase
    tracer: Tracer
    notes: list[str] = field(default_factory=list)
    commands: list[Outcome] = field(default_factory=list)
    result: Json = None
    steps: int = 0
    stopped: str = ""
    generated: bool = False

    def to_json(self) -> dict[str, Any]:
        kb = self.kb
        return {
            "language": self.language,
            "program": self.program,
            "generated": self.generated,
            "notes": self.notes,
            "result": self.result,
            "stopped": self.stopped,
            "knowledge": {
                key: {
                    "value": f.value,
                    "method": f.method,
                    "support": kb.support(key).label,
                    "confidence": round(kb.confidence(key), 3),
                }
                for key, f in kb.facts.items()
            },
            "provenance_graph": kb.provenance_graph(),
            "commands": [
                {
                    "id": o.command.id,
                    "states": o.states,
                    "result": o.result,
                    "checks": [asdict(check) for check in o.checks],
                }
                for o in self.commands
            ],
            "journal": [
                {"seq": e.seq, "kind": e.kind, "key": e.key, "detail": e.detail} for e in kb.journal
            ],
            "trace": self.tracer.export(),
        }


def run_procedure(
    language: Language,
    program: str,
    *,
    mode: str = "dry-run",
    out_dir: Path = Path("demo/sortie"),
    environment: dict[str, Any] | None = None,
    permissions: frozenset[str] | None = None,
    max_steps: int = 1000,
    policy: PermissionPolicy | None = None,
    approve: Callable[[Command], bool] | None = None,
    generated: bool = False,
) -> ProcedureReport:
    if type(generated) is not bool:
        raise ValueError("generated must be a boolean host decision")
    proc = language.procedure
    if proc["kind"] != "program":
        raise LanguageError(f"{language.name} n'utilise pas la procédure program")
    kb, tracer = KnowledgeBase(), Tracer()
    report = ProcedureReport(language.name, program, kb, tracer, generated=generated)
    with tracer.span("language.typecheck"):
        language.load_program(program)
    entry = proc["entry"]
    if not language.session.type_of(entry).endswith("Effect.t"):
        raise LanguageError(f"`{entry}` doit être une procédure (type … Effect.t)")

    adapters = language.adapters
    env = None
    if adapters.identifiers("environment"):
        env = adapters.get("environment")(environment or {}, out_dir)
    actuators = adapters.identifiers("actuator")
    granted = (
        {f"actuator:{identifier}" for identifier in actuators}
        if permissions is None
        else permissions
    )
    dispatcher = Dispatcher(language.schemas, set(granted), mode, policy=policy, approve=approve)
    for identifier in actuators:
        action = adapters.get("actuator", identifier)(env if env is not None else out_dir)
        if not isinstance(action, Actuator) or action.id != identifier:
            raise LanguageError(f"fabrique d'actionneur incompatible : {identifier}")
        dispatcher.register(trace_actuator(action, tracer))
    readings: dict[str, int] = {}

    def apply(callback: Value, arguments: list[Value]) -> Value:
        with tracer.span("procedure.resume", boundary="pure"):
            return language.session.interpreter.apply(callback, arguments)

    value: Value = language.session.value(entry)
    with tracer.span("hypomnesis.run", langage=language.name, mode=mode):
        while isinstance(value, Variant) and value.tag != "Done":
            report.steps += 1
            if report.steps > max_steps:
                report.stopped = f"budget de {max_steps} étapes épuisé"
                break
            op, arg = value.tag, value.arg
            if op == "Observe":
                sensor, k = arg
                sensors = adapters.identifiers("sensor")
                if sensor not in sensors:
                    raise LanguageError(
                        f"capteur non déclaré par le langage : {sensor}. "
                        f"Capteurs déclarés : {', '.join(sensors) or 'aucun'}."
                    )
                with tracer.span("observer.read", capteur=sensor):
                    payload = language.schemas.validate_message(
                        adapters.get("sensor", sensor)(env, sensor)
                    )
                readings[sensor] = readings.get(sensor, 0) + 1
                key = f"{sensor}#{readings[sensor]}"
                kb.observe(key, payload, f"capteur {sensor}")
                value = apply(k, [(key, python_to_json(payload))])
            elif op == "Act":
                actuator, command, k = arg
                with tracer.span("command.dispatch", actionneur=actuator, mode=mode):
                    outcome = dispatcher.dispatch(
                        dispatcher.command(actuator, json_to_python(command))
                    )
                report.commands.append(outcome)
                value = apply(
                    k, [python_to_json({"state": outcome.state, "result": outcome.result})]
                )
            elif op in ("Solve", "SolveTyped"):
                problem, k = arg
                p = to_problem(problem)
                with tracer.span(
                    "solver.solve", solver=z3_solver.NAME, contraintes=len(p.constraints)
                ):
                    solution = z3_solver.solve(p)
                try:
                    checked = solution_value(p, solution)
                except BridgeError as exc:
                    raise EvaluationError(f"solution refusée par la vérification : {exc}") from exc
                if op == "SolveTyped":
                    value = apply(k, [checked])
                    continue
                answer: Value = NONE
                if solution.status == "sat":
                    answer = _some(
                        from_iterable((n, float(x)) for n, x in solution.assignment.items())
                    )
                value = apply(k, [answer])
            elif op == "Record":
                key, payload, method, support, k = arg
                _record(kb, key, json_to_python(payload), method, support, generated=generated)
                value = apply(k, [UNIT])
            elif op == "Retract":
                key, why, k = arg
                if key not in kb.facts:
                    raise EvaluationError(
                        f"retrait d'un fait inconnu : {key}. Un fait ne se retire que s'il a "
                        "été enregistré plus tôt dans la même procédure ; cette étape suppose "
                        f"qu'une étape précédente l'a produit. {_known(kb)}"
                    )
                invalidated = kb.retract_source(kb.source_id(key), why)
                value = apply(k, [from_iterable(invalidated)])
            elif op == "Note":
                text, k = arg
                report.notes.append(text)
                value = apply(k, [UNIT])
            else:
                raise EvaluationError(f"opération d'effet inconnue : {op}")
        else:
            report.result = json_to_python(to_json_value(value.arg))
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "rapport.json").write_text(
        json.dumps(report.to_json(), indent=2, ensure_ascii=False, default=str), encoding="utf-8"
    )
    return report


def _known(kb: KnowledgeBase) -> str:
    return f"Faits connus à ce point : {', '.join(kb.facts) or 'aucun'}."


def _record(
    kb: KnowledgeBase,
    key: str,
    value: Json,
    method: str,
    support: Variant,
    *,
    generated: bool = False,
) -> None:
    premises = list(iter_list(support.arg)) if support.tag == "Derived" else []
    missing = [p for p in premises if p not in kb.facts]
    if missing:
        raise EvaluationError(
            f"prémisses inconnues pour {key} : {', '.join(missing)}. Ces faits n'ont pas "
            "été enregistrés avant cette étape : elle suppose qu'une étape précédente "
            f"(estimation, mesure, résolution) les a produits. {_known(kb)}"
        )
    if generated:
        if support.tag not in ("Given", "Estimated", "Assumed", "Derived"):
            raise EvaluationError(f"support inconnu : {support.tag}")
        kb.hypothesis(key, value, f"programme généré : {method}", 0.0)
        return
    if support.tag == "Given":
        kb.observe(key, value, f"programme M1 : {method}")
    elif support.tag == "Estimated":
        kb.estimate(key, value, method, support.arg)
    elif support.tag == "Assumed":
        kb.hypothesis(key, value, method, support.arg)
    elif support.tag == "Derived":
        kb.derive(key, value, method, premises)
    else:
        raise EvaluationError(f"support inconnu : {support.tag}")


def render(report: ProcedureReport) -> str:
    kb = report.kb
    out = [f"Langage {report.language} — procédure (effets interprétés par le moteur) :"]
    out += [f"  {i}. {note}" for i, note in enumerate(report.notes, 1)]
    out += ["", f"Résultat : {report.result}" + (f" ({report.stopped})" if report.stopped else "")]
    out += ["", "Connaissances :"]
    for key in kb.facts:
        out.append(
            f"  {key} = {kb.value(key)!r} [{kb.support(key).label}, {kb.confidence(key):.2f}]"
        )
    derived = [k for k, f in kb.facts.items() if f.premises]
    if derived:
        out += ["", f"Provenance de {derived[-1]} :"] + [
            "  " + line for line in kb.explain(derived[-1])
        ]
    if report.commands:
        out += ["", "Commandes :"]
        out += [
            f"  {o.command.id} : " + " → ".join(s for s, _ in o.states) for o in report.commands
        ]
    out += ["", "Traces :"] + ["  " + line for line in report.tracer.tree()]
    return "\n".join(out)
