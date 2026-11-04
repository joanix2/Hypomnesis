---
title: "HYP-100 · Modalité graduée `[g]` dans le typeur"
lane: hypothese
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-04T19:36:05+01:00
description: "P2 · L · Niveau M3 (méta-métamodèle) · dépend de HYP-031"
priority: P2
tags: [architecture, compilateur, epistemique, metalangage, moteur-symbolique, python]
---

## Conversation

### user

**Ticket** HYP-100 · **Priorité** P2 · **Taille** L · **Epic** Niveau M3 (méta-métamodèle) · **Dépend de** HYP-031 · **Labels** python

#### Contexte

Étape 4 de `docs/architecture/m3-metalangage.md` (§5.3) : le support épistémique porté par les types. Une valeur `[Estimated] Length.t` combinée à `[Observed]` donne `[Estimated]` ; une action qui exige `[Observed]` refuse statiquement une estimation.

#### Tâches proposées

- Types gradués sur le treillis de support ; règles de typage (Granule, QTT) ; coercions `g ⊑ g'`.
- Interaction avec l'inférence HM : inférer les grades (contraintes de treillis).

#### Critères d'acceptation

- Exemples de la note M3 §5.3 acceptés et refusés comme indiqué.
- ADR rédigée.

#### Fichiers concernés

- `src/hypomnesis/language/typesystem/`

#### Références

- `docs/architecture/m3-metalangage.md`
- Conventions et définition de fini : `.agentkanban/memory.md`

### agent

Reclassement demandé par l'utilisateur : `todo` → `hypothese`. Porter les
grades dans le typeur reste une piste architecturale de l'ADR 0006 proposée ;
l'adoption des trois axes épistémiques ne vaut pas adoption de ce mécanisme.
Priorité et dépendances conservées ; aucune implémentation lancée.

### user
