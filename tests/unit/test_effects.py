"""Bibliothèque standard : Json, to_json, Effect et >>= (HYP-060)."""

from hypomnesis.language import ast as A
from hypomnesis.language.parser import parse_expression
from hypomnesis.session import Session

S = Session()


def value(expr: str) -> str:
    return S.eval(expr).render().split(" = ", 1)[1]


def test_bind_with_lambda_nests_to_the_right():
    e = parse_expression("a >>= fun x -> b >>= fun y -> c")
    assert isinstance(e, A.BinOp) and isinstance(e.right, A.Lambda)
    inner = e.right.body
    assert isinstance(inner, A.BinOp) and inner.op == ">>="


def test_effect_is_a_monad_on_pure_values():
    # loi de l'élément neutre à gauche : return x >>= f  ==  f x
    assert value("Effect.return 3 >>= fun x -> Effect.return (x + 1)") == "Done 4"
    # associativité, sur une description non exécutée
    assert value(
        '(Effect.note "a" >>= fun () -> Effect.return 1) >>= fun x -> Effect.return (x + 1)'
    ).startswith('Note ("a"')


def test_procedures_are_inert_values():
    assert S.type_of("Effect.observe") == "string -> (string * Json.t) Effect.t"
    assert value('Effect.observe "capteur"').startswith('Observe ("capteur", <fun>)')


def test_to_json():
    assert value('to_json (1, "a", [true])') == 'Arr [Num 1.; Str "a"; Arr [Bool true]]'
    assert value("to_json (Some 2.5, None)") == "Arr [Num 2.5; Null]"
    assert value('Json.num_field "x" (Json.Obj [("x", Json.Num 3.0)])') == "Some 3."
