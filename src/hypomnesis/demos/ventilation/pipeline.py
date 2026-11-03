"""Démonstrateur MVP secondaire (§16.3) : capteur, règle, actionneur, rétroaction.

Un capteur simulé envoie une température dans une enveloppe JSON validée (§9.6).
La règle du domaine (`domaine.hyp`, pure) décide une commande de ventilateur ;
seul le dispatcher l'exécute (contrat, permission). L'hypothèse « le ventilateur
fonctionne » est explicite : l'effet attendu en dépend. Un second relevé confirme
l'effet, ou le réfute — alors l'hypothèse est retirée, ce qui invalide l'effet
attendu, et une panne est conclue à partir des seules observations. La boucle
est bornée (§11).
"""

from __future__ import annotations

import itertools
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from importlib.resources import files
from typing import Any

from hypomnesis.contracts.registry import SchemaRegistry
from hypomnesis.effects.dispatcher import Actuator, Dispatcher, Outcome, Payload
from hypomnesis.epistemics.knowledge import KnowledgeBase
from hypomnesis.observability.trace import Tracer
from hypomnesis.runtime.values import show
from hypomnesis.session import Session

DOMAIN = files("hypomnesis.demos.ventilation")
READING = "https://schemas.example.org/hypomnesis/temperature.reading/1.0.0"
FAN_SET = "https://schemas.example.org/hypomnesis/fan.set/1.0.0"
FAN_RESULT = "https://schemas.example.org/hypomnesis/fan.set.result/1.0.0"
FAN_PERMISSION = "actuator:fan.set"


@dataclass
class Room:
    """Pièce simulée : le ventilateur refroidit, sauf s'il est en panne."""

    celsius: float
    broken: bool = False
    speed: int = 0
    _ids: Any = field(default_factory=lambda: itertools.count(1), repr=False)

    def message(self) -> dict[str, Any]:
        """Relevé du capteur, dans l'enveloppe de message standard."""
        return {
            "message_id": f"msg-{next(self._ids)}",
            "schema_id": READING,
            "schema_version": "1.0.0",
            "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "correlation_id": "ventilation",
            "payload": {"sensor_id": "thermo-1", "celsius": round(self.celsius, 2)},
        }

    def tick(self) -> None:
        self.celsius += 0.2 if self.broken or self.speed == 0 else -self.speed / 25


def registry() -> SchemaRegistry:
    reg = SchemaRegistry.with_builtin_schemas()
    for name in (
        "temperature.reading-1.0.0.json",
        "fan.set-1.0.0.json",
        "fan.set.result-1.0.0.json",
    ):
        reg.add(json.loads(DOMAIN.joinpath(name).read_text(encoding="utf-8")))
    return reg


def fan(room: Room) -> Actuator:
    def execute(payload: Payload) -> dict[str, Any]:
        room.speed = payload["speed_percent"]
        return {"status": "accepted", "speed_percent": room.speed}

    return Actuator("fan.set", FAN_PERMISSION, FAN_SET, FAN_RESULT, execute)


@dataclass
class Report:
    kb: KnowledgeBase
    tracer: Tracer
    steps: list[str] = field(default_factory=list)
    commands: list[Outcome] = field(default_factory=list)
    conclusion: str = ""


def run(
    temperature: float = 31.0,
    *,
    broken: bool = False,
    budget: int = 5,
    room: Room | None = None,
) -> Report:
    room = room or Room(temperature, broken)
    kb, tracer = KnowledgeBase(), Tracer()
    report = Report(kb, tracer)
    reg = registry()
    session = Session()
    session.load(DOMAIN.joinpath("domaine.hyp").read_text(encoding="utf-8"))
    dispatcher = Dispatcher(reg, {FAN_PERMISSION}, mode="production")
    dispatcher.register(fan(room))

    def read(i: int) -> str:
        with tracer.span("observer.read", capteur="thermo-1"):
            payload = reg.validate_message(room.message())  # enveloppe puis contenu
        key = f"temperature.t{i}"
        kb.observe(key, payload["celsius"], f"capteur thermo-1 (relevé {i})")
        return key

    with tracer.span("hypomnesis.run", domaine="ventilation"):
        # « Le ventilateur fonctionne » : une hypothèse, pas un fait.
        kb.hypothesis("ventilateur.fonctionne", True, "fonctionnement nominal supposé", 0.9)
        hypothesis = kb.source_id("ventilateur.fonctionne")
        current = read(0)
        for i in range(1, budget + 1):
            t = kb.value(current)
            with tracer.span("knowledge.resolve", regle="Ventilation.decider"):
                decision = session.eval(f"Ventilation.decider {t!r}").value
            if decision.tag == "Arret":
                report.steps.append(f"{t} °C ≤ seuil : aucune action")
                report.conclusion = "température sous le seuil"
                break
            speed = decision.arg
            kb.derive(f"commande.c{i}", show(decision), "Ventilation.decider", [current])
            kb.derive(
                f"effet_attendu.c{i}",
                "baisse de température",
                "effet d'une commande si le ventilateur fonctionne",
                [f"commande.c{i}", "ventilateur.fonctionne"],
            )
            with tracer.span("actuator.execute", actionneur="fan.set", vitesse=speed):
                cmd = dispatcher.command("fan.set", {"fan_id": "fan-1", "speed_percent": speed})
                outcome = dispatcher.dispatch(cmd)
            report.commands.append(outcome)
            room.tick()
            after = read(i)
            t_after = kb.value(after)
            with tracer.span("observer.verify", regle="Ventilation.effet_confirme"):
                confirmed = session.eval(f"Ventilation.effet_confirme {t!r} {t_after!r}").value
            if confirmed:
                kb.derive(
                    f"effet_confirme.c{i}", True, "Ventilation.effet_confirme", [current, after]
                )
                report.steps.append(f"{t} °C → {show(decision)} → {t_after} °C : effet confirmé")
                current = after
                continue
            # Réfutation : l'hypothèse tombe, et avec elle l'effet attendu.
            invalidated = kb.retract_source(hypothesis, "effet attendu non observé")
            kb.derive(
                "ventilateur.en_panne",
                True,
                "commande acceptée mais température non abaissée",
                [f"commande.c{i}", current, after],
            )
            report.steps.append(
                f"{t} °C → {show(decision)} → {t_after} °C : effet réfuté ; "
                f"invalidés : {', '.join(invalidated)}"
            )
            report.conclusion = "panne du ventilateur (alerte)"
            break
        else:
            report.conclusion = f"budget de {budget} itérations épuisé"
        if not report.conclusion:
            report.conclusion = "température ramenée sous le seuil"
    return report


def render(report: Report) -> str:
    kb = report.kb
    out = ["Boucle capteur → règle → actionneur → capteur :"]
    out += [f"  {i}. {s}" for i, s in enumerate(report.steps, 1)]
    out += ["", f"Conclusion : {report.conclusion}"]
    for key in (
        "ventilateur.en_panne",
        *[k for k in kb.facts if k.startswith("effet_confirme")][-1:],
    ):
        if key in kb.facts:
            out += ["", "Provenance :"] + ["  " + line for line in kb.explain(key)]
    out += ["", "Hypothèses :"]
    state = "retirée" if "ventilateur.fonctionne" not in kb.facts else "maintenue"
    out.append(f"  ventilateur.fonctionne : {state}")
    out += ["", "Commandes :"]
    out += [f"  {o.command.id} {dict(o.command.payload)} : {o.state}" for o in report.commands]
    out += ["", "Traces :"] + ["  " + line for line in report.tracer.tree()]
    return "\n".join(out)
