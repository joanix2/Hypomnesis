from pathlib import Path

import pytest

from hypomnesis.cli import main
from hypomnesis.language.errors import TypeCheckError
from hypomnesis.session import Session

EXAMPLES = Path(__file__).resolve().parents[2] / "demo" / "examples"
MECHANICS = [EXAMPLES / "mechanics" / "units.hyp", EXAMPLES / "mechanics" / "plate.hyp"]


def test_mechanics_example_runs():
    session = Session()
    for path in MECHANICS:
        session.load(path.read_text())
    assert session.eval("area_mm2").render() == "val it : float = 9600."
    assert session.eval("volume_mm3").render() == "val it : float option = Some 38400."
    assert session.type_of("Mechanics.area") == "Mechanics.plate -> Area.t"


def test_dimension_errors_are_caught_before_execution():
    session = Session()
    session.load(MECHANICS[0].read_text())
    with pytest.raises(TypeCheckError, match=r"Area\.t"):
        session.check(
            "let bad = Length.add (Length.mm 1.0) (Length.multiply (Length.mm 1.0) (Length.mm 2.0))"
        )


@pytest.mark.parametrize("path", sorted((EXAMPLES / "basics").glob("*.hyp")), ids=lambda p: p.name)
def test_basic_examples_run(path, capsys):
    assert main(["run", str(path)]) == 0
    assert "val" in capsys.readouterr().out


def test_cli_reports_errors(tmp_path, capsys):
    bad = tmp_path / "bad.hyp"
    bad.write_text("let x = 1 +. 2.0")
    assert main(["check", str(bad)]) == 1
    err = capsys.readouterr().err
    assert "bad.hyp:1:9: type error" in err and "^" in err
