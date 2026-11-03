"""Démonstrateur MVP secondaire « ventilation » (§16.3)."""

import pytest

from hypomnesis.cli import main
from hypomnesis.contracts.registry import ContractError
from hypomnesis.demos.ventilation.pipeline import Room, run
from hypomnesis.epistemics.provenance import Support


def test_working_fan_confirms_the_expected_effect():
    report = run(31.0)
    kb = report.kb
    assert report.conclusion == "température sous le seuil"
    assert kb.value("effet_confirme.c1") is True
    assert kb.support("effet_confirme.c1") is Support.OBSERVED
    assert "ventilateur.fonctionne" in kb.facts  # hypothèse maintenue
    assert [o.state for o in report.commands] == ["Completed"]


def test_broken_fan_refutes_the_hypothesis():
    report = run(31.0, broken=True)
    kb = report.kb
    assert report.conclusion == "panne du ventilateur (alerte)"
    assert "ventilateur.fonctionne" not in kb.facts
    assert "effet_attendu.c1" not in kb.facts  # dépendait de l'hypothèse
    assert kb.value("ventilateur.en_panne") is True
    assert kb.support("ventilateur.en_panne") is Support.OBSERVED  # conclu des seules observations


def test_expected_effect_depends_on_the_hypothesis():
    report = run(31.0, budget=1, room=Room(31.0, broken=False))
    assert report.kb.support("effet_attendu.c1") is Support.HYPOTHESIS


def test_no_action_below_threshold():
    report = run(25.0)
    assert report.conclusion == "température sous le seuil"
    assert not report.commands


def test_loop_is_bounded():
    room = Room(60.0)  # très chaud : il faut plusieurs commandes
    report = run(budget=1, room=room)
    assert len(report.commands) == 1
    assert "budget" in report.conclusion


def test_invalid_sensor_message_is_rejected():
    class BadSensor(Room):
        def message(self):
            message = super().message()
            message["payload"]["celsius"] = 999  # hors du contrat du capteur
            return message

    with pytest.raises(ContractError):
        run(room=BadSensor(31.0))


def test_cli(capsys):
    assert main(["demo", "ventilation", "--panne"]) == 0
    assert "panne du ventilateur" in capsys.readouterr().out
