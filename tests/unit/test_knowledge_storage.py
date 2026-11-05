"""Real SQLite transactions, typed journal replay and strict JSON imports."""

import json
import sqlite3
from copy import deepcopy
from dataclasses import replace

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from hypomnesis.contracts.codec import TypeCodec
from hypomnesis.contracts.registry import ContractError
from hypomnesis.epistemics.conflicts import ConflictChecker, Invariant
from hypomnesis.epistemics.knowledge import Fact, KnowledgeBase, Source
from hypomnesis.epistemics.provenance import obs
from hypomnesis.epistemics.storage import (
    SQLITE_VERSION,
    JournalError,
    SQLiteStore,
    export_json,
    from_document,
    import_json,
    to_document,
)
from hypomnesis.session import Session


@pytest.fixture(scope="module")
def codecs():
    codec = TypeCodec(Session().checker, "int")
    return {key: codec for key in ("x", "input", "derived", "hole", "constant")}


def snapshot(base):
    return (
        base.sources,
        base.facts,
        base.unknowns,
        base.retracted,
        base.journal,
        base._next_source_id,
        base.conflicts,
    )


def scenario():
    base = KnowledgeBase(conflict_checker=ConflictChecker(("x",), policy="best-support"))
    first = base.observe("input", 4, "input sensor")
    base.estimate("x", 3, "model", 0.6)
    base.observe("x", 7, "sensor")
    base.derive("derived", 8, "method text must never execute", ["input"])
    base.unknown("hole", "not yet known")
    base.retract_source(next(first.provenance.observations()), "withdrawn input")
    base.derive("constant", 9, "program constant", [])
    base.replace_observation("x", 6, "corrected sensor", "correction")
    return base


def test_json_and_sqlite_replay_all_axes_and_exact_history(tmp_path, codecs):
    base = scenario()
    before = snapshot(base)
    encoded = export_json(base, codecs)
    assert snapshot(import_json(encoded, codecs)) == before
    assert snapshot(base) == before
    path = tmp_path / "knowledge.sqlite"
    with SQLiteStore(path, codecs) as store:
        store.save(base)
        store.save(base)
        assert snapshot(store.load()) == before
        assert store.export_json() == encoded
    with SQLiteStore(path, codecs) as store:
        resumed = store.load()
        assert resumed.observe("x", 12, "next") == base.observe("x", 12, "next")
        store.save(resumed)
        assert snapshot(store.load()) == snapshot(base)


def test_nominal_records_options_lists_and_large_integers_roundtrip():
    session = Session()
    session.load("type box = { count : int option; items : int list }")
    codec = TypeCodec(session.checker, "box")
    base = KnowledgeBase()
    base.observe("box", session.eval("{ count = Some 3; items = [1; 2] }").value, "source")
    assert snapshot(import_json(export_json(base, {"box": codec}), {"box": codec})) == snapshot(
        base
    )
    integer = TypeCodec(session.checker, "int")
    base = KnowledgeBase()
    base.observe("x", 10**80 + 17, "exact integer")
    assert import_json(export_json(base, {"x": integer}), {"x": integer}).value("x") == 10**80 + 17


def test_invariant_bindings_are_required_and_never_executed_by_replay(tmp_path, codecs):
    calls = []

    def accepts(facts):
        calls.append(facts)
        return facts[0].value > 0

    checker = ConflictChecker(invariants=(Invariant("positive", ("x",), accepts),))
    base = KnowledgeBase(conflict_checker=checker)
    base.observe("x", -1, "sensor")
    encoded = export_json(base, codecs)
    assert not calls
    with pytest.raises(JournalError, match="host bindings"):
        import_json(encoded, codecs)
    with SQLiteStore(tmp_path / "invariants.sqlite", codecs, checker=checker) as store:
        store.save(base)
        loaded = store.load()
        assert not calls and loaded.facts == base.facts
        assert loaded.conflicts.coherence == "conflict" and len(calls) == 1
        base.conflict_checker = replace(checker, policy="best-support")
        store.checker = base.conflict_checker
        store.save(base)
        assert store.load().conflict_checker == base.conflict_checker
    with pytest.raises(JournalError, match="does not match"):
        import_json(encoded, codecs, checker=ConflictChecker(("x",)))


