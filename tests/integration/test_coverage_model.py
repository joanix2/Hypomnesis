"""The actual Python pattern matrices agree with the sound Lean coverage checker."""

import itertools
import json
import random
import subprocess
from pathlib import Path

import pytest

from hypomnesis.ir import core as ir
from hypomnesis.language.typesystem.exhaustiveness import Coverage
from hypomnesis.language.typesystem.types import TCon, prune, substitute
from hypomnesis.session import Session

FORMAL = Path(__file__).resolve().parents[2] / "formal"


def lean_list(items):
    return "[" + ", ".join(items) + "]"


def product(items, constructor, terminal=None):
    items = list(items)
    if terminal is not None:
        items.append(terminal)
    result = items.pop()
    for item in reversed(items):
        result = f"({constructor} {item} {result})"
    return result


class Model:
    def __init__(self, checker):
        self.types = checker.types_by_qname
        self.indices = {}
        self.signature = []

    def type(self, type_):
        type_ = prune(type_)
        assert isinstance(type_, TCon), type_
        if type_.name in ("int", "bool", "float", "string", "unit"):
            return "." + type_.name
        if type_.name == "*":
            return product((self.type(t) for t in type_.args), ".prod")
        if type_.name == "->":
            return f"(.arrow {self.type(type_.args[0])} {self.type(type_.args[1])})"
        if type_ not in self.indices:
            self.indices[type_] = len(self.signature)
            self.signature.append(None)
            info = self.types[type_.name]
            if info.kind == "record":
                body = product(
                    (self.type(substitute(f.type, type_.args)) for f in info.fields),
                    ".prod",
                    ".unit",
                )
                constructors = [body]
            else:
                assert info.ctors, info
                constructors = [
                    ".unit" if c.arg is None else self.type(substitute(c.arg, type_.args))
                    for c in info.ctors
                ]
            self.signature[self.indices[type_]] = lean_list(constructors)
        return f"(.data {self.indices[type_]})"

    def patterns(self, pattern, type_):
        type_ = prune(type_)
        assert isinstance(type_, TCon)
        if isinstance(pattern, ir.PAlias):
            return self.patterns(pattern.pattern, type_)
        if isinstance(pattern, ir.POr):
            return self.patterns(pattern.left, type_) + self.patterns(pattern.right, type_)
        if isinstance(pattern, ir.PWild):
            return [".wild"]
        if isinstance(pattern, ir.PVar):
            return [".var"]
        if isinstance(pattern, ir.PLit):
            value = pattern.value
            if value == ():
                return [".wild"]
            if type(value) is bool:
                return ["(.bool " + str(value).lower() + ")"]
            if type(value) is int:
                return [f"(.int ({value}))"]
            if type(value) is float:
                return [f"(.float ({value} : Float))"]
            assert isinstance(value, str)
            return ["(.string " + json.dumps(value, ensure_ascii=False) + ")"]
        if isinstance(pattern, ir.PTuple):
            parts = [self.patterns(p, t) for p, t in zip(pattern.items, type_.args, strict=True)]
            return [product(choice, ".pair") for choice in itertools.product(*parts)]
        info = self.types[type_.name]
        if isinstance(pattern, ir.PRecord):
            fields = dict(pattern.fields)
            parts = [
                self.patterns(fields.get(f.name, ir.PWild()), substitute(f.type, type_.args))
                for f in info.fields
            ]
            return [
                f"(.ctor 0 {product(choice, '.pair', '.wild')})"
                for choice in itertools.product(*parts)
            ]
        assert isinstance(pattern, ir.PCtor), pattern
        ctor = info.ctors[pattern.index]
        if pattern.arg is None:
            arguments = [".wild"]
        else:
            arguments = self.patterns(pattern.arg, substitute(ctor.arg, type_.args))
        return [f"(.ctor {pattern.index} {arg})" for arg in arguments]


def case(session, source):
    session.check(source)
    [site] = session.checker._match_sites
    model = Model(session.checker)
    type_ = model.type(site.type)
    patterns = [
        pattern
        for arm in site.arms
        if not arm.guarded
        for pattern in model.patterns(arm.pattern, site.type)
    ]
    matrix = [(arm.pattern,) for arm in site.arms if not arm.guarded]
    expected = (
        Coverage(session.checker.types_by_qname).useful(matrix, (ir.PWild(),), (site.type,)) is None
    )
    expression = f"exhaustive {lean_list(model.signature)} 128 {type_} {lean_list(patterns)}"
    return expression, expected


