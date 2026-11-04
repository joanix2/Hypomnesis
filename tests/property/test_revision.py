"""Incremental and full revision agree on generated bases (HYP-033)."""

from dataclasses import FrozenInstanceError

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from hypomnesis.epistemics.knowledge import Fact, KnowledgeBase
from hypomnesis.epistemics.provenance import obs
from hypomnesis.epistemics.revision import dependency_index, invalidated, recompute


@settings(deadline=None)
@given(
    st.lists(
        st.lists(st.integers(min_value=0, max_value=5), min_size=1, max_size=5),
        max_size=15,
    ),
    st.lists(st.integers(min_value=0, max_value=5), unique=True),
)
def test_incremental_revision_equals_full_recomputation(paths, removals):
    kb = KnowledgeBase()
    for i in range(6):
        kb.observe(f"input-{i}", i, f"sensor-{i}")
    sources = [kb.source_id(f"input-{i}") for i in range(6)]
    for i, alternatives in enumerate(paths):
        term = obs(sources[alternatives[0]])
        for choice in alternatives[1:]:
            term = term + obs(sources[choice]) * obs(sources[(choice + 1) % 6])
        kb.facts[f"output-{i}"] = Fact(f"output-{i}", i, term, "generated")
    original = dict(kb.facts)
    for removal in removals:
        before = kb.journal
        kb.retract_source(sources[removal], "generated retraction")
        assert kb.facts == recompute(original, kb.retracted)
        assert kb.journal[: len(before)] == before
        assert [e.seq for e in kb.journal] == list(range(1, len(kb.journal) + 1))


def test_journal_is_read_only_and_retains_replaced_and_invalidated_facts():
    kb = KnowledgeBase()
    old = kb.observe("x", {"items": [1]}, "sensor")
    kb.derive("y", 2, "double", ["x"])
    prefix = kb.journal
    kb.replace_observation("x", {"items": [3]}, "new sensor", "corrected")
    assert kb.journal[: len(prefix)] == prefix
    assert "y" not in kb.facts and "y" in kb.unknowns
    assert kb.value("x") == {"items": [3]}
    assert next(e for e in kb.journal if e.kind == "replaced").fact == old
    assert kb.journal[-1].kind == "revised"
    with pytest.raises(AttributeError):
        kb.journal.clear()
    with pytest.raises(AttributeError):
        kb.journal = ()
    with pytest.raises(FrozenInstanceError):
        kb.journal[0].kind = "changed"
    kb.journal[0].fact.value["items"].clear()
    assert kb.journal[0].fact.value == {"items": [1]}


def test_index_uses_original_sources_not_replaced_premise_keys():
    kb = KnowledgeBase()
    kb.observe("x", 1, "first")
    kb.derive("y", 2, "double", ["x"])
    old_source = kb.source_id("x")
    kb.observe("x", 3, "second")
    index = dependency_index(kb.facts)
    assert index[old_source] == frozenset({"y"})
    assert invalidated(kb.facts, {old_source}) == ["y"]


def test_surviving_alternative_recalculates_support_and_confidence():
    kb = KnowledgeBase()
    kb.observe("a", 1, "sensor")
    kb.estimate("b", 1, "model", 0.4)
    kb.facts["choice"] = Fact(
        "choice", 1, kb.facts["a"].provenance + kb.facts["b"].provenance, "alternative"
    )
    assert kb.confidence("choice") == 1
    kb.retract_source(kb.source_id("a"), "sensor lost")
    assert kb.confidence("choice") == 0.4
    assert kb.support("choice") == kb.support("b")


def test_replacing_observation_rejects_bad_input_without_changes():
    kb = KnowledgeBase()
    kb.observe("x", 1, "sensor")
    before = (dict(kb.facts), kb.journal, set(kb.retracted))
    with pytest.raises(ValueError):
        kb.replace_observation("x", object(), "sensor", "bad")
    assert before == (kb.facts, kb.journal, kb.retracted)
    kb.estimate("e", 2, "model", 0.5)
    with pytest.raises(ValueError):
        kb.replace_observation("e", 3, "sensor", "not an observation")
