---
title: "HYP-015 · Traces : remplacer le traceur maison par le SDK OpenTelemetry"
lane: qa
created: 2026-11-03T21:36:21+01:00
updated: 2026-11-04T14:50:00+01:00
description: "P1 · M · Fondations et gouvernance · dépend de HYP-002 · migration vers bibliothèque"
priority: P1
tags: [dette, observabilite, python]
---

## Conversation

### user

**Ticket** HYP-015 · **Priorité** P1 · **Taille** M · **Epic** Fondations et gouvernance · **Dépend de** HYP-002 · **Labels** python, observabilité, dette

#### Contexte

`src/hypomnesis/observability/trace.py` reproduit à la main une petite partie d'OpenTelemetry (spans imbriqués, attributs, statut). Le SDK officiel fournit la même chose, plus la propagation du contexte et l'export OTLP. Ce ticket remplace le traceur ; HYP-070 complète ensuite l'instrumentation et l'export vers un collecteur.

#### Tâches proposées

- Utiliser `opentelemetry-sdk` avec un exportateur en mémoire pour construire l'arbre de spans et l'export JSON des rapports M0.
- Conserver les noms de spans du §12.3 et les attributs actuels.
- Relier le `trace_id` OpenTelemetry au `trace_context` de l'enveloppe de message (§9.6).
- Garantir que désactiver la télémétrie ne change aucun résultat (ADR 0005).

#### Critères d'acceptation

- Les rapports M0 contiennent toujours l'arbre de spans, désormais produit par OpenTelemetry.
- Un test vérifie qu'un run avec et sans télémétrie donne les mêmes connaissances.
- Tous les tests existants passent sans modification de leurs attentes.
- `./scripts/validate.sh complet` vert.

#### Fichiers concernés

- `src/hypomnesis/observability/trace.py`
- `src/hypomnesis/engine/procedure.py`
- `pyproject.toml`

#### Références

- Ticket de coordination : HYP-007
- Conventions et définition de fini : `.agentkanban/memory.md` (« bibliothèques plutôt que code maison »)

### agent

HYP-015 implémenté : `Tracer` est désormais une façade au-dessus du SDK OpenTelemetry 1.45 ; `engine/procedure.py` est resté intact.

**Fait**
- `src/hypomnesis/observability/trace.py` réécrit : un `TracerProvider` propre à chaque `Tracer` (jamais de provider global), `SimpleSpanProcessor` + `InMemorySpanExporter`, `trace_id` fixé à la création par un générateur d'identifiants dédié, parent explicite (pile propre au `Tracer`, racine démarrée sur un contexte vide : aucun span d'un autre traceur n'est adopté). `span()`, `tree()`, `export()`, `trace_id`, `spans` conservés ; mêmes noms de spans et mêmes attributs ; mêmes clés dans `rapport.json`.
- Identifiants exportés en hexadécimal (trace 32, span 16 caractères) : format identique à l'ancien, donc aucun test modifié. Attributs non scalaires rendus par `repr`. Exception → `StatusCode.ERROR` (statut JSON `error`), puis relancée.
- Nouveau `trace_context(tracer)` : `traceparent` W3C pour l'enveloppe (§9.6), validé par `SchemaRegistry` contre `envelope-1.0.0.json`.
- `Tracer(enabled=False)` : `NoOpTracerProvider`, aucun span.
- Tests : `tests/unit/test_trace.py` (9 tests : format d'export, arbre et marque d'erreur, attributs, isolation entre traceurs, `trace_context`, conformité au schéma, run avec/sans télémétrie → mêmes connaissances, commandes, journal). `tests/integration/test_languages.py` passe sans modification.
- `TECHNICAL.md` : nouvelle section « Observabilité (HYP-015) ».

**Écarts et points de vigilance**
- Le test de caractérisation a été écrit avec la migration (pas exécuté contre l'ancien code, qui n'avait pas `trace_context`) ; il fixe le format d'export de l'ancien traceur.
- Les spans sont désormais exportés dans l'ordre de **début** (le SDK les termine dans l'ordre de fin) : tri explicite, ordre identique à l'ancien.
- La classe `Span` maison a disparu (aucun consommateur) ; `Tracer.span()` renvoie le `Span` OpenTelemetry.
- Hors d'un span, `trace_context` renvoie un identifiant de span nul et le drapeau `00` (accepté par le schéma, non valide au sens strict du W3C).
- « Relier le `trace_id` au `trace_context` de l'enveloppe » : la fonction existe ; aucun code ne construit encore d'enveloppe (le dispatcher n'en émet pas), le branchement relève de HYP-070 / de l'instrumentation.
- Pas d'export OTLP (HYP-070). `pyproject.toml` non touché.
- `./scripts/validate.sh complet` : tests, Lean, certificats OK ; le hook `pre-commit` signale un échec uniquement parce que le hook `pyright` (0 erreur) « a modifié des fichiers » : il s'agit des fiches kanban d'autres agents (HYP-006…) régénérées pendant leur travail en parallèle, pas de mes fichiers.

### user
