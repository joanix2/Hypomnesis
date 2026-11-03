---
id: HYP-080
title: "Publication des DSL pour les LLM"
status: backlog
priority: P1
size: M
epic: P7-LLM
depends_on: [HYP-041]
labels: [python, llm]
assignee: 
---

# HYP-080 — Publication des DSL pour les LLM

## Contexte

§14.2 : la génération s'appuie sur les descriptions de domaines, signatures, grammaires, catalogues de plugins et permissions.

## Tâches

- [ ] Commande `hypomnesis describe` : export structuré (JSON et Markdown) des modules, types, signatures et plugins accessibles.
- [ ] Taille maîtrisée : sélection par domaine.

## Critères d'acceptation

- [ ] La description du domaine `Mechanics` tient dans un prompt et liste toutes les valeurs publiques avec leurs types.

## Fichiers concernés

- `src/hypomnesis/llm/`

## Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `kanban/README.md`
