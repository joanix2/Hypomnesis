"""Replayable certificates from host-selected, typed, pure language checkers."""

from __future__ import annotations

from collections.abc import Mapping

from opentelemetry.trace import Status, StatusCode

from hypomnesis.capabilities.result import Certificate, Diagnostic, Result, failure, success
from hypomnesis.contracts.codec import CodecError, TypeCodec
from hypomnesis.language.errors import EvaluationError
from hypomnesis.observability.trace import operation
from hypomnesis.runtime.values import Value, iter_list
from hypomnesis.session import Session


class LanguageValidator:
    def __init__(self, session: Session, function: str, input_type: str) -> None:
        self.codec = TypeCodec(session.checker, input_type)
        if session.type_of(function) != f"{input_type} -> string list":
            raise ValueError(f"{function} must have type {input_type} -> string list")
        self.session = session
        self.function = function
        self.input_type = input_type
        self._callback = session.value(function)

    def _check(self, value: Value) -> tuple[str, ...]:
        violations = tuple(iter_list(self.session.interpreter.apply(self._callback, [value])))
        if any(not isinstance(v, str) or not v.strip() for v in violations):
            raise EvaluationError("validator must return meaningful string violations")
        return violations

    def validate(self, proposal: Value, /) -> Result[Value]:
        with operation("validator.check", plugin=self.function) as span:
            result = self._validate(proposal)
            if span is not None:
                status = (
                    "accepted"
                    if result.ok
                    else "rejected"
                    if result.diagnostics[0].code == "validator.rejected"
                    else "error"
                )
                span.set_attribute("validation.result", status)
                if status == "error":
                    span.set_status(Status(StatusCode.ERROR))
            return result

    def _validate(self, proposal: Value) -> Result[Value]:
        try:
            payload = self.codec.encode(proposal)
            snapshot = self.codec.decode(payload)
        except CodecError as exc:
            return failure(Diagnostic("validator.input", str(exc)))
        try:
            violations = self._check(snapshot)
        except EvaluationError as exc:
            return failure(Diagnostic("validator.checker", str(exc)))
        evidence = {
            "checker": self.function,
            "input_type": self.input_type,
            "input": payload,
            "violations": list(violations),
        }
        if violations:
            return failure(
                Diagnostic(
                    "validator.rejected",
                    "; ".join(violations),
                    data={"counterexample": evidence},
                )
            )
        return success(snapshot, certificate=Certificate("validator.accepted", evidence))

    def recheck(self, evidence: Mapping[str, object]) -> Result[bool]:
        """A valid witness succeeds; its value says whether the proposal was accepted."""
        if (
            not isinstance(evidence, Mapping)
            or set(evidence) != {"checker", "input_type", "input", "violations"}
            or evidence["checker"] != self.function
            or evidence["input_type"] != self.input_type
            or type(evidence["violations"]) is not list
        ):
            return failure(Diagnostic("validator.evidence", "incorrect evidence envelope"))
        try:
            value = self.codec.decode(evidence["input"])
            actual = self._check(value)
        except (CodecError, EvaluationError) as exc:
            return failure(Diagnostic("validator.evidence", str(exc)))
        if list(actual) != evidence["violations"]:
            return failure(Diagnostic("validator.evidence", "violations do not match replay"))
        return success(not actual)
