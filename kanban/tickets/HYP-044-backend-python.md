---
id: HYP-044
title: "Adaptateur de backend Python générique"
status: backlog
priority: P0
size: M
epic: P3-EXTENSIONS
depends_on: [HYP-041, HYP-042]
labels: [python]
assignee: 
---

# HYP-044 — Adaptateur de backend Python générique

## Contexte

§6.2 : premier backend. Un appel valide l'entrée, appelle l'adaptateur, valide la sortie et enregistre le résultat.

## Tâches

- [ ] Charger l'`entry_point` du manifeste ; isoler les erreurs ; appliquer `timeout_seconds`.
- [ ] Validation JSON Schema en entrée et en sortie de chaque appel.
- [ ] Rendre l'appel disponible au langage via une primitive déclarée (pas d'accès Python arbitraire).

## Critères d'acceptation

- [ ] Une sortie non conforme est rejetée et journalisée ; le programme reçoit une erreur typée.

## Fichiers concernés

- `src/hypomnesis/backends/python/`

## Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `kanban/README.md`
