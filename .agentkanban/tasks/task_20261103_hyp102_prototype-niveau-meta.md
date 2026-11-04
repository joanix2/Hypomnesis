---
title: "HYP-102 · Prototype du niveau méta (λΠ-modulo, `Desc`) en Lean"
lane: todo
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P3 · L · Niveau M3 (méta-métamodèle) · dépend de HYP-023, HYP-005"
priority: P3
tags: [architecture, lean, metalangage, recherche]
---

## Conversation

### user

**Ticket** HYP-102 · **Priorité** P3 · **Taille** L · **Epic** Niveau M3 (méta-métamodèle) · **Dépend de** HYP-023, HYP-005 · **Labels** lean, recherche

#### Contexte

Étape 5 de `docs/architecture/m3-metalangage.md` (§3.2, §6.6, §7) : noyau méta en λΠ-calcul modulo réécriture et univers de descriptions avec `⌜Desc⌝ : Desc` au niveau suivant (lévitation). Chantier de recherche.

#### Tâches proposées

- Formaliser en Lean les huit primitives du §7 de la note.
- Encoder la théorie `Mechanics` et la théorie des théories ; montrer `El ⌜M3⌝ ≅ M3` au niveau suivant.
- Rapport : ce qui est réellement utilisé par les domaines (pour dimensionner le noyau).

#### Critères d'acceptation

- Encodage vérifié par Lean ; rapport versionné dans `docs/architecture/`.

#### Fichiers concernés

- `formal/Hypomnesis/Meta/`

#### Références

- `docs/architecture/m3-metalangage.md`
- Conventions et définition de fini : `.agentkanban/memory.md`
