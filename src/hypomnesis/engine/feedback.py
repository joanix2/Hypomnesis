"""Generic procedure « feedback loop » (M3), configured by an M2 manifest.

environment (M2 adapter) ─ sensor message ─▶ envelope + contract ─▶ observed fact
decide (M2 function)     ─ Some x ─▶ command (M2 builder) ─▶ dispatcher ─▶ actuator
                         ─ None   ─▶ stop
expected effect          ─ depends on an explicit hypothesis (M2 manifest)
verify (M2 function)     ─ true  ─▶ effect confirmed by observations; loop again
                         ─ false ─▶ hypothesis withdrawn, expected effect falls with it,
                                    refutation concluded from observations alone
bounded by the `budget` field of the M1 setup (§11).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from hypomnesis.effects.dispatcher import Dispatcher, Outcome
from hypomnesis.engine.bridge import option, to_json
from hypomnesis.engine.language import Language, LanguageError
from hypomnesis.epistemics.knowledge import KnowledgeBase
from hypomnesis.observability.trace import Tracer
from hypomnesis.runtime.values import RecordValue


@dataclass
class FeedbackReport:
    language: str
    kb: KnowledgeBase
    tracer: Tracer
    hypothesis: str
    steps: list[str] = field(default_factory=list)
    commands: list[Outcome] = field(default_factory=list)
    conclusion: str = ""


def run_feedback(
    language: Language, program: str, *, environment: dict[str, Any] | None = None
) -> FeedbackReport:
    proc = language.procedure
    if proc["kind"] != "feedback-loop":
        raise LanguageError(f"{language.name} n'utilise pas la procédure feedback-loop")
    kb, tracer = KnowledgeBase(), Tracer()
    report = FeedbackReport(language.name, kb, tracer, proc["hypothesis"])
    with tracer.span("language.typecheck"):
        language.load_program(program)
    setup = language.session.value(proc["setup"])
    if not isinstance(setup, RecordValue):
        raise LanguageError(f"`{proc['setup']}` doit être un record")
    setup_json = to_json(setup)
    budget = int(setup_json.get("budget", 5))
    env = language.adapter(proc["environment"])(setup_json, environment or {})
    action = proc["actuator"]
    dispatcher = Dispatcher(language.schemas, {f"actuator:{action['actuator']}"}, "production")
    dispatcher.register(language.adapter(action["adapter"])(env))
    decide = language.function(proc["decide"])
    build = language.function(action["command"])
    verify = language.function(proc["verify"])

    def read(i: int) -> str:
        with tracer.span("observer.read"):
            payload = language.schemas.validate_message(env.message())
        if payload is None or proc["measure"] not in payload:
            raise LanguageError("relevé sans la grandeur mesurée")
        key = f"mesure.r{i}"
        kb.observe(key, payload[proc["measure"]], f"capteur (relevé {i})")
        return key

    with tracer.span("hypomnesis.run", langage=language.name):
        kb.hypothesis("hypothese", True, proc["hypothesis"], 0.9)
        hypothesis = kb.source_id("hypothese")
        current = read(0)
        for i in range(1, budget + 1):
            before = kb.value(current)
            with tracer.span("knowledge.resolve", regle=proc["decide"]):
                decision = option(decide(before))
            if decision is None:
                report.steps.append(f"{before} : aucune action ({proc['decide']})")
                report.conclusion = "aucune action nécessaire"
                break
            kb.derive(f"decision.c{i}", to_json(decision), proc["decide"], [current])
            kb.derive(
                f"effet_attendu.c{i}",
                True,
                "effet attendu de la décision, sous l'hypothèse",
                [f"decision.c{i}", "hypothese"],
            )
            with tracer.span("actuator.execute", actionneur=action["actuator"]):
                command = dispatcher.command(action["actuator"], to_json(build(decision)))
                outcome = dispatcher.dispatch(command)
            report.commands.append(outcome)
            env.tick()
            after = read(i)
            with tracer.span("observer.verify", regle=proc["verify"]):
                confirmed = verify(before, kb.value(after))
            if confirmed:
                kb.derive(f"effet_confirme.c{i}", True, proc["verify"], [current, after])
                report.steps.append(
                    f"{before} → {to_json(decision)} → {kb.value(after)} : effet confirmé"
                )
                current = after
                continue
            invalidated = kb.retract_source(hypothesis, "effet attendu non observé")
            kb.derive(
                "hypothese.refutee",
                True,
                "commande exécutée mais effet attendu non observé",
                [f"decision.c{i}", current, after],
            )
            report.steps.append(
                f"{before} → {to_json(decision)} → {kb.value(after)} : effet réfuté ; "
                f"invalidés : {', '.join(invalidated)}"
            )
            report.conclusion = f"hypothèse réfutée : « {proc['hypothesis']} » (alerte)"
            break
        else:
            report.conclusion = f"budget de {budget} itérations épuisé"
    return report


def render(report: FeedbackReport) -> str:
    kb = report.kb
    out = [f"Langage {report.language} — boucle capteur → décision → actionneur → capteur :"]
    out += [f"  {i}. {s}" for i, s in enumerate(report.steps, 1)]
    out += ["", f"Conclusion : {report.conclusion}"]
    confirmed = [k for k in kb.facts if k.startswith("effet_confirme")]
    for key in ("hypothese.refutee", *confirmed[-1:]):
        if key in kb.facts:
            out += ["", "Provenance :"] + ["  " + line for line in kb.explain(key)]
    state = "maintenue" if "hypothese" in kb.facts else "retirée"
    out += ["", f"Hypothèse « {report.hypothesis} » : {state}", "", "Commandes :"]
    out += [f"  {o.command.id} {dict(o.command.payload)} : {o.state}" for o in report.commands]
    out += ["", "Traces :"] + ["  " + line for line in report.tracer.tree()]
    return "\n".join(out)
