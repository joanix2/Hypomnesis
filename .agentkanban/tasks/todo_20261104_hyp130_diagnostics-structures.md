---
title: "HYP-130 · TODO"
lane: qa
created: 2026-11-04T14:30:00+01:00
updated: 2026-11-04T18:19:29+01:00
description: "Checklist de HYP-130"
priority: P1
tags: [compilateur, llm, metalangage, outillage, python]
---

# Iteration 1

État des lieux : `Span` porte déjà `line, column, end_line, end_column` (`language/errors.py`) et chaque erreur a un attribut `stage` (`syntax error`, `type error`, `name error`, `runtime error`). Il reste à les sérialiser. `hypomnesis check` n'a pas de canal d'avertissements (HYP-010 l'ajoutera : prévoir la gravité `warning` dans le schéma dès maintenant). Sans GPU.

Fichiers : `src/hypomnesis/language/errors.py`, `src/hypomnesis/cli.py`, `src/hypomnesis/contracts/schemas/diagnostics-1.0.0.json` (nouveau), `tests/unit/test_diagnostics.py` (nouveau). Éviter tout autre changement de `cli.py` en parallèle (HYP-010, HYP-137).

Mise à jour 2026-11-04 : depuis HYP-006, `cli.py` est écrit avec **Typer** : `--format` et `--langage` s'ajoutent comme paramètres annotés de la fonction `check` (`--format` en `Enum` texte|json), et `main(argv) -> int` doit continuer à rendre un entier. HYP-016 ajoute aussi une option à `benchmark-llm` dans ce fichier : coordonner les commits.

- [x] Vérifier la position de fin de l'étendue pour chaque étape (syntaxe Lark, nommage, typage, champ inconnu) ; lister dans le ticket celles où `end_*` est approximé (parser.py ligne ~72 : fin = début + 1)
- [x] Ajouter `HypomnesisError.to_diagnostic(filename)` → dict : `stage` (`syntax`|`name`|`type`|`runtime`, identifiant stable distinct du libellé affiché), `severity`, `message`, `file`, `line`, `column`, `end_line`, `end_column`
- [x] Schéma JSON Schema 2020-12 `diagnostics-1.0.0.json` (`$id` sous `https://schemas.example.org/hypomnesis/…`, `version`, `diagnostics: [...]`, `additionalProperties: false`) ; constante d'identifiant exportée
- [x] Vérifier que `SchemaRegistry.with_builtin_schemas()` charge le nouveau schéma (test de contrats existant inchangé)
- [x] CLI : `hypomnesis check --format json|text` (défaut `text`) ; en `json`, imprimer sur stdout un document conforme, code de retour identique (0/1)
- [x] CLI : option `--langage DOSSIER` : charger le langage M2 (`engine.language.load_language`) avant de vérifier les fichiers M1 dans son contexte ; erreur claire si le dossier n'est pas un langage
- [x] Sortie texte actuelle strictement inchangée (tests `test_examples.py`, `test_certificate.py` inchangés)
- [x] Tests : une erreur de syntaxe, une erreur de type et un champ inconnu (programme M1 + `--langage languages/mecanique`) → JSON valide contre le schéma, avec la bonne ligne et colonne
- [x] Test : programme correct → `{"version": ..., "diagnostics": []}` et code 0
- [x] Test : validation du document par `SchemaRegistry.issues` sur chaque cas
- [x] `docs/` : décrire le format (section dans `docs/language/` ou `TECHNICAL.md`) ; ajouter une note à HYP-132/133 sur le format à consommer
- [x] `./scripts/validate.sh complet`, commit en français, mettre la tâche en `qa`
