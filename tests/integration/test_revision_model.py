"""Compare real revisions with the proved, executable Lean index/journal model."""

import json
import random
import subprocess
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path

import pytest

from hypomnesis.contracts.codec import TypeCodec
from hypomnesis.epistemics.knowledge import AXIOM, Fact, KnowledgeBase
from hypomnesis.epistemics.provenance import ONE, ZERO, Obs, One, Plus, Times, Zero, obs
from hypomnesis.epistemics.serialization import _encode_provenance
from hypomnesis.epistemics.storage import export_json, import_json
from hypomnesis.session import Session

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


def payload(fact):
    return json.dumps(
        {"value": fact.value, "method": fact.method, "premises": fact.premises},
        sort_keys=True,
    )


def fact_term(fact):
    return f"⟨{literal(fact.key)}, {provenance(fact.provenance)}, {literal(payload(fact))}⟩"


def unknown_term(unknown):
    return f"({literal(unknown.key)}, {literal(unknown.description)})"


def event_term(event):
    fact = "none" if event.fact is None else f"(some {fact_term(event.fact)})"
    unknown = "none" if event.unknown is None else f"(some {unknown_term(event.unknown)})"
    return (
        f"⟨{event.seq}, {literal(event.kind)}, {literal(event.key)}, "
        f"{literal(event.detail)}, {fact}, {unknown}⟩"
    )


def context(base):
    return json.dumps(
        {
            "sources": {key: asdict(source) for key, source in base.sources.items()},
            "counter": base._next_source_id,
        },
        sort_keys=True,
    )


def state_term(base):
    return (
        f"⟨{items(fact_term(fact) for fact in base.facts.values())}, "
        f"{items(unknown_term(unknown) for unknown in base.unknowns.values())}, "
        f"{items(literal(source) for source in sorted(base.retracted))}, "
        f"{items(event_term(event) for event in base.journal)}, {literal(context(base))}⟩"
    )


def wire_fact(fact):
    if fact is None:
        return None
    return [fact.key, _encode_provenance(fact.provenance), payload(fact)]


def wire_unknown(unknown):
    return None if unknown is None else [unknown.key, unknown.description]


def wire(base):
    return {
        "facts": [wire_fact(fact) for fact in base.facts.values()],
        "unknowns": [wire_unknown(unknown) for unknown in base.unknowns.values()],
        "withdrawn": sorted(base.retracted),
        "journal": [
            [
                event.seq,
                event.kind,
                event.key,
                event.detail,
                wire_fact(event.fact),
                wire_unknown(event.unknown),
            ]
            for event in base.journal
        ],
        "context": context(base),
    }


RUNNER = """
import Hypomnesis.Epistemics.Revision
import Lean
open Hypomnesis.Epistemics
open Hypomnesis.Epistemics.Revision
set_option maxRecDepth 8192
set_option maxHeartbeats 8000000
def provJson : Prov String → Lean.Json
  | .obs x => .mkObj [("op", .str "obs"), ("id", .str x)]
  | .zero => .mkObj [("op", .str "zero")]
  | .one => .mkObj [("op", .str "one")]
  | .plus a b => .mkObj [("op", .str "plus"), ("left", provJson a), ("right", provJson b)]
  | .times a b => .mkObj [("op", .str "times"), ("left", provJson a), ("right", provJson b)]
def factJson (f : Revision.Fact String) : Lean.Json :=
  .arr #[.str f.key, provJson f.provenance, .str f.data]
def eventJson (e : Event String) : Lean.Json :=
  .arr #[Lean.toJson e.seq, .str e.kind, .str e.key, .str e.detail,
    (e.fact.map factJson).getD .null, Lean.toJson e.unknown]
def stateJson : Option (State String String) → Lean.Json
  | none => .null
  | some s => .mkObj [
    ("facts", .arr (s.facts.map factJson).toArray),
    ("unknowns", Lean.toJson s.unknowns),
    ("withdrawn", Lean.toJson s.withdrawn),
    ("journal", .arr (s.journal.map eventJson).toArray),
    ("context", .str s.context)]
"""


def random_term(rng, sources, depth):
    if depth == 0 or rng.randrange(3) == 0:
        return rng.choice([ZERO, ONE, *(obs(source) for source in sources)])
    constructor = rng.choice([Plus, Times])
    return constructor(random_term(rng, sources, depth - 1), random_term(rng, sources, depth - 1))


def cases():
    rng = random.Random(36)
    corpus = []
    for i in range(40):
        base = KnowledgeBase()
        for j in range(3):
            base.observe(f"input-{j}", j, f"sensor-{j}")
        sources = list(base.sources)

        for j in range(5):
            p = ZERO if j == 0 else ONE if j == 1 else random_term(rng, sources, 3)
            base.publish_fact(Fact(f"output-{j}", j + i, p, "opaque derivation"))
        base.unknown("hole", "awaiting evidence")
        base.unknown("input-0", "pending confirmation")
        if i % 2:
            base.retract_source(sources[0], "earlier withdrawal")
        for source in (sources[0], sources[1], "unrelated", AXIOM):
            corpus.append((base, source, "révision"))
    return corpus


def test_real_python_and_lean_revision_states_match(lean_lake, tmp_path):
    built = subprocess.run(
        [lean_lake, "build", "Hypomnesis.Epistemics.Revision"],
        cwd=FORMAL,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert built.returncode == 0, built.stdout + built.stderr
    corpus = cases()
    assert len(corpus) == 160
    for start in range(0, len(corpus), 20):
        batch = corpus[start : start + 20]
        source = tmp_path / "Samples.lean"
        source.write_text(
            RUNNER
            + "\ndef cases : List (State String String × String × String) := "
            + items(
                f"({state_term(base)}, {literal(source)}, {literal(reason)})"
                for base, source, reason in batch
            )
            + "\n#eval IO.println (Lean.Json.arr ((cases.map fun (s, x, r) => "
            "Lean.Json.arr #[stateJson (revise_incr s x r), "
            "stateJson (recompute_after s x r)]).toArray)).compress\n",
            encoding="utf-8",
        )
        result = subprocess.run(
            [lean_lake, "env", "lean", f"--root={tmp_path}", str(source)],
            cwd=FORMAL,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        results = json.loads(result.stdout)
        assert len(results) == len(batch)
        for (base, source, reason), pair in zip(batch, results, strict=True):
            changed = deepcopy(base)
            if source == AXIOM:
                with pytest.raises(ValueError, match="rétractable"):
                    changed.retract_source(source, reason)
                assert wire(changed) == wire(base)
                expected = None
            else:
                changed.retract_source(source, reason)
                expected = wire(changed)
            for actual in pair:
                if actual is not None:
                    actual["withdrawn"].sort()
                assert actual == expected


def test_zero_invalidation_is_replayable_with_the_real_storage_codec():
    codec = TypeCodec(Session(prelude=False).checker, "int")
    base = KnowledgeBase()
    base.publish_fact(Fact("x", 1, ZERO, "unsupported"))
    base.retract_source("unrelated", "revision")
    assert not base.facts and base.unknowns["x"].description == "invalidée : revision"
    loaded = import_json(export_json(base, {"x": codec}), {"x": codec})
    assert loaded.journal == base.journal and loaded.unknowns == base.unknowns
