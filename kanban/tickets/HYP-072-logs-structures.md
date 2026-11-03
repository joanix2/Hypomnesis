---
id: HYP-072
title: "Logs structurés corrélés et expurgation"
status: backlog
priority: P1
size: S
epic: P6-OBSERVABILITE
depends_on: [HYP-070]
labels: [python, observabilité]
assignee: 
---

# HYP-072 — Logs structurés corrélés et expurgation

## Contexte

§12.5 : logs JSON corrélés aux traces ; pas de données brutes de capteurs, de prompts LLM ni de données personnelles par défaut.

## Tâches

- [ ] Format du §12.5 ; filtre d'expurgation configurable.
- [ ] Corrélation `trace_id` et `span_id`.

## Critères d'acceptation

- [ ] Test : un prompt LLM n'apparaît jamais dans les logs par défaut.

## Fichiers concernés

- `src/hypomnesis/observability/logging.py`

## Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `kanban/README.md`
