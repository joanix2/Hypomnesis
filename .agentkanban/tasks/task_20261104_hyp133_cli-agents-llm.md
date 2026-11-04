---
title: "HYP-133 · CLI utilisable par les agents LLM"
lane: todo
created: 2026-11-04T08:56:00+01:00
updated: 2026-11-04T08:56:00+01:00
description: "P1 · S · Outillage et visualisation · dépend de HYP-080, HYP-130"
---

## Conversation

### user

**Ticket** HYP-133 · **Priorité** P1 · **Taille** S · **Epic** Outillage et visualisation · **Dépend de** HYP-080, HYP-130 · **Labels** python, llm, outillage

#### Contexte

Un agent doit pouvoir découvrir un langage, vérifier un programme et le simuler sans analyser du texte destiné à un humain. HYP-080 fournit `describe` ; ce ticket rend l'ensemble des commandes homogène.

#### Tâches proposées

- Sortie JSON stable et versionnée pour `describe`, `check` et l'exécution en `simulate` ou `dry-run`.
- Codes de retour documentés ; aucune invite interactive ; données sur stdout et journaux sur stderr.
- Documentation courte destinée aux agents.

#### Critères d'acceptation

- Un programme peut être découvert, écrit, corrigé et simulé en n'utilisant que ces sorties JSON ; un test de bout en bout le vérifie.
- Chaque sortie est validée par son JSON Schema.

#### Fichiers concernés

- `src/hypomnesis/cli.py`
- `TECHNICAL.md`

#### Références

- À coordonner avec HYP-006 (migration vers Typer)
- Conventions et définition de fini : `.agentkanban/memory.md`

### agent

Note (HYP-130) : le format de diagnostic à consommer est le contrat `diagnostics/1.0.0` (`src/hypomnesis/contracts/schemas/diagnostics-1.0.0.json`), produit par `hypomnesis check --format json [--langage DOSSIER]` ou, en Python, par `HypomnesisError.to_diagnostic(fichier)` + `diagnostics_document([...])` (`hypomnesis.language.errors`). Positions 1-based, fin exclusive, `null` sans étendue ; `stage` ∈ `syntax|name|type|runtime|error`. Limites d'étendue : voir `TECHNICAL.md` § « Diagnostics structurés ».

### user
