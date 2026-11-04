---
title: "HYP-040 · Interfaces des capacités (Observer … Resolver)"
lane: qa
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-04T14:55:00+01:00
description: "P0 · M · Phase 3 — Extensions et contrats · dépend de HYP-002"
priority: P0
tags: [architecture, capacites, contrats, moteur-symbolique, python]
---

## Conversation

### user

**Ticket** HYP-040 · **Priorité** P0 · **Taille** M · **Epic** Phase 3 — Extensions et contrats · **Dépend de** HYP-002 · **Labels** python

#### Contexte

§6 : neuf interfaces génériques. Leur rôle type-théorique est décrit au §4.4 de `docs/architecture/m3-metalangage.md` (estimateur = proposer une métavariable, validateur = rendre un certificat, etc.).

#### Tâches proposées

- `src/hypomnesis/capabilities/` : un protocole typé par interface, indépendant du backend.
- Chaque appel rend un résultat structuré (valeur, certificat, diagnostic), jamais une exception brute.
- Docstrings reliant chaque interface au §6 et au §4.4 de la note M3.

#### Critères d'acceptation

- Pyright strict sur le module ; un plugin factice de chaque type passe les tests de conformité.

#### Fichiers concernés

- `src/hypomnesis/capabilities/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`

### agent

Implémenté (commit f87d00e) : `src/hypomnesis/capabilities/` (`result.py`, `protocols.py`, `safe.py`, `__init__.py`), `tests/unit/test_capabilities.py` (16 tests, un plugin factice par rôle, conformité statique par assignation typée, confinement des exceptions), section « Capacités » de `TECHNICAL.md`, note pour HYP-041. Checklist entièrement cochée.

Contenu : neuf `typing.Protocol` `runtime_checkable` (les neuf rôles du §6, identiques à l'énumération `role` du manifeste, vérifié par test) ; `Result[T]` immuable (`value`, `certificate`, `diagnostics`, `ok`) ; `Diagnostic` ; `Certificate` ; `guarded` (toute `Exception` d'un plugin devient un `Result` en échec `capability.raised`) ; `ROLES` / `roles_of`. Validator : refus = diagnostic d'erreur dont `data` porte le contre-exemple.

Écarts : (1) `pyproject.toml` interdit d'édition, donc Pyright strict via `# pyright: strict` en tête de chaque module (0 erreur sur `capabilities/` et le test). (2) `KnowledgeBase` est `Protocol[Fact]` (query/store) au lieu de `[In, Out]`.

Vérifié : ruff (check + format), Pyright et pytest sur mes fichiers ; `test_engine_contains_no_domain` passe ; `validate.sh rapide` : tests verts, seul ruff lint échoue.

Pas vert : `validate.sh complet` est ROUGE à cause du travail en cours d'autres agents, pas de ce ticket : ruff/Pyright sur `src/hypomnesis/language/docs.py` (HYP-130/137), tests `test_provenance_graph`, `test_benchmark`, `test_llm::test_an_undocumented_language_falls_back_on_its_source` (HYP-139/143). Reste : relancer `./scripts/validate.sh complet` une fois ces chantiers commités ; s'il est vert, passer cette fiche en `qa` (laissée en `doing`).

### user
