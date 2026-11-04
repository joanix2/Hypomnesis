---
title: "HYP-060 · Effect IR et effets algébriques"
lane: qa
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T19:42:42+01:00
description: "P0 · L · Phase 5 — Effets et actionneurs · dépend de HYP-002"
priority: P0
tags: [effets, metalangage, moteur-symbolique, python, runtime]
---

## Conversation

### user

**Ticket** HYP-060 · **Priorité** P0 · **Taille** L · **Epic** Phase 5 — Effets et actionneurs · **Dépend de** HYP-002 · **Labels** python

#### Contexte

§10 et §6.3 de `docs/architecture/m3-metalangage.md` : un effet est une signature d'opérations ; un programme à effets est une valeur (un terme libre) ; seul le runtime l'interprète, via un handler. Le noyau reste pur (ADR 0003).

#### Tâches proposées

- Syntaxe des signatures d'effets et du type des calculs (`'a effect`), avec `return` et `bind` (§10.2).
- `ir/effect.py` : lecture de source, invocation de plugin, construction de commande, attente, vérification.
- Garantir statiquement qu'aucun terme pur n'exécute d'effet.

#### Critères d'acceptation

- Un programme qui décrit un mouvement de moteur s'évalue en une valeur inerte tant qu'aucun handler ne l'exécute.
- ADR sur la représentation des effets.

#### Fichiers concernés

- `src/hypomnesis/ir/effect.py`
- `src/hypomnesis/effects/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`

### agent

Implémenté : **les effets sont des valeurs du langage**, et les procédures sont des programmes Hypomnesis.

- **Bibliothèque standard (M3)** :
  - `Json.t` et la primitive pure `to_json` ;
  - `'a Effect.t` avec `Done`, `Observe`, `Act`, `Solve`, `Record`, `Retract`, `Note` ;
  - `return`, `bind` (une monade : `'a t -> ('a -> 'b t) -> 'b t`) et les opérations ;
  - l'opérateur `>>=`, la grammaire acceptant `m >>= fun x -> e`.
- **`engine/procedure.py`** : l'interpréteur, seule entité qui exécute.
  - **Capteurs** : seuls ceux que déclare le langage ; message validé (enveloppe puis contrat), fait **observé** ;
  - **Actions** : par le dispatcher (contrat, permission, contraintes, mode) ;
  - **Solveur** : solution revérifiée ;
  - **Connaissances** : enregistrées avec leur support (`Given`, `Estimated`, `Assumed`, `Derived` avec prémisses vérifiées), retraits ;
  - **Bornes** : nombre d'étapes limité.

  Un programme ne peut pas fabriquer une observation.
- Les procédures figées `constrained-design` et `feedback-loop` sont **supprimées** du moteur. Elles sont réécrites en Hypomnesis dans les langages :
  - `Plaque.concevoir` (l'estimateur est choisi par le programme M1) ;
  - `Plaque.concevoir_puis_mesurer` (révision par un pied à coulisse simulé) ;
  - `Ventilation.reguler` (boucle récursive, hypothèse explicite, réfutation).
- Le manifeste ne connaît plus qu'un type de procédure, `program` : point d'entrée, capteurs, actionneurs, environnement.

Tests :
- 23 tests de langages, dont les garde-fous : prémisses inexistantes, capteur non déclaré, point d'entrée qui n'est pas une procédure, procédure infinie arrêtée par le budget ;
- 4 tests unitaires de la bibliothèque (lois de la monade, inertie des procédures, `to_json`) ;
- le test d'architecture : toujours aucun domaine dans le moteur.

`./scripts/validate.sh complet` vert. Passée en `qa`.

### user