def test_invalid_file_has_exact_value_path_and_leaves_existing_store_unchanged(tmp_path, codecs):
    base = scenario()
    bad = to_document(base, codecs)
    bad["events"][0]["fact"]["value"] = "not an integer"
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(bad))
    with SQLiteStore(tmp_path / "valid.sqlite", codecs) as store:
        store.save(base)
        before = store.export_json()
        with pytest.raises(JournalError) as caught:
            store.import_file(path)
        assert caught.value.path == "$.events[0].fact.value"
        assert store.export_json() == before


def test_schema_and_semantic_errors_have_paths(codecs):
    document = to_document(scenario(), codecs)
    cases = [
        (lambda d: d["sources"][0].update(kind="invented"), ContractError, "$.sources[0].kind"),
        (lambda d: d["events"][0].update(seq=2), JournalError, "$.events[0].seq"),
        (lambda d: d["sources"].append(d["sources"][0]), JournalError, "$.sources"),
        (lambda d: d["events"][0].update(key="different"), JournalError, "$.events[0].key"),
        (
            lambda d: d["events"][0]["fact"].update(provenance={"op": "obs", "id": "missing"}),
            JournalError,
            "$.events[0].fact.provenance",
        ),
    ]
    for edit, error, path in cases:
        bad = deepcopy(document)
        edit(bad)
        with pytest.raises(error) as caught:
            from_document(bad, codecs)
        assert path in str(caught.value)
    with pytest.raises(JournalError) as caught:
        from_document(document, {})
    assert caught.value.path == "$.events[0].fact.type"
    bad = deepcopy(document)
    bad["events"][0]["fact"]["type"]["name"] = "bool"
    with pytest.raises(JournalError) as caught:
        from_document(bad, codecs)
    assert caught.value.path == "$.events[0].fact.type"


@pytest.mark.parametrize(
    "encoded",
    [
        '{"nested":{"duplicate":1,"duplicate":2}}',
        '{"nested":NaN}',
        '{"nested":Infinity}',
        '{"nested":1e400}',
        '{"unfinished":',
    ],
)
def test_duplicate_nonfinite_and_malformed_json_is_rejected(encoded, codecs):
    with pytest.raises(JournalError) as caught:
        import_json(encoded, codecs)
    assert caught.value.path.startswith("$")
    if "duplicate" in encoded:
        assert caught.value.path == '$["nested"]["duplicate"]'


def test_unjournaled_changes_are_not_silently_discarded(codecs):
    base = scenario()
    base.facts["hole"] = Fact("hole", 99, obs("axiome"), "unlogged insertion")
    with pytest.raises(JournalError, match="not represented"):
        export_json(base, codecs)


def test_append_only_prefix_and_source_identity_are_enforced(tmp_path, codecs):
    base = scenario()
    with SQLiteStore(tmp_path / "journal.sqlite", codecs) as store:
        store.save(base)
        before = store.export_json()
        with pytest.raises(JournalError, match="stored prefix"):
            store.save(KnowledgeBase())
        source_id = next(iter(base.sources))
        base.sources[source_id] = replace(base.sources[source_id], origin="altered history")
        with pytest.raises(JournalError, match="cannot be changed"):
            store.save(base)
        assert store.export_json() == before
    with sqlite3.connect(tmp_path / "journal.sqlite") as db:
        for operation in ("UPDATE events SET payload=payload", "DELETE FROM events"):
            with pytest.raises(sqlite3.IntegrityError, match="append-only"):
                db.execute(operation)


def test_sql_failure_mid_append_rolls_back_events_and_metadata(tmp_path, codecs):
    path = tmp_path / "rollback.sqlite"
    base = scenario()
    with SQLiteStore(path, codecs) as store:
        store.save(base)
        before = store.export_json()
        reject_seq = len(base.journal) + 2
        with sqlite3.connect(path) as db:
            db.execute(
                f"CREATE TRIGGER reject_test BEFORE INSERT ON events WHEN NEW.seq={reject_seq} "
                "BEGIN SELECT RAISE(ABORT, 'injected database failure'); END"
            )
        base.observe("input", 1, "first addition")
        base.observe("hole", 2, "second addition")
        with pytest.raises(sqlite3.IntegrityError, match="injected"):
            store.save(base)
        assert store.export_json() == before


