---
title: "HYP-090 · Scénario MVP principal : plaque de bout en bout"
lane: todo
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P0 · L · Phase 8 — Stabilisation · dépend de HYP-054, HYP-052, HYP-055, HYP-063, HYP-082"
priority: P0
tags: [dsl, estimateurs, exemple, moteur-symbolique, mvp, python, solveurs]
---

## Conversation

### user

**Ticket** HYP-090 · **Priorité** P0 · **Taille** L · **Epic** Phase 8 — Stabilisation · **Dépend de** HYP-054, HYP-052, HYP-055, HYP-063, HYP-082 · **Labels** python, exemple

#### Contexte

§16.2 : « Crée une plaque de 120 × 80 mm, estime son épaisseur, vérifie sa validité et exporte sa géométrie. » Dix étapes.

#### Tâches proposées

- Enchaîner transcription, compilation, normalisation des dimensions, estimation, résolution, validation, commande d'export, résultat JSON.
- Actionneur logiciel d'export de géométrie (fichier).
- Trace et métriques enregistrées.

#### Critères d'acceptation

- Test de bout en bout avec réponse LLM enregistrée.
- Chaque étape du §16.2 est identifiable dans la trace et la provenance.

#### Fichiers concernés

- `examples/mechanics/`
- `tests/e2e/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`
