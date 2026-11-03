---
id: HYP-024
title: "Pont F3a : annoter l'élaboration avec les types inférés"
status: backlog
priority: P0
size: M
epic: FORMEL
depends_on: [HYP-002]
labels: [python]
assignee: 
---

# HYP-024 — Pont F3a : annoter l'élaboration avec les types inférés

## Contexte

Pour émettre un certificat (§« Pont de certificats » de `docs/verification/strategie.md`), la Core IR doit porter le type de chaque paramètre de lambda, de chaque liaison et de chaque instanciation polymorphe. Le vérificateur Python (`language/typesystem/infer.py`) les calcule déjà, mais les jette.

## Tâches

- [ ] Ajouter des annotations de types optionnelles aux nœuds `Lambda`, `Let`, `LetRec`, `Global` (instanciation) de `ir/core.py`.
- [ ] Les remplir à la fin de l'inférence, après résolution complète des variables (`prune`).
- [ ] Garantir que l'interpréteur ignore ces annotations (aucun coût à l'exécution).

## Critères d'acceptation

- [ ] Après vérification, plus aucune annotation ne contient de variable de type non résolue (sauf variables généralisées).
- [ ] Test : chaque nœud annoté de `examples/` a un type clos ou explicitement quantifié.

## Fichiers concernés

- `src/hypomnesis/ir/core.py`
- `src/hypomnesis/language/typesystem/infer.py`

## Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `kanban/README.md`
