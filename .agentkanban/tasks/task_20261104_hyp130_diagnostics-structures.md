---
title: "HYP-130 · Diagnostics structurés du compilateur (JSON)"
lane: todo
created: 2026-11-04T08:56:00+01:00
updated: 2026-11-04T08:56:00+01:00
description: "P1 · S · Outillage et visualisation · dépend de HYP-002"
---

## Conversation

### user

**Ticket** HYP-130 · **Priorité** P1 · **Taille** S · **Epic** Outillage et visualisation · **Dépend de** HYP-002 · **Labels** python, outillage, llm

#### Contexte

Le linter VS Code, le serveur MCP et les agents LLM ont tous besoin des erreurs du compilateur sous une forme exploitable par une machine. Aujourd'hui `hypomnesis check` ne produit que du texte. Ce ticket est le socle commun de HYP-132 et HYP-133.

#### Tâches proposées

- Option `hypomnesis check --format json` : étape (`syntax`, `type`…), message, fichier, ligne, colonne de début et de fin, gravité.
- Étendre `Span` si la fin de l'étendue n'est pas disponible à toutes les étapes.
- Publier le format comme contrat JSON Schema versionné (ADR 0004).
- Permettre de vérifier un programme M1 dans le contexte d'un langage M2 (`--langage`).

#### Critères d'acceptation

- Une erreur de syntaxe, de type et de champ inconnu donnent chacune un JSON conforme au schéma, avec la bonne position.
- La sortie texte actuelle ne change pas.
- `./scripts/validate.sh complet` vert.

#### Fichiers concernés

- `src/hypomnesis/cli.py`
- `src/hypomnesis/language/errors.py`
- `src/hypomnesis/contracts/schemas/`

#### Références

- Conventions et définition de fini : `.agentkanban/memory.md`

