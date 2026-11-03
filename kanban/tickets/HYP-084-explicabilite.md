---
id: HYP-084
title: "Explicabilité : reformuler ce qui a été compris et fait"
status: backlog
priority: P2
size: M
epic: P7-LLM
depends_on: [HYP-081, HYP-031]
labels: [python, llm]
assignee: 
---

# HYP-084 — Explicabilité : reformuler ce qui a été compris et fait

## Contexte

§14.5 : reformuler ce qui a été compris, les informations utilisées, les hypothèses, règles, validations et actions à venir.

## Tâches

- [ ] Construire l'explication à partir de la provenance (termes et journal), et non d'une génération libre.
- [ ] Le LLM peut mettre en forme, mais chaque affirmation renvoie à une entrée de provenance.

## Critères d'acceptation

- [ ] Chaque phrase de l'explication cite un identifiant de fait, de règle ou de commande.

## Fichiers concernés

- `src/hypomnesis/llm/`

## Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `kanban/README.md`
