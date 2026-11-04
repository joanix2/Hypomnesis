"""Reproducible host assembly; all mechanics rules remain in the M2 language."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import TypeVar

from hypomnesis.backends import z3_solver
from hypomnesis.backends.sklearn import RegressionEstimator
from hypomnesis.capabilities.result import Result
from hypomnesis.contracts.codec import TypeCodec
from hypomnesis.effects.dispatcher import Command, Dispatcher
from hypomnesis.effects.transports import FileTransport
from hypomnesis.engine.bridge import solution_value, to_json, to_problem
from hypomnesis.engine.language import load_language
from hypomnesis.engine.procedure import trace_actuator
from hypomnesis.engine.validators import LanguageValidator
from hypomnesis.epistemics.knowledge import KnowledgeBase
from hypomnesis.epistemics.metavariables import propose, resolve
from hypomnesis.language.errors import HypomnesisError
from hypomnesis.observability.trace import Tracer
from hypomnesis.runtime.values import RecordValue
from hypomnesis_codegen.hypotheses import capture_input
from hypomnesis_codegen.ollama import Reply
from hypomnesis_codegen.translation import translate

ROOT = Path(__file__).resolve().parents[2]
LANGUAGE = ROOT / "demo/languages/mecanique"
RESPONSE = ROOT / "demo/programs/mecanique/plaque_120x80.hyp"
REQUEST = (
    "Crée une plaque de 120 × 80 mm, estime son épaisseur, "
    "vérifie sa validité et exporte sa géométrie."
)
T = TypeVar("T")


class RecordedClient:
    """A fixed test response, not a network model or an inference measurement."""

    def __init__(self, response: str) -> None:
        self.response = response
        self.calls = 0

    def chat(
        self,
        model: str,
        messages: list[dict[str, str]],
        *,
        num_ctx: int = 16384,
        temperature: float = 0.0,
    ) -> Reply:
        self.calls += 1
        return Reply(self.response, 0.0, 0, 0.0)


def _require(result: Result[T]) -> T:
    if not result.ok or result.value is None:
        raise RuntimeError(
            "; ".join(f"{d.code}: {d.message}" for d in result.diagnostics)
            or "capability returned no value"
        )
    return result.value


def run_mvp(
    out_dir: Path,
    *,
    response: str | None = None,
    source_unit: str = "mm",
    permissions: frozenset[str] = frozenset({"actuator:geometry.export"}),
) -> dict[str, object]:
    out_dir.mkdir(parents=True, exist_ok=True)
    tracer, kb = Tracer(), KnowledgeBase()
    report: dict[str, object] = {"status": "failed", "steps": []}
    steps: list[dict[str, object]] = []
    report["steps"] = steps

    def completed(number: int, span: str, evidence: str) -> None:
        steps.append({"number": number, "span": span, "evidence": evidence})

    try:
        with tracer.span("hypomnesis.run", scenario="mvp-mechanics", model="recorded-fixture"):
            language = load_language(LANGUAGE)
            client = RecordedClient(RESPONSE.read_text() if response is None else response)
            translation = translate(
                client,
                "recorded-fixture",
                language,
                REQUEST,
                examples=[],
                max_repairs=0,
                tracer=tracer,
            )
            if not translation.accepted:
                raise RuntimeError(translation.attempts[-1].error)
            kb.hypothesis(
                "transcription.program", translation.program, "recorded test fixture", 0.0
            )
            completed(1, "llm.transcribe", "transcription.program")
            kb.derive("compilation.typed", True, "static compiler check", ["transcription.program"])
            completed(2, "language.typecheck", "compilation.typed")

            with tracer.span("dimensions.normalize", source_unit=source_unit, target_unit="mm"):
                candidate = load_language(LANGUAGE)
                candidate.load_program(translation.program)
                codec = TypeCodec(language.session.checker, "Plaque.demande")
                demand = codec.decode(codec.encode(candidate.session.value("demande")))
                inputs = capture_input(
                    language.session.checker, "Plaque.demande", demand, kb, key="demande"
                )
                report["input"] = inputs.report()
                if len(inputs.missing) != 1 or inputs.missing[0].id != "demande.epaisseur":
                    raise ValueError("the requested thickness must remain absent, not invented")
                hole = inputs.missing[0]
                normalized = language.function("Plaque.normaliser")(demand, source_unit)
                if normalized.tag != "Some":
                    raise ValueError(f"unsupported source unit: {source_unit}")
                demand = normalized.arg
                normalized_data = codec.encode(demand)
                kb.derive(
                    "normalisee",
                    normalized_data,
                    "Plaque.normaliser to mm",
                    ["compilation.typed", *(f.key for f in inputs.facts)],
                )
            completed(3, "dimensions.normalize", "normalisee")

            with tracer.span("estimator.predict"):
                spec = json.loads((LANGUAGE / "modeles/epaisseur-1.0.0.json").read_text())
                estimator = RegressionEstimator(**spec)
                features = {"petit_cote_mm": language.function("Plaque.petit_cote")(demand)}
                prediction = _require(estimator.estimate(features))
                fact = kb.estimate("epaisseur.estimation", prediction.value, prediction.origin, 0.6)
                hole = propose(hole, fact.value, kb.support(fact.key), fact.provenance)
                report["estimator"] = {
                    "model": prediction.model,
                    "version": prediction.version,
                    "validation_rmse": prediction.validation_rmse,
                    "features": features,
                }
            completed(4, "estimator.predict", "epaisseur.estimation")

            with tracer.span("solver.solve", solver=z3_solver.NAME):
                problem = to_problem(language.function("Plaque.probleme_type")(demand, fact.value))
                solution = z3_solver.solve(problem)
                checked = solution_value(problem, solution)
                report["solution"] = TypeCodec(language.session.checker, "Problem.solution").encode(
                    checked
                )
                if solution.status != "sat":
                    raise RuntimeError(f"solver {solution.status}: {solution.reason}")
                thickness = float(solution.assignment["epaisseur"])
                solved = kb.derive(
                    "demande.epaisseur",
                    thickness,
                    "independently checked Z3 model",
                    ["normalisee", "epaisseur.estimation"],
                )
                hole = resolve(
                    propose(hole, solved.value, kb.support(solved.key), solved.provenance), choice=1
                )
                report["metavariable"] = {
                    "id": hole.id,
                    "state": hole.state,
                    "value": hole.value,
                    "grade": hole.grade.name if hole.grade is not None else None,
                    "coherence": hole.coherence,
                    "proposals": [
                        {"value": p.fact.value, "grade": p.grade.name} for p in hole.proposals
                    ],
                    "selection": 1,
                }
            completed(5, "solver.solve", "demande.epaisseur")

            with tracer.span("validator.validate"):
                validator = LanguageValidator(
                    language.session, "Plaque.verifier_proposition", "Plaque.proposition"
                )
                proposal = RecordValue(
                    "Plaque.proposition", (("demande", demand), ("epaisseur_proposee", thickness))
                )
                validated = validator.validate(proposal)
                _require(validated)
                if validated.certificate is None:
                    raise RuntimeError("validator returned no replayable certificate")
                report["validation"] = dict(validated.certificate.body)
                kb.derive(
                    "demande.valide",
                    True,
                    "Plaque.verifier_proposition",
                    ["normalisee", "demande.epaisseur"],
                )
            completed(6, "validator.validate", "demande.valide")

            with tracer.span("command.dispatch"):
                payload = to_json(
                    language.function("Plaque.commande_export")(demand, thickness, "json")
                )
                kb.derive("commande.export", payload, "Plaque.commande_export", ["demande.valide"])
                action = language.adapters.get("actuator", "geometry.export")(out_dir)
                dispatcher = Dispatcher(language.schemas, set(permissions), mode="production")
                dispatcher.register(trace_actuator(action, tracer))
                command = dispatcher.command(action.id, payload)
                transport = FileTransport(
                    out_dir / "scenarios" / f"{tracer.trace_id}.jsonl", language.schemas
                )
                envelope = {
                    "message_id": "export-request",
                    "schema_id": action.command_schema,
                    "schema_version": "1.0.0",
                    "timestamp": datetime.now(UTC).isoformat(),
                    "correlation_id": tracer.trace_id,
                    "payload": command.payload,
                }
                transport.send(envelope)
                received = transport.receive()
                if received is None:
                    raise RuntimeError("export command was not delivered")
                outcome = dispatcher.dispatch(Command(command.id, action.id, received["payload"]))
                report["commands"] = [
                    {
                        "id": command.id,
                        "state": outcome.state,
                        "states": [[state, detail] for state, detail in outcome.states],
                        "checks": [asdict(c) for c in outcome.checks],
                        "result": outcome.result,
                    }
                ]
                if outcome.state != "Completed" or outcome.result is None:
                    raise RuntimeError(f"export did not complete: {outcome.state}")
                transport.send(
                    {
                        **envelope,
                        "message_id": "export-response",
                        "schema_id": action.result_schema,
                        "payload": outcome.result,
                    }
                )
                reply = transport.receive()
                if reply is None:
                    raise RuntimeError("export response was not delivered")
                kb.observe("export.result", reply["payload"], "validated software export response")
                report["transport"] = str(transport.path)
            completed(7, "command.dispatch", "commande.export")
            completed(8, "actuator.execute", "export.result")

            with tracer.span("result.encode"):
                result = {
                    "thickness_mm": hole.value,
                    "geometry": payload["part"],
                    "normalized_request": normalized_data,
                    "export": outcome.result,
                    "support": kb.support("demande.valide").name,
                }
                encoded_result = json.dumps(result, ensure_ascii=False, allow_nan=False)
                kb.derive(
                    "result.json",
                    encoded_result,
                    "JSON encoding",
                    ["commande.export", "export.result"],
                )
                report["result"] = json.loads(encoded_result)
            completed(9, "result.encode", "result.json")

            with tracer.span("metrics.record"):
                report["metrics"] = {
                    "model_mode": "recorded-fixture",
                    "model_calls": client.calls,
                    "tokens_measured": False,
                    "commands": len(dispatcher.history),
                    "solver_ms": solution.duration_ms,
                    "estimator_validation_rmse": prediction.validation_rmse,
                }
            completed(10, "metrics.record", "metrics")
            report["status"] = "completed"
    except (ValueError, RuntimeError, HypomnesisError, OSError) as exc:
        report["error"] = str(exc)
        raise
    finally:
        report["trace"] = tracer.export()
        report["provenance_graph"] = kb.provenance_graph()
        report["knowledge"] = {
            key: {"value": kb.value(key), "support": kb.support(key).name} for key in kb.facts
        }
        report["journal"] = [
            {"seq": event.seq, "kind": event.kind, "key": event.key, "detail": event.detail}
            for event in kb.journal
        ]
        (out_dir / "rapport_mvp.json").write_text(
            json.dumps(report, ensure_ascii=False, allow_nan=False, indent=2), encoding="utf-8"
        )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "demo/sortie/mvp-mecanique")
    args = parser.parse_args()
    report = run_mvp(args.output)
    print(json.dumps(report["result"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
