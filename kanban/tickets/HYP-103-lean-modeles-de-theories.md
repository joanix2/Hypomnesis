---
id: HYP-103
title: "Lean F7 : modèles de théories et substituabilité"
status: backlog
priority: P3
size: L
epic: FORMEL
depends_on: [HYP-046, HYP-102]
labels: [lean, recherche]
assignee: 
---

# HYP-103 — Lean F7 : modèles de théories et substituabilité

## Contexte

Hypothèses H1, H3, H6 : deux modèles d'une même théorie sont interchangeables pour tout programme écrit contre la théorie.

## Tâches

- [ ] Formaliser théories, modèles et morphismes de théories.
- [ ] Prouver : un programme écrit contre une théorie a le même résultat observable dans deux modèles qui satisfont les mêmes lois, modulo ces lois.

## Critères d'acceptation

- [ ] Théorèmes sans `sorry`, ajoutés à l'audit.

## Fichiers concernés

- `formal/Hypomnesis/Meta/`

## Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `kanban/README.md`
