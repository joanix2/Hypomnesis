---
title: "HYP-133 · CLI utilisable par les agents LLM"
lane: qa
created: 2026-11-04T08:56:00+01:00
updated: 2026-11-04T08:56:00+01:00
description: "P1 · S · Outillage et visualisation · dépend de HYP-080, HYP-130"
priority: P1
tags: [llm, outillage, python]
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

### agent

Plan / todo / implement du lot Mac approuvé, sans sous-agent ni LLM.
Prérequis HYP-080/130 en QA. Respecter l'ADR 0012 et le catalogue existant :
la découverte reste `hypomnesis-codegen decrire --format json`, sans
réintroduire les commandes LLM dans le noyau ni dupliquer le catalogue.
Versionner et valider ce document, conserver diagnostics/1.0.0 pour check,
ajouter lancer --format json avec contrat d'exécution explicite.

Préserver les sorties texte et la séparation des distributions. En JSON,
données seules sur stdout, impressions Python des adaptateurs sur stderr,
diagnostics structurés pour les refus d'exécution ; pas de coercition
silencieuse d'objets non JSON. Documenter les codes de retour et les
erreurs d'usage Typer (stderr, code 2). Tester un parcours sous-processus
découverte → programme incorrect → correction via diagnostics → check →
simulate/dry-run, avec validation de chaque document par son schéma.

### user

### agent

Livraison vérifiée : catalogue JSON versionné/validé, contrat diagnostics
inchangé, exécution JSON versionnée avec modes, résultat, connaissances,
commandes, journal, trace et diagnostics. Aucun second catalogue ni import
Codegen dans le moteur. JSON strict sans conversion silencieuse d'objets.
Rapports partiels distingués des succès ; 1000 notes puis arrêt à l'étape
1001 vérifiés, code 1. Impressions Python des adaptateurs sur stderr.
Options --env invalides refusées explicitement.

75 tests ciblés passent. Le parcours sous-processus part du seul catalogue
JSON, écrit un M1 incorrect, exploite son diagnostic, corrige et vérifie,
puis simulate/dry-run en mode generated, sans callback d'actionneur exécuté.
Toutes les sorties sont validées par leurs schémas embarqués.
Guide agents, codes de retour et limites publiés ; aucune invite ni LLM.

Validation complète verte : linters, Pyright, noyau, Codegen, Lean/audit,
90 tests obligatoires et toujours 500 termes différentiels. Les instantanés
Markdown des prompts sont inchangés. Passage en QA pour revue humaine,
pas de passage agent en done.

### user

### agent

Validation rapide et rafraîchissement du graphe également verts après QA.
Jalon prêt au commit local ; aucun push ni appel LLM.

### user
