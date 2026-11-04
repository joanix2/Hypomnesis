---
title: "HYP-038 · Exposer les connaissances dans le langage"
lane: qa
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P1 · M · Phase 2 — Moteur épistémique · dépend de HYP-030, HYP-033"
priority: P1
tags: [dsl, epistemique, metalangage, moteur-symbolique, python]
---

## Conversation

### user

**Ticket** HYP-038 · **Priorité** P1 · **Taille** M · **Epic** Phase 2 — Moteur épistémique · **Dépend de** HYP-030, HYP-033 · **Labels** python

#### Contexte

Les programmes Hypomnesis doivent pouvoir manipuler les connaissances (§2 OBJ-04, §5) sans effet de bord : lecture d'une base immuable passée en argument, construction de faits dérivés.

#### Tâches proposées

- Bibliothèque `Knowledge` (types et fonctions natives pures) : interroger, dériver, consulter la provenance et le support.
- Les primitives passent par le registre natif fermé (ADR 0003).
- Exemple `examples/knowledge/` sur la plaque.

#### Critères d'acceptation

- Un programme dérive un fait dont le support est calculé automatiquement (Estimated si une prémisse l'est).

#### Fichiers concernés

- `src/hypomnesis/stdlib/`
- `src/hypomnesis/runtime/natives.py`
- `examples/knowledge/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`

### agent

Référence adoptée par HYP-005 : spécification v0.3 §7.1. Exposer les axes
indépendamment ; `Derived` est une justification, son support vient des
prémisses. L'exemple d'une prémisse estimée reste valable sans supposer
l'absence de prémisses moins étayées. Conserver les primitives pures et le
registre fermé ; les démonstrations suivent désormais `demo/` (ADR 0011).

### user

### agent

Plan : exposer un instantané persistant passé explicitement à la bibliothèque
Knowledge, avec recherche optionnelle, valeur, provenance et support calculé
par les opérations de semi-anneau déjà définies dans le modèle.
Les dérivations conservent leurs prémisses et ne modifient pas la base initiale.

Choix d'implémentation plus simple que de nouvelles primitives opaques :
fonctions pures en Hypomnesis dans le prélude, types algébriques et records
existants, aucune nouvelle forme IR ni extension du registre natif. Un pont
hôte transforme KnowledgeBase en vue Json.t immuable ; les valeurs nominales
requièrent leur encodeur hôte explicite. L'observation du monde reste dans
Effect.Observe : une vue de données n'est pas une nouvelle autorité d'observation.
Tester différentiellement les lectures de provenance et fournir l'exemple plaque.

### user

### agent

Bibliothèque Knowledge ajoutée au prélude : base passée explicitement,
recherche et valeur optionnelles, provenance, support calculé et dérivation
persistante. Une conclusion issue d'une observation et d'une estimation
est automatiquement Estimated. Produits, alternatives, prémisses répétées
et sources retirées conservent leur sémantique ; les constantes sont Defaulted.
Une valeur connue mais Unsupported ne devient pas artificiellement Unknown.

Le pont hôte `epistemics.language.snapshot_value` capture une vue immuable
Json.t Knowledge.t ; les valeurs nominales requièrent un encodeur explicite.
Aucune mutation de KnowledgeBase, primitive de capteur ou nouvelle forme IR.
Les fonctions sont écrites en Hypomnesis plutôt que dans de nouveaux natifs,
suivant le choix de simplification annoncé ; le registre fermé reste inchangé.
Une vue de données n'est pas une attestation d'observation du monde.

Sept tests ajoutés dont une comparaison générée des lectures de provenance
avec Python, persistance, révision, inconnues, constantes et types nominaux.
L'exemple `demo/examples/knowledge/plaque.hyp` calcule sa surface dans une
fonction prenant la base en argument, avec support Estimated et entrée inchangée.
Guide connaissances et TECHNICAL actualisés.

`./scripts/validate.sh complet` est vert : 873 tests moteur, 77 Codegen,
linters, Pyright, contrats, Kanban, Lean et audit des axiomes.
La chaîne de certificats existante reste verte ; aucune nouvelle propriété
Lean n'est revendiquée pour la bibliothèque. Passage en QA ; done reste humain.

### user