def test_nonempty_v1_migration_preserves_history_and_adds_guards(tmp_path, codecs):
    path = tmp_path / "legacy.sqlite"
    base = scenario()
    with SQLiteStore(path, codecs) as store:
        store.save(base)
        before = store.export_json()
    with sqlite3.connect(path) as db:
        db.execute("DROP TRIGGER journal_no_update")
        db.execute("DROP TRIGGER journal_no_delete")
        db.execute("PRAGMA user_version=1")
    with SQLiteStore(path, codecs) as store:
        assert store.export_json() == before
        base.observe("hole", 3, "after migration")
        store.save(base)
        assert snapshot(store.load()) == snapshot(base)
    with sqlite3.connect(path) as db:
        assert db.execute("PRAGMA user_version").fetchone()[0] == SQLITE_VERSION
        with pytest.raises(sqlite3.IntegrityError):
            db.execute("DELETE FROM events")


def test_unknown_sqlite_versions_and_unversioned_user_data_are_not_overwritten(tmp_path, codecs):
    for version in (0, 999):
        path = tmp_path / f"foreign-{version}.sqlite"
        with sqlite3.connect(path) as db:
            db.execute("CREATE TABLE user_data (value TEXT)")
            db.execute("INSERT INTO user_data VALUES ('preserve')")
            db.execute(f"PRAGMA user_version={version}")
        with pytest.raises(JournalError):
            SQLiteStore(path, codecs)
        with sqlite3.connect(path) as db:
            assert db.execute("SELECT value FROM user_data").fetchone()[0] == "preserve"


def test_source_ids_cannot_collide_with_imported_or_withdrawn_identifiers():
    base = KnowledgeBase(sources={"obs-1": Source("obs-1", "observation", "existing")})
    base.retract_source("obs-2", "reserved withdrawn identifier")
    fact = base.observe("x", 1, "new")
    assert next(fact.provenance.observations()) == "obs-3"
    assert base.sources["obs-1"].origin == "existing"


def test_source_counter_cannot_regress_in_an_existing_store(tmp_path, codecs):
    base = scenario()
    with SQLiteStore(tmp_path / "counter.sqlite", codecs) as store:
        store.save(base)
        before = store.export_json()
        base._next_source_id = 1
        with pytest.raises(JournalError) as caught:
            store.save(base)
        assert caught.value.path == "$.next_source_id"
        assert store.export_json() == before


def test_import_does_not_invent_invalidated_unknown_snapshots(codecs):
    document = to_document(scenario(), codecs)
    event = next(event for event in document["events"] if event["kind"] == "invalidated")
    event["unknown"] = None
    with pytest.raises(JournalError, match="snapshots do not match"):
        from_document(document, codecs)


def test_empty_database_requires_a_save_and_invalid_utf8_is_localized(tmp_path, codecs):
    bad = tmp_path / "invalid.json"
    bad.write_bytes(b"\xff")
    with SQLiteStore(tmp_path / "empty.sqlite", codecs) as store:
        with pytest.raises(JournalError, match="no journal saved"):
            store.load()
        with pytest.raises(JournalError, match="invalid UTF-8"):
            store.import_file(bad)


@settings(max_examples=30, deadline=None)
@given(st.lists(st.tuples(st.integers(-9, 9), st.booleans()), max_size=12))
def test_generated_journal_replay_is_exact_without_mutating_the_original(steps):
    codec = TypeCodec(Session(prelude=False).checker, "int")
    base = KnowledgeBase(conflict_checker=ConflictChecker(("x",), policy="best-support"))
    for value, revise in steps:
        if revise and "x" in base.facts:
            base.replace_observation("x", value, "revised", "correction")
        else:
            base.observe("x", value, "observer")
    before = snapshot(base)
    loaded = import_json(export_json(base, {"x": codec}), {"x": codec})
    assert snapshot(loaded) == before and snapshot(base) == before
