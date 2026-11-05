"""Erased conflict reports agree with the generic proved detector."""

import json
import random
import subprocess
from pathlib import Path

from hypomnesis.epistemics.conflicts import ConflictChecker, Invariant
from hypomnesis.epistemics.knowledge import Fact, KnowledgeBase
from hypomnesis.epistemics.provenance import ONE, ZERO, Obs, One, Plus, Zero, obs
from hypomnesis.epistemics.serialization import _encode_provenance
from hypomnesis.runtime.values import RecordValue, Variant

FORMAL = Path(__file__).resolve().parents[2] / "formal"


def literal(value):
    return json.dumps(value, ensure_ascii=False)


def items(values):
    return "[" + ", ".join(values) + "]"


def provenance(term):
    if isinstance(term, Obs):
        return f"(.obs {literal(term.id)})"
    if isinstance(term, Zero):
        return ".zero"
    if isinstance(term, One):
        return ".one"
    operation = "plus" if isinstance(term, Plus) else "times"
    return f"(.{operation} {provenance(term.left)} {provenance(term.right)})"


def claims(base):
    return list(
        dict.fromkeys(
            [event.fact for event in base.journal if event.fact is not None]
            + list(base.facts.values())
        )
    )


def equivalence_classes(facts):
    representatives = []
    classes = {}
    for fact in facts:
        for i, representative in enumerate(representatives):
            if fact.same_value(representative):
                classes[fact] = i
                break
        else:
            classes[fact] = len(representatives)
            representatives.append(fact)
    for left in facts:
        for right in facts:
            assert (classes[left] == classes[right]) == left.same_value(right)
    return classes


def metadata(fact):
    return json.dumps({"snapshot": fact._value, "method": fact.method, "premises": fact.premises})


def wire_fact(fact, classes):
    return [fact.key, _encode_provenance(fact.provenance), classes[fact], metadata(fact)]


def fact_term(fact, classes):
    return (
        f"⟨{literal(fact.key)}, {provenance(fact.provenance)}, "
        f"({classes[fact]}, {literal(metadata(fact))})⟩"
    )


RUNNER = """
import Hypomnesis.Epistemics.Conflicts
import Lean
open Hypomnesis.Epistemics
open Hypomnesis.Epistemics.Revision
open Hypomnesis.Epistemics.Conflicts
set_option maxRecDepth 8192
set_option maxHeartbeats 8000000
abbrev Data := Nat × String
def theory : Theory Data := ⟨["x", "missing"], [
  ⟨"agree", ["x", "y"], fun fs => match fs with
    | [a, b] => a.data.1 == b.data.1
    | _ => false⟩,
  ⟨"chain", ["x", "y", "u"], fun fs => match fs with
    | [a, b, c] => a.data.1 == b.data.1 || b.data.1 == c.data.1
    | _ => false⟩]⟩
def provJson : Prov String → Lean.Json
  | .obs x => .mkObj [("op", .str "obs"), ("id", .str x)]
  | .zero => .mkObj [("op", .str "zero")]
  | .one => .mkObj [("op", .str "one")]
  | .plus a b => .mkObj [("op", .str "plus"), ("left", provJson a), ("right", provJson b)]
  | .times a b => .mkObj [("op", .str "times"), ("left", provJson a), ("right", provJson b)]
def factJson (f : Revision.Fact Data) : Lean.Json :=
  .arr #[.str f.key, provJson f.provenance, Lean.toJson f.data.1, .str f.data.2]
def reportJson : Report Data → Lean.Json
  | .functional key fs => .arr #[.str "functional", .str key, .arr (fs.map factJson).toArray]
  | .invariant rule fs => .arr #[.str "invariant", .str rule.name, .arr (fs.map factJson).toArray]
"""


def corpus():
    rng = random.Random(37)
    values = [
        None,
        (),
        True,
        False,
        0,
        1,
        10**30,
        0.0,
        -0.0,
        1.0,
        3.5,
        "a",
        "é",
        [1, True],
        [1, 1],
        (1, 2),
        {"a": 1, "b": 2},
        {"b": 2, "a": 1},
        RecordValue("R", (("a", 1),)),
        RecordValue("S", (("a", 1),)),
        Variant("Some", 1, 1),
        Variant("None", None, 0),
    ]
    result = []
    for i in range(48):
        base = KnowledgeBase()
        for j in range(3):
            value = values[(i + j) % len(values)] if i % 4 else values[i % len(values)]
            if j == 0:
                base.observe("x", value, f"sensor-{j}")
            elif j == 1:
                base.estimate("x", value, f"model-{j}", 0.5)
            else:
                base.hypothesis("x", value, f"assumption-{j}", 0.2)
        if i % 3:
            base.observe("y", rng.choice(values), "other")
        else:
            base.unknown("y", "missing")
        if i % 2:
            base.observe("u", rng.choice(values), "third")
        sources = list(base.sources)
        p = ZERO if i % 2 else ONE
        base.publish_fact(Fact("x", rng.choice(values), p, "constant proof"))
        base.publish_fact(
            Fact(
                "x",
                rng.choice(values),
                obs(sources[0]) + obs(sources[1]),
                "alternative",
            )
        )
        if i % 4 == 1:
            base.retract_source(sources[0], "withdraw first")
        if i % 5 == 0:
            base.retract_source(sources[1], "withdraw second")
        result.append(base)
    return result


def test_typed_reports_and_live_history_agree_with_the_lean_detector(lean_lake, tmp_path):
    built = subprocess.run(
        [lean_lake, "build", "Hypomnesis.Epistemics.Conflicts"],
        cwd=FORMAL,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert built.returncode == 0, built.stdout + built.stderr
    bases = corpus()
    assert len(bases) == 48
    for start in range(0, len(bases), 8):
        batch = bases[start : start + 8]
        projected = [(base, claims(base), equivalence_classes(claims(base))) for base in batch]
        source = tmp_path / "Samples.lean"
        source.write_text(
            RUNNER
            + "\ndef cases : List (List (Revision.Fact Data) × List String) := "
            + items(
                f"({items(fact_term(fact, classes) for fact in facts)}, "
                f"{items(literal(s) for s in sorted(base.retracted))})"
                for base, facts, classes in projected
            )
            + "\n#eval IO.println (Lean.Json.arr ((cases.map fun (fs, w) => "
            "Lean.Json.arr ((scan Prod.fst theory fs w).map reportJson).toArray)"
            ".toArray)).compress\n",
            encoding="utf-8",
        )
        ran = subprocess.run(
            [lean_lake, "env", "lean", f"--root={tmp_path}", str(source)],
            cwd=FORMAL,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        assert ran.returncode == 0, ran.stdout + ran.stderr
        actual = json.loads(ran.stdout)
        assert len(actual) == len(projected)
        for (base, _, classes), reports in zip(projected, actual, strict=True):
            for policy in ("report", "best-support"):
                checker = ConflictChecker(
                    ("x", "missing"),
                    (
                        Invariant("agree", ("x", "y"), lambda fs: fs[0].same_value(fs[1])),
                        Invariant(
                            "chain",
                            ("x", "y", "u"),
                            lambda fs: fs[0].same_value(fs[1]) or fs[1].same_value(fs[2]),
                        ),
                    ),
                    policy=policy,
                )
                expected = [
                    [report.kind, report.rule, [wire_fact(fact, classes) for fact in report.facts]]
                    for report in checker.scan(base).conflicts
                ]
                assert reports == expected
