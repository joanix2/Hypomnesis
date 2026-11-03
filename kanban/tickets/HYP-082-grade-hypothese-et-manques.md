---
id: HYP-082
title: "Sorties LLM au grade `Hypothesis` et détection des manques"
status: backlog
priority: P1
size: M
epic: P7-LLM
depends_on: [HYP-081, HYP-032]
labels: [python, llm]
assignee: 
---

# HYP-082 — Sorties LLM au grade `Hypothesis` et détection des manques

## Contexte

§14.4 : les informations manquantes restent explicites ; le LLM ne doit pas inventer les valeurs. Propriété P12 (monotonie du support).

## Tâches

- [ ] Toute valeur littérale introduite par le LLM sans source a le support `Hypothesis`.
- [ ] Les valeurs absentes deviennent des métavariables à résoudre par les estimateurs.
- [ ] Rapport des informations manquantes à l'utilisateur.

## Critères d'acceptation

- [ ] « Estime son épaisseur » produit une métavariable résolue par l'estimateur, et non une valeur inventée par le LLM.

## Fichiers concernés

- `src/hypomnesis/llm/`

## Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `kanban/README.md`
