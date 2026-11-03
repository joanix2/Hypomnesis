---
title: "HYP-112 · DSL Applications : un langage pour construire des applications"
lane: todo
created: 2026-11-03T17:50:18+01:00
updated: 2026-11-03T17:50:18+01:00
description: "P2 · L · Instances de domaines · dépend de HYP-046, HYP-042, HYP-062 · idée à planifier"
---

## Conversation

### user

**Ticket** HYP-112 · **Priorité** P2 · **Taille** L · **Epic** Instances de domaines · **Dépend de** HYP-046, HYP-042, HYP-062 · **Labels** idée, dsl

#### Idée

Une instance de DSL pour décrire des applications : modèle de données, écrans et formulaires, workflows, rôles et permissions, API. On génère ensuite le code dans des technologies cibles.

#### Pistes de conception

- **Concepts** : entité et champs typés, relation, écran, formulaire, workflow (automate d'états : états, transitions, actions), rôle, permission, point d'API.
- **Génération de code comme morphisme de théories** (capacité `Transpiler`, note M3 §6.1) : la même description produit par exemple un backend FastAPI et un frontend React.
- **Contrats** : les formulaires et l'API dérivent leurs JSON Schema des types des entités (HYP-042). La validation côté client et côté serveur reste donc cohérente par construction.
- **Effets** : écritures en base, envoi de messages et déploiement passent par le pipeline de validation et de permissions des effets (HYP-062).

#### Propriétés prouvables envisagées

- Tout état d'un workflow est atteignable depuis l'état initial, et aucun état non final n'est bloquant.
- Toute transition et tout point d'API est protégé par au moins un rôle ; aucune donnée n'est accessible sans permission.
- Une migration de schéma préserve les données existantes (foncteurs de migration Δ, Σ, Π, note M3 §6.2).
- La génération de code préserve le sens : le code généré respecte les contrats de la description.

#### Questions ouvertes

- Quelles technologies cibles pour la génération ?
- Applications de gestion (formulaires et workflows) en priorité, ou périmètre plus large ?

#### Références

- `docs/architecture/m3-metalangage.md` (§6.1, §6.2)
- `docs/adr/0004-contrats-json-schema.md`
- Conventions : `.agentkanban/memory.md`