@pytest.fixture(scope="module")
def compare(lean_lake, tmp_path_factory):
    built = subprocess.run(
        [lean_lake, "build", "Hypomnesis.Core.CoverageExamples"],
        cwd=FORMAL,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert built.returncode == 0, built.stdout + built.stderr
    directory = tmp_path_factory.mktemp("lean-coverage")

    def run(cases):
        for start in range(0, len(cases), 40):
            batch = cases[start : start + 40]
            source = directory / "Samples.lean"
            source.write_text(
                "import Hypomnesis.Core.CoverageExamples\nimport Lean\n"
                "open Hypomnesis.Core Hypomnesis.Core.Coverage\n"
                "set_option maxRecDepth 4096\nset_option maxHeartbeats 4000000\n"
                "#eval IO.println (Lean.toJson "
                + lean_list(f"({expression})" for expression, _ in batch)
                + ").compress\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [lean_lake, "env", "lean", str(source)],
                cwd=FORMAL,
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
            assert result.returncode == 0, result.stdout + result.stderr
            actual = json.loads(result.stdout)
            assert actual == [expected for _, expected in batch], batch

    return run


def test_real_python_matrices_match_lean_across_nested_domains(compare):
    session = Session()
    session.check(
        "type record = {a : bool; b : bool}\n"
        "type tree = Leaf | Branch of tree * tree\n"
        "type 'a box = Box of 'a\n"
        "type choice = Empty | Chosen of bool"
    )
    corpus = [
        ("bool", ["true"]),
        ("bool", ["true", "false"]),
        ("bool", ["_ when true"]),
        ("bool", ["true when true", "false"]),
        ("bool", ["_ when false", "true", "false"]),
        ("bool", ["(true | false)"]),
        ("bool option", ["None"]),
        ("bool option", ["Some true", "None", "Some false"]),
        ("bool option", ["(Some true | Some false)", "None"]),
        ("bool option", ["(Some _ as o)", "None"]),
        ("int list", ["[]", "_ :: _"]),
        ("int list", ["[]", "[_]", "_ :: _ :: _"]),
        ("int list", ["[]", "[_]"]),
        ("int list", ["_ :: _"]),
        ("tree", ["Leaf", "Branch _"]),
        ("tree", ["Leaf", "Branch (Leaf, _)"]),
        ("tree", ["Leaf", "Branch (Leaf, _)", "Branch (Branch _, _)"]),
        ("bool box", ["Box true", "Box false"]),
        ("bool box", ["Box true"]),
        ("choice", ["Empty", "Chosen true", "Chosen false"]),
        ("record", ["{a = true}", "{a = false}"]),
        ("record", ["{a = true; b = false}", "{a = false}"]),
        ("record", ["{a = true}", "{b = true}", "{a = false; b = false}"]),
        ("bool * bool * bool", ["(true, _, _)", "(false, true, _)", "(false, false, _)"]),
        ("int", ["-1", "0", "1"]),
        ("int", ["-1", "_"]),
        ("float", ["0.0", "1.0"]),
        ("float", ["_"]),
        ("string", ['""', '"texte"']),
        ("string", ['""', "_"]),
        ("unit", ["()"]),
    ]
    cases = []
    for type_, patterns in corpus:
        arms = " | ".join(p + " -> 0" for p in patterns)
        cases.append(case(session, f"let f (x : {type_}) = match x with {arms}"))
    assert any(expected for _, expected in cases)
    assert any(not expected for _, expected in cases)
    compare(cases)


def test_generated_finite_matrices_match_lean_and_the_exact_domain(compare):
    session = Session()
    rng = random.Random(22)
    domain = set(itertools.product([False, True], repeat=2))
    patterns = [
        ("_", domain),
        ("(true, _)", {(True, False), (True, True)}),
        ("(_, false)", {(False, False), (True, False)}),
    ] + [(f"({str(a).lower()}, {str(b).lower()})", {(a, b)}) for a, b in sorted(domain)]
    cases = []
    for _ in range(240):
        selected = [rng.randrange(len(patterns)) for _ in range(rng.randrange(1, 9))]
        covered = set().union(*(patterns[i][1] for i in selected))
        source = "let f (x : bool * bool) = match x with " + " | ".join(
            patterns[i][0] + " -> 0" for i in selected
        )
        expression, expected = case(session, source)
        assert expected == (covered == domain)
        cases.append((expression, expected))
    compare(cases)


def test_budget_exhaustion_is_never_an_acceptance(compare):
    compare(
        [
            ("exhaustive [] 0 .bool [.wild]", None),
            ("exhaustive [] 1 .bool [.wild]", None),
            ("exhaustive [] 2 .bool [.wild]", True),
            ("exhaustive [] 1 .bool [.bool true, .bool false]", None),
        ]
    )
