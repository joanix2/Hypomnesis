"""Optional, domain-independent linear regression with held-out error reporting."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from importlib import import_module
from typing import TypeGuard

from hypomnesis.capabilities.result import Certificate, Diagnostic, Result, failure, success


def _number(value: object) -> TypeGuard[int | float]:
    if not isinstance(value, int | float) or isinstance(value, bool):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


@dataclass(frozen=True)
class Prediction:
    value: float
    model: str
    version: str
    validation_rmse: float

    @property
    def origin(self) -> str:
        return (
            f"{self.model}@{self.version}; "
            f"validation_rmse={self.validation_rmse:.17g}; empirical, not calibrated"
        )


class RegressionEstimator:
    """Setup errors raise ValueError; calls return capability diagnostics."""

    def __init__(
        self,
        *,
        model: str,
        version: str,
        features: Sequence[str],
        training: Sequence[Sequence[float]],
        validation: Sequence[Sequence[float]],
    ) -> None:
        if any(not isinstance(s, str) or not s.strip() for s in (model, version)):
            raise ValueError("model and version must be nonempty identifiers")
        if (
            not isinstance(features, Sequence)
            or isinstance(features, str)
            or not features
            or any(not isinstance(s, str) or not s.strip() for s in features)
        ):
            raise ValueError("features must be a nonempty sequence of identifiers")
        if len(set(features)) != len(features):
            raise ValueError("feature names must be distinct")
        self.model = model
        self.version = version
        self.features = tuple(features)
        train = self._rows(training)
        held_out = self._rows(validation)
        if len(train) < len(features) + 1:
            raise ValueError("insufficient training rows")
        if {row[:-1] for row in train} & {row[:-1] for row in held_out}:
            raise ValueError("training and validation inputs must be disjoint")
        self.domain = tuple(
            (min(row[i] for row in train), max(row[i] for row in train))
            for i in range(len(features))
        )
        if any(lo == hi for lo, hi in self.domain):
            raise ValueError("every feature must vary in the training data")
        if any(not self._inside(row[:-1]) for row in held_out):
            raise ValueError("validation inputs must be inside the training domain")
        linear_model = import_module("sklearn.linear_model")
        self._model = linear_model.LinearRegression().fit(
            [row[:-1] for row in train], [row[-1] for row in train]
        )
        predictions = self._model.predict([row[:-1] for row in held_out])
        self.validation_rmse = math.sqrt(
            sum(
                (float(predicted) - row[-1]) ** 2
                for predicted, row in zip(predictions, held_out, strict=True)
            )
            / len(held_out)
        )
        if not math.isfinite(self.validation_rmse):
            raise ValueError("nonfinite validation error")

    def _rows(self, rows: Sequence[Sequence[float]]) -> tuple[tuple[float, ...], ...]:
        if (
            not isinstance(rows, Sequence)
            or not rows
            or any(
                not isinstance(row, Sequence)
                or isinstance(row, str)
                or len(row) != len(self.features) + 1
                or any(not _number(v) for v in row)
                for row in rows
            )
        ):
            raise ValueError("rows must contain finite numeric features followed by a target")
        return tuple(tuple(float(v) for v in row) for row in rows)

    def _inside(self, values: Sequence[float]) -> bool:
        return all(lo <= v <= hi for v, (lo, hi) in zip(values, self.domain, strict=True))

    def estimate(self, unknown: Mapping[str, object], /) -> Result[Prediction]:
        if not isinstance(unknown, Mapping) or set(unknown) != set(self.features):
            return failure(Diagnostic("estimator.features", "expected exactly the model features"))
        values: list[float] = []
        for name in self.features:
            value = unknown[name]
            if not _number(value):
                return failure(Diagnostic("estimator.input", "features must be finite numbers"))
            values.append(float(value))
        if not self._inside(values):
            return failure(
                Diagnostic(
                    "estimator.out_of_domain",
                    "extrapolation outside the training domain is refused",
                    data={"features": self.features, "domain": self.domain, "input": values},
                )
            )
        try:
            value = float(self._model.predict([values])[0])
        except ValueError as exc:
            return failure(Diagnostic("estimator.predict", str(exc)))
        if not math.isfinite(value):
            return failure(Diagnostic("estimator.predict", "nonfinite model prediction"))
        prediction = Prediction(value, self.model, self.version, self.validation_rmse)
        return success(
            prediction,
            certificate=Certificate(
                "estimator.linear-regression",
                {
                    "model": self.model,
                    "version": self.version,
                    "uncertainty": {"kind": "held-out-rmse", "value": self.validation_rmse},
                    "features": self.features,
                    "domain": self.domain,
                },
            ),
        )
