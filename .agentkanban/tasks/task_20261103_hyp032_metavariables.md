---
title: "HYP-032 · Métavariables : inconnues explicites et contraintes"
lane: qa
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P1 · M · Phase 2 — Moteur épistémique · dépend de HYP-030"
priority: P1
tags: [epistemique, moteur-symbolique, python]
---

## Conversation

### user

**Ticket** HYP-032 · **Priorité** P1 · **Taille** M · **Epic** Phase 2 — Moteur épistémique · **Dépend de** HYP-030 · **Labels** python

#### Contexte

§4.2 et §4.4 de `docs/architecture/m3-metalangage.md` : une valeur inconnue est une métavariable `?x : A`. Estimateurs, solveurs et générateurs la résolvent ; l'épaisseur de la plaque du scénario MVP en est le premier exemple.

#### Tâches proposées

- Représentation `MetaVar(id, type, constraints)` et état de résolution (non résolue, proposée avec grade, résolue).
- API : `propose(meta, value, grade, provenance)`, `resolve`, `conflict`.
- Interdire qu'une métavariable soit utilisée comme valeur concrète sans résolution (erreur explicite).

#### Critères d'acceptation

- Tests : proposition par deux sources, sélection de la meilleure par le support, conflit détecté si incompatibles.

#### Fichiers concernés

- `src/hypomnesis/epistemics/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`

### agent

HYP-005 adopte les trois axes (spécification v0.3 §7.1). `Unknown` appartient
à l'existence : métavariable non résolue, jamais valeur sentinelle.
Chaque proposition conserve son support et sa provenance ; une inconnue
sans proposition n'a pas de support concret inventé. La sélection par support
ne supprime pas le constat d'incompatibilité sur l'axe de cohérence.

### user

### agent

Implémentation prévue : métavariable persistante avec identifiant, TypeCodec
fermé fourni par l'hôte et contraintes pures nommées. Chaque proposition
capture une valeur immuable, son support et sa provenance. Les opérations
renvoient un nouvel état, sans modifier les propositions antérieures.

Arbitrage conservateur : best sélectionne le meilleur support, mais refuse
une égalité de supports incompatibles ; resolve refuse tout conflit sans
choix explicite d'une proposition. Même après ce choix, l'axe Conflict reste
visible tant que les propositions incompatibles restent présentes. Ajouter
une proposition rouvre la résolution. Aucune valeur concrète ni aucun grade
ne seront inventés pour une inconnue non résolue.

### user

### agent

Implémentation vérifiée dans `epistemics/metavariables.py` : type fermé via
TypeCodec, contraintes nommées pures, propositions et résolution persistantes.
propose conserve les instantanés Fact, support et provenance. best préfère
le support le plus fort sans arbitrer silencieusement les égalités incompatibles.
resolve exige un choix explicite en présence de conflit ; ce choix ne masque
pas l'axe de cohérence. Toute proposition nouvelle rouvre la résolution.

La lecture concrète avant résolution lève UnresolvedMetaVar ; aucun grade
n'est inventé pour le trou. Type, contraintes, grades et indices de choix
sont contrôlés. Les erreurs ne modifient pas les états précédents.
Les grades de proposition restent des jugements hôte, non une promotion
automatique des faits de KnowledgeBase ; cette frontière est documentée.

23 tests ajoutés : deux sources, meilleurs supports, conflits à tous grades,
égalité ambiguë, choix explicite, réouverture, types nominaux, contraintes,
erreurs et propriété générée du meilleur support. Guide connaissances et
TECHNICAL actualisés ; aucun changement de Core IR ni nouvelle preuve revendiquée.

`./scripts/validate.sh complet` est vert : 866 tests moteur, 77 Codegen,
linters, Pyright, contrats, Kanban, Lean et audit des axiomes.
Passage en QA ; done reste une décision humaine.

### user
