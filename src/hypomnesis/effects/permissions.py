"""Declarative, exact-name permissions; explicit denials override grants."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PermissionPolicy:
    allowed: frozenset[str] = frozenset()
    denied: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        for entries in (self.allowed, self.denied):
            if not isinstance(entries, frozenset) or any(
                not isinstance(entry, str) or not entry.strip() for entry in entries
            ):
                raise ValueError("permissions must be immutable sets of non-empty names")

    def permits(self, permission: str) -> bool:
        return permission in self.allowed and permission not in self.denied
