---
title: "HYP-033 · Révision des connaissances et journal d'événements"
lane: qa
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P0 · M · Phase 2 — Moteur épistémique · dépend de HYP-031"
priority: P0
tags: [epistemique, moteur-symbolique, python]
---

## Conversation

### user

**Ticket** HYP-033 · **Priorité** P0 · **Taille** M · **Epic** Phase 2 — Moteur épistémique · **Dépend de** HYP-031 · **Labels** python

#### Contexte

§7.3 : identifier les dépendants, invalider, recalculer, conserver l'historique, signaler les contradictions. Avec la provenance en semi-anneau, retirer une observation revient à la substitution `x ↦ 0` (P10, P11).

#### Tâches proposées

- Journal en ajout seul : `Observed`, `Retracted`, `Replaced`, `Derived`, `Revised`.
- Index inverse observation → conclusions (variables des termes de provenance).
- Révision incrémentale : recalculer uniquement les conclusions qui mentionnent l'observation.

#### Critères d'acceptation

- Test : révision incrémentale et recalcul complet donnent le même état (sur des scénarios générés).
- Aucune entrée du journal n'est jamais modifiée ni supprimée.

#### Fichiers concernés

- `src/hypomnesis/epistemics/revision.py`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`

### agent

Référence adoptée par HYP-005 : spécification v0.3 §7.1–7.3.
Les noms `Observed` et `Derived` du journal sont des événements historiques,
pas des statuts exclusifs des connaissances. La révision conserve séparément
existence, support et cohérence ; OBJ-11 exige des preuves, sans déclarer
déjà établie la correction de cet algorithme (HYP-036).

### user

objectif finir les P0

### agent

Lot P0 HYP-031 → HYP-033 traité directement, sans sous-agent. Réutilisation
de la base existante : index inverse reconstruit depuis les provenances pour
tolérer les insertions historiques par l'hôte ; seules les conclusions
candidates sont évaluées. Référence exhaustive indépendante et retraits
successifs générés pour vérifier l'équivalence.

Le journal expose désormais un tuple d'événements gelés et conserve les faits
remplacés ou invalidés. `replace_observation` valide d'abord, rétracte la source
ancienne et signale les conclusions devenues inconnues ; aucune méthode
textuelle n'est exécutée implicitement. Le moteur de règles devra les dériver
à nouveau. Les sources retirées ne contribuent plus au support ou à la
confiance des dérivations alternatives survivantes.

Validation complète verte : **842 tests** (765 cœur, 77 Codegen), linters,
types, schémas, build/audit Lean et vérificateur de certificats. Les cinq
nouveaux tests de révision couvrent les scénarios générés, les retraits
successifs, les alternatives et l'historique protégé. Le lot ne prouve pas
encore HYP-036 : c'est une validation Python, pas une preuve de l'algorithme.
Passage de HYP-031 et HYP-033 en QA ; l'objectif global de finir les P0 reste
ouvert, les autres tickets ne sont pas déclarés terminés.

### user
