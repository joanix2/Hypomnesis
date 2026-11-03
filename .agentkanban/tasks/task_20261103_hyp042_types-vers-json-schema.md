---
title: "HYP-042 · Correspondance types Hypomnesis ↔ JSON Schema"
lane: todo
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P0 · L · Phase 3 — Extensions et contrats · dépend de HYP-041"
---

## Conversation

### user

**Ticket** HYP-042 · **Priorité** P0 · **Taille** L · **Epic** Phase 3 — Extensions et contrats · **Dépend de** HYP-041 · **Labels** python, contrats

#### Contexte

§13.4 : les signatures des extensions doivent permettre de générer ou de vérifier les contrats JSON Schema ; les correspondances entre types statiques, types JSON et concepts sont explicites.

#### Tâches proposées

- Définir la correspondance (ADR) : int, float, string, bool, unit, records, variants (objet étiqueté), listes, option.
- Générer un schéma depuis un type et vérifier la compatibilité entre une signature et un schéma déclaré.
- Encodage et décodage valeur ↔ JSON.

#### Critères d'acceptation

- Pour tout type supporté : `decode(encode(v)) == v` et `encode(v)` est conforme au schéma généré (test Hypothesis).
- Une signature incompatible avec le schéma du manifeste est refusée avant toute exécution.
- ADR rédigée.

#### Fichiers concernés

- `src/hypomnesis/contracts/`
- `docs/adr/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`
