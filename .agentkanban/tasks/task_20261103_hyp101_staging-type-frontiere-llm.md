---
title: "HYP-101 · Code typé `⇑A` pour la frontière LLM"
lane: hypothese
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-04T19:36:05+01:00
description: "P3 · L · Niveau M3 (méta-métamodèle) · dépend de HYP-081, HYP-012"
priority: P3
tags: [architecture, compilateur, llm, metalangage, python]
---

## Conversation

### user

**Ticket** HYP-101 · **Priorité** P3 · **Taille** L · **Epic** Niveau M3 (méta-métamodèle) · **Dépend de** HYP-081, HYP-012 · **Labels** python

#### Contexte

§5.4 de `docs/architecture/m3-metalangage.md` : une sortie LLM est de la syntaxe non typée ; seul l'élaborateur produit du code typé `⇑A`, et seul ce code peut être épissé. Le pipeline du §14.3 devient une chaîne de modalités.

#### Tâches proposées

- Type `Syntax.t` (non typé) et `'a code` (typé) ; `elaborate : Syntax.t -> ('a code, diagnostic) result`.
- Rendre impossible la construction de `'a code` hors de l'élaborateur.

#### Critères d'acceptation

- Aucun chemin, dans l'API, ne mène d'une chaîne LLM à l'exécution sans passer par `elaborate` (vérifié par revue et test).

#### Fichiers concernés

- `src/hypomnesis/llm/`
- `src/hypomnesis/language/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`

### agent

Reclassement demandé par l'utilisateur : `todo` → `hypothese`. Le staging
modal par code typé reste une piste de l'ADR 0006 proposée, pas un engagement
sur cette API. L'obligation existante de vérifier les programmes avant
exécution reste inchangée. Priorité et dépendances conservées.

### user
