"""Static package declarations and dependency plans shared by every language frontend."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import networkx as nx

from hypomnesis.contracts.registry import SchemaRegistry
from hypomnesis.engine.errors import LanguageError, MissingDescriptionError, SourceError
from hypomnesis.language import ast as A
from hypomnesis.language.docs import missing_descriptions
from hypomnesis.language.errors import HypomnesisError
from hypomnesis.language.parser import parse_program
from hypomnesis.session import Session, prelude_source

ENTRY = "langage.hyp"
DECLARATION_SCHEMA = "https://schemas.example.org/hypomnesis/language-declaration/1.0.0"


def package_file(root: Path, reference: str) -> Path:
    root = root.resolve()
    if Path(reference).is_absolute():
        raise LanguageError(f"chemin relatif au paquet requis : {reference}")
    path = (root / reference).resolve()
    if not path.is_relative_to(root) or path == root:
        raise LanguageError(f"fichier hors du paquet du langage : {reference} ({root})")
    return path


def entry_path(path: Path) -> Path:
    path = path.resolve()
    return path if path.suffix == ".hyp" else path / ENTRY


def _read(path: Path, overlays: dict[str, str]) -> str:
    if str(path) in overlays:
        return overlays[str(path)]
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise LanguageError(f"lecture impossible de {path} : {exc}") from exc


def _parse(path: Path, source: str) -> A.Program:
    try:
        return parse_program(source)
    except HypomnesisError as exc:
        raise SourceError(exc, path, source) from exc


def _nested_declarations(items: tuple[A.Item, ...]) -> bool:
    return any(
        isinstance(item, A.LanguageItem)
        or (isinstance(item, A.ModuleItem) and _nested_declarations(item.items))
        for item in items
    )


@dataclass(frozen=True)
class LayerSource:
    path: Path
    text: str
    program: A.Program


@dataclass(frozen=True)
class Layer:
    entry: Path
    configuration: dict[str, Any]
    sources: tuple[LayerSource, ...]

    @property
    def name(self) -> str:
        return self.configuration["name"]

    @property
    def root(self) -> Path:
        return self.entry.parent


@dataclass
class LayerPlan:
    entry: Path
    layers: dict[Path, Layer]
    graph: nx.DiGraph

    @property
    def root(self) -> Layer:
        return self.layers[self.entry]

    def order(self, entry: Path | None = None) -> list[Path]:
        target = entry or self.entry
        closure = nx.ancestors(self.graph, target) | {target}
        return list(
            nx.lexicographical_topological_sort(
                self.graph.subgraph(closure), key=lambda path: self.layers[path].name
            )
        )

    def source_files(self) -> list[LayerSource]:
        return [source for entry in self.order() for source in self.layers[entry].sources]

    def to_json(self) -> dict[str, object]:
        generations = nx.topological_generations(self.graph)
        return {
            "version": "1.0.0",
            "root": self.root.name,
            "orientation": "dependency-to-dependent",
            "nodes": [
                {
                    "id": layer.name,
                    "version": layer.configuration["version"],
                    "entry": str(layer.entry),
                }
                for layer in sorted(self.layers.values(), key=lambda layer: layer.name)
            ],
            "edges": [
                {"from": self.layers[a].name, "to": self.layers[b].name}
                for a, b in sorted(
                    self.graph.edges, key=lambda edge: tuple(self.layers[p].name for p in edge)
                )
            ],
            "layers": [
                sorted(self.layers[path].name for path in generation) for generation in generations
            ],
        }


def resolve_layers(
    root: Path, overlays: dict[str, str] | None = None, *, stop_at: Path | None = None
) -> LayerPlan:
    """Read declarations and source ASTs without evaluating any user code."""
    overlays = {str(Path(path).resolve()): text for path, text in (overlays or {}).items()}
    schemas = SchemaRegistry.with_builtin_schemas()
    layers: dict[Path, Layer] = {}
    graph = nx.DiGraph()
    identities: dict[str, Path] = {}
    source_owners: dict[Path, Path] = {}

    def visit(path: Path) -> None:
        if path in layers:
            return
        text = _read(path, overlays)
        program = _parse(path, text)
        if not program.items:
            raise LanguageError(f"{path} : déclaration `language` attendue en premier")
        declaration, *body = program.items
        if not isinstance(declaration, A.LanguageItem):
            raise LanguageError(f"{path} : déclaration `language` attendue en premier")
        if _nested_declarations(tuple(body)):
            raise LanguageError(f"{path} : déclaration `language` unique et de premier niveau")
        config: dict[str, Any] = dict(declaration.configuration)
        if "name" in config:
            raise LanguageError(f"{path} : le nom est déclaré après `language`, pas dans le record")
        config["name"] = declaration.name
        config.setdefault("sources", [])
        config.setdefault("imports", [])
        issues = schemas.issues(DECLARATION_SCHEMA, config)
        if issues:
            raise LanguageError(f"{path} : déclaration invalide : " + "; ".join(map(str, issues)))
        if declaration.name in identities:
            raise LanguageError(
                f"identité de couche dupliquée {declaration.name} : "
                f"{identities[declaration.name]} et {path}"
            )
        identities[declaration.name] = path
        sources = [LayerSource(path, text, A.Program(tuple(body), span=program.span))]
        for reference in config["sources"]:
            if sources[-1].path == stop_at:
                break
            source_path = package_file(path.parent, reference)
            if source_path == path:
                raise LanguageError(f"{path} : l'entrée ne doit pas figurer dans sources")
            source_text = _read(source_path, overlays)
            source_program = _parse(source_path, source_text)
            if _nested_declarations(source_program.items):
                raise LanguageError(f"{source_path} : déclaration réservée au fichier d'entrée")
            sources.append(LayerSource(source_path, source_text, source_program))
        for source in sources:
            if source.path in source_owners:
                raise LanguageError(
                    f"source partagée entre couches ou répétée : {source.path} "
                    f"({source_owners[source.path]}, {path})"
                )
            source_owners[source.path] = path
        for key in ("contracts", "adapters"):
            for reference in config.get(key, []):
                package_file(path.parent, reference)
        if "examples" in config:
            package_file(path.parent, config["examples"])
        layers[path] = Layer(path, config, tuple(sources))
        graph.add_node(path)
        for reference in config["imports"]:
            if Path(reference).is_absolute():
                raise LanguageError(f"{path} : import relatif requis : {reference}")
            dependency = entry_path(path.parent / reference)
            graph.add_edge(dependency, path)
            visit(dependency)

    entry = entry_path(root)
    visit(entry)
    if not nx.is_directed_acyclic_graph(graph):
        cycle = nx.find_cycle(graph)
        names = [layers[a].name for a, _ in cycle] + [layers[cycle[0][0]].name]
        raise LanguageError("cycle d'imports : " + " -> ".join(names))
    return LayerPlan(entry, layers, graph)


def check_layers(
    plan: LayerPlan,
    *,
    strict: bool = True,
    stop_at: Path | None = None,
    entry: Path | None = None,
) -> Session:
    """Check each layer only with its declared closure; return the root's static session."""
    result: Session | None = None
    root = entry or plan.entry
    for target in plan.order(root):
        session = Session(prelude=False)
        session.check(prelude_source())
        session.prelude_definitions = len(session.definitions)
        owners: dict[tuple[str, str], Path] = {}
        for entry in plan.order(target):
            for source in plan.layers[entry].sources:
                tables = ("values", "types", "modules", "ctors")
                before = {
                    (kind, name): value
                    for kind in tables
                    for name, value in getattr(session.checker.root, kind).items()
                }
                try:
                    session.check_program(source.program)
                    if strict:
                        missing = missing_descriptions(source.text)
                        if missing:
                            raise MissingDescriptionError(missing[0], str(source.path))
                except HypomnesisError as exc:
                    if isinstance(exc, MissingDescriptionError):
                        raise
                    raise SourceError(exc, source.path, source.text) from exc
                for kind in tables:
                    for name, value in getattr(session.checker.root, kind).items():
                        key = kind, name
                        if before.get(key) is value:
                            continue
                        if key in owners and owners[key] != entry:
                            raise LanguageError(
                                f"{source.path} : collision d'export {name} ({kind}) entre "
                                f"{owners[key]} et {entry}"
                            )
                        owners[key] = entry
                if target == root and source.path == stop_at:
                    return session
        result = session
    assert result is not None
    return result
