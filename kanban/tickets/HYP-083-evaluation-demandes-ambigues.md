---
id: HYP-083
title: "Jeu d'évaluation de demandes ambiguës"
status: backlog
priority: P2
size: M
epic: P7-LLM
depends_on: [HYP-081]
labels: [llm, tests]
assignee: 
---

# HYP-083 — Jeu d'évaluation de demandes ambiguës

## Contexte

§17 phase 7 : tester les demandes ambiguës. Évaluation empirique, hors du champ formel (⛔ dans `proprietes.md`).

## Tâches

- [ ] Corpus de demandes avec résultats attendus (programme, ou demande de précision).
- [ ] Métriques : taux de programmes bien typés, taux de clarifications pertinentes.

## Critères d'acceptation

- [ ] Rapport reproductible versionné.

## Fichiers concernés

- `tests/llm_eval/`

## Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `kanban/README.md`
