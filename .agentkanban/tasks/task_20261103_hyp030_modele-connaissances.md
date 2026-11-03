---
title: "HYP-030 · Modèle de données des connaissances"
lane: todo
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P0 · M · Phase 2 — Moteur épistémique · dépend de HYP-002"
---

## Conversation

### user

**Ticket** HYP-030 · **Priorité** P0 · **Taille** M · **Epic** Phase 2 — Moteur épistémique · **Dépend de** HYP-002 · **Labels** python

#### Contexte

§7 du cahier des charges et §4.2–4.3 de `docs/architecture/m3-metalangage.md`. Une connaissance est un fait (valeur typée d'un concept) avec une provenance. Les statuts se lisent selon trois axes : existence (connu ou métavariable), support (`Observed` ⊑ `Estimated` ⊑ `Defaulted` ⊑ `Hypothesis`) et cohérence. Si HYP-005 rejette cette décomposition, revenir aux sept statuts de la v0.2.

#### Tâches proposées

- Créer `src/hypomnesis/epistemics/knowledge.py` : structures immuables `Fact`, `Observation`, identifiants stables.
- Représenter `Unknown` par une métavariable (voir HYP-032) et non par une valeur sentinelle.
- Sérialisation JSON (schéma versionné dans `contracts/schemas/`).

#### Critères d'acceptation

- Structures gelées, testées ; aller-retour JSON validé par schéma.
- Docstring reliant chaque statut du §7.1 à sa représentation.

#### Fichiers concernés

- `src/hypomnesis/epistemics/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- `docs/architecture/m3-metalangage.md`
- Conventions et définition de fini : `.agentkanban/memory.md`
