---
title: "HYP-023 · Lean F2 : polymorphisme dans les termes élaborés"
lane: todo
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P1 · L · Vérification formelle (Lean) · dépend de HYP-020"
---

## Conversation

### user

**Ticket** HYP-023 · **Priorité** P1 · **Taille** L · **Epic** Vérification formelle (Lean) · **Dépend de** HYP-020 · **Labels** lean

#### Contexte

L'inférence HM produit des schémas `∀ᾱ.τ`. Pour que le certificat reste vérifiable par un algorithme simple, il doit expliciter les abstractions et instanciations de types, à la manière de Système F restreint au rang 1 : on ne prouve pas l'algorithme W, on vérifie son résultat.

#### Tâches proposées

- Ajouter variables de type, `Λ` (généralisation au `let`) et instanciation explicite aux termes élaborés.
- Substitution de types et lemmes associés (préservation du typage par substitution).
- Étendre la sûreté, `typeOf` et ses preuves.

#### Critères d'acceptation

- Preuves sans `sorry`.
- `List.map` du prélude s'exprime et se type dans le fragment.

#### Fichiers concernés

- `formal/Hypomnesis/Core/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`
