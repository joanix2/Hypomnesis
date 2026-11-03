import pytest

from hypomnesis.language.errors import EvaluationError
from hypomnesis.session import Session
from tests.conftest import run


def value(source: str, expr: str) -> str:
    session = Session()
    session.load(source)
    return session.eval(expr).render().split(" = ", 1)[1]


def test_arithmetic_and_strings():
    assert value("", "1 + 2 * 3 - 4 / 2") == "5"
    assert value("", "7 mod 3, -7 / 2, -7 mod 2") == "(1, -3, -1)"
    assert value("", "2.0 ** 10.0 /. 4.0") == "256."
    assert value("", '"hyp" ^ "omnesis"') == '"hypomnesis"'


def test_closures_capture_their_environment():
    assert value("let add n = fun x -> x + n\nlet add3 = add 3", "add3 4") == "7"


def test_partial_and_over_application():
    source = "let add3 a b c = a + b + c\nlet twice f = fun x -> f (f x)"
    assert value(source, "List.map (add3 1 2) [1; 2]") == "[4; 5]"
    assert value(source, "twice (add3 0 1) 0") == "2"
    assert value(source, "(fun x -> fun y -> x * y) 6 7") == "42"


def test_pattern_matching():
    source = (
        "type shape = Circle of float | Rect of float * float | Empty\n"
        "let area s = match s with\n"
        "  | Circle r -> 3.0 *. r *. r\n"
        "  | Rect (w, h) when w = h -> w *. w\n"
        "  | Rect (w, h) -> w *. h\n"
        "  | Empty -> 0.0\n"
        "let rec first_two l = match l with x :: y :: _ -> Some (x, y) | _ -> None"
    )
    assert value(source, "List.map area [Circle 1.0; Rect (2.0, 2.0); Rect (2.0, 3.0); Empty]") == (
        "[3.; 4.; 6.; 0.]"
    )
    assert value(source, "first_two [1; 2; 3], first_two [1]") == "(Some (1, 2), None)"


def test_records():
    source = "type p = { x : int; y : int }\nlet a = { y = 2; x = 1 }\nlet b = { a with x = 10 }"
    assert value(source, "a, b, b.x + b.y") == "({x = 1; y = 2}, {x = 10; y = 2}, 12)"
    assert value(source, "match b with { x; y = 2 } -> x | _ -> 0") == "10"


def test_structural_equality_and_ordering():
    assert value("", '[1; 2] = [1; 2], Some 1 < Some 2, None < Some 0, (1, "b") > (1, "a")') == (
        "(true, true, true, true)"
    )


def test_comparing_functions_fails():
    with pytest.raises(EvaluationError, match="functional value"):
        Session().eval("(fun x -> x) = (fun x -> x)")


def test_short_circuit_boolean_operators():
    assert value("", 'false && failwith "never", true || failwith "never"') == "(false, true)"


def test_tail_calls_run_in_constant_stack():
    assert (
        value(
            "let rec count n acc = if n = 0 then acc else count (n - 1) (acc + 1)", "count 300000 0"
        )
        == "300000"
    )


def test_deep_non_tail_recursion():
    assert (
        value("let rec depth n = if n = 0 then 0 else 1 + depth (n - 1)", "depth 50000") == "50000"
    )


def test_shadowing_keeps_old_closures_intact():
    bindings = run("let x = 1\nlet get () = x\nlet x = 2\nlet r = (get (), x)")
    assert bindings["r"] == "val r : int * int = (1, 2)"


def test_let_and_sees_outer_scope():
    assert value("", "let x = 1 in let x = 2 and y = x in (x, y)") == "(2, 1)"


def test_match_failure_is_reported():
    with pytest.raises(EvaluationError, match="Match_failure"):
        Session().eval("match 3 with 1 -> 0")


def test_division_by_zero():
    with pytest.raises(EvaluationError, match="Division_by_zero"):
        Session().eval("1 / 0")


def test_failwith():
    with pytest.raises(EvaluationError, match="Failure: boom"):
        Session().eval('failwith "boom"')


def test_prelude_list_functions():
    assert value("", "List.sort compare [3; 1; 2], List.rev [1; 2; 3]") == "([1; 2; 3], [3; 2; 1])"
    assert value("", "List.filter (fun x -> x mod 2 = 0) (List.range 0 7)") == "[0; 2; 4; 6]"
    assert value("", "List.fold_right (fun x acc -> x :: acc) [1; 2] [3]") == "[1; 2; 3]"
    assert value("", 'List.assoc_opt "b" [("a", 1); ("b", 2)]') == "Some 2"
    assert value("", 'String.concat "-" (List.map string_of_int [1; 2; 3])') == '"1-2-3"'
    assert value("", "Option.value (Option.map (fun x -> x + 1) None) 0") == "0"


def test_unparenthesized_tuples_and_or_patterns():
    source = (
        "let a, b = 1, 2\n"
        "let classify x y = match x, y with\n"
        '  | 0, _ | _, 0 -> "zero"\n'
        '  | (1 | 2), n -> "small " ^ string_of_int n\n'
        '  | _ -> "other"'
    )
    assert value(source, "a + b") == "3"
    assert value(source, "List.map (fun (x, y) -> classify x y) [(0, 5); (2, 7); (3, 3)]") == (
        '["zero"; "small 7"; "other"]'
    )
