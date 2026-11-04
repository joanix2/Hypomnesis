---
title: "HYP-103 · Lean F7 : modèles de théories et substituabilité"
lane: hypothese
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-04T19:36:05+01:00
description: "P3 · L · Vérification formelle (Lean) · dépend de HYP-046, HYP-102"
priority: P3
tags: [architecture, lean, metalangage, moteur-symbolique, recherche]
---

## Conversation

### user

**Ticket** HYP-103 · **Priorité** P3 · **Taille** L · **Epic** Vérification formelle (Lean) · **Dépend de** HYP-046, HYP-102 · **Labels** lean, recherche

#### Contexte

Hypothèses H1, H3, H6 : deux modèles d'une même théorie sont interchangeables pour tout programme écrit contre la théorie.

#### Tâches proposées

- Formaliser théories, modèles et morphismes de théories.
- Prouver : un programme écrit contre une théorie a le même résultat observable dans deux modèles qui satisfont les mêmes lois, modulo ces lois.

#### Critères d'acceptation

- Théorèmes sans `sorry`, ajoutés à l'audit.

#### Fichiers concernés

- `formal/Hypomnesis/Meta/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`

### agent

Reclassement demandé par l'utilisateur : `todo` → `hypothese`. Ce ticket
porte les hypothèses H1/H3/H6 sur les modèles et leur substituabilité,
conditionnées au prototype méta encore proposé. Priorité et dépendances
conservées ; le théorème envisagé reste à préciser et à établir.

### user
