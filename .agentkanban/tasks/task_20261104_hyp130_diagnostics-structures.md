---
title: "HYP-130 · Diagnostics structurés du compilateur (JSON)"
lane: qa
created: 2026-11-04T08:56:00+01:00
updated: 2026-11-04T14:55:00+01:00
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

### agent

Fait (commit `613cacc`, plus la section `TECHNICAL.md` « Diagnostics structurés (HYP-130) », embarquée par erreur dans le commit `f87d00e` de HYP-040 qui a ajouté tout `TECHNICAL.md`) :

- `src/hypomnesis/language/errors.py` : `stage_id` stable par classe (`syntax`, `name`, `type`, `runtime`, `error` par défaut → toute sous-classe de `HypomnesisError`, par ex. celle de HYP-137, se rend sans modification), `HypomnesisError.to_diagnostic(filename)`, `diagnostics_document`, constantes `DIAGNOSTICS_SCHEMA_ID`/`DIAGNOSTICS_VERSION`. `Span` n'a pas changé (il porte déjà les fins).
- `src/hypomnesis/contracts/schemas/diagnostics-1.0.0.json` (chargé automatiquement par `SchemaRegistry`).
- `src/hypomnesis/cli.py` : `check --format text|json` (`CheckFormat`) et `--langage DOSSIER` ; en `json`, stdout ne contient que le document ; texte et codes de sortie inchangés.
- `tests/unit/test_diagnostics.py` (15 tests : syntaxe, type, champ inconnu avec `languages/mecanique`, programme correct, texte inchangé, sous-classe inconnue, schéma). Tests passés : `test_diagnostics.py`, `test_cli_contract.py`, `tests/contracts`, et `validate.sh rapide` vert.
- Notes ajoutées aux fiches HYP-132 et HYP-133 (format à consommer).

Écarts / vigilance :

- Étendues approximées (documentées dans `TECHNICAL.md`) : erreur de syntaxe = début + 1 colonne (`parser._convert_error`) ; champ inconnu = l'expression enregistrement entière (`infer._check_fields`, pas d'étendue du nom de champ dans l'AST). Les affiner changerait le rendu texte : à traiter dans un ticket à part si souhaité.
- Le schéma laisse `stage` ouvert (motif) plutôt qu'une énumération, pour admettre de nouvelles étapes sans changer de version majeure.
- **`validate.sh complet` n'est PAS vert au moment du rendu**, à cause du travail en cours de HYP-137 (hors de mon périmètre) : ruff `RUF007` et 6 erreurs Pyright dans `src/hypomnesis/language/docs.py`, et `tests/unit/test_language_docs.py::test_underscore_names_and_their_members_need_no_description` en échec. Lean et audit des axiomes sont verts. Reste à faire : relancer `./scripts/validate.sh complet` une fois HYP-137 stabilisé ; si tout est vert, mettre cette fiche en `qa` (la case finale de la checklist est restée décochée pour cette raison). Fiche laissée en `doing`.
- J'ai écrit, par erreur de méthode, les notes HYP-132/133 via un script Python au lieu de l'outil d'édition ; le résultat est correct.

### user
