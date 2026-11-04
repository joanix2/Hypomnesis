---
title: "HYP-080 · Publication des DSL pour les LLM"
lane: qa
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P1 · M · Phase 7 — Intégration LLM · dépend de HYP-041"
priority: P1
tags: [documentation, dsl, llm, python]
---

## Conversation

### user

**Ticket** HYP-080 · **Priorité** P1 · **Taille** M · **Epic** Phase 7 — Intégration LLM · **Dépend de** HYP-041 · **Labels** python, llm

#### Contexte

§14.2 : la génération s'appuie sur les descriptions de domaines, signatures, grammaires, catalogues de plugins et permissions.

#### Tâches proposées

- Commande `hypomnesis describe` : export structuré (JSON et Markdown) des modules, types, signatures et plugins accessibles.
- Taille maîtrisée : sélection par domaine.

#### Critères d'acceptation

- La description du domaine `Mechanics` tient dans un prompt et liste toutes les valeurs publiques avec leurs types.

#### Fichiers concernés

- `src/hypomnesis/llm/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`

### agent

Plan/todo/implémentation dans la continuité de l'objectif P0 :
l'ADR 0012 remplace l'ancien emplacement `src/hypomnesis/llm/` par
`packages/codegen`. La sélection d'un langage limite déjà son DAG et publie
les signatures documentées ; réutiliser ce catalogue, sans second format.
Compléter les métadonnées statiques (contrats, adaptateurs déclarés) et
les plugins explicitement fournis par l'hôte, avec leurs permissions
requises, jamais des droits implicitement accordés.

Vérifier JSON/Markdown, exhaustivité des valeurs publiques de Mechanics,
taille mesurée <= 16 Kio UTF-8 et absence d'import des backends/adaptateurs.
La CLI reste `hypomnesis-codegen decrire`, conformément à la séparation
adoptée, pas de réintroduction d'une commande LLM dans le noyau.

### user

### agent

Terminé, validation complète verte. Catalogue JSON/Markdown enrichi avec
contrats, adaptateurs déclarés et plugins explicitement publiés par l'hôte
(`decrire --plugin`), signatures et permissions requises non accordées.
Aucun import de backend ou d'adaptateur ; erreurs de manifeste explicites.
Bibliothèques sans procédure et valeurs publiques à la racine également prises
en charge. Exhaustivité des valeurs publiques de Mechanics testée.

Mesure mécanique : 4 336 octets UTF-8, sous le budget explicite de 16 Kio ;
ce n'est pas une borne de tokens indépendante du tokenizer. 26 tests ciblés
passent. Instantanés intentionnellement actualisés : les anciens résultats
de banc LLM ne sont pas strictement comparables sans réexécution.
Passage QA uniquement, done réservé à la vérification humaine.

### user
