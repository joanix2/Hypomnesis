---
id: HYP-002
title: "Phase 1 : langage minimal (parser, HM, interpréteur)"
status: done
priority: P0
size: L
epic: LANG
depends_on: [HYP-001]
labels: [python]
assignee: 
---

# HYP-002 — Phase 1 : langage minimal (parser, HM, interpréteur)

## Contexte

Grammaire Lark LALR, inférence Hindley-Milner, élaboration vers la Core IR, interpréteur avec appels terminaux, prélude, CLI run/check/repl.

## Résultat

- Réalisé (commit 69a4ef5).

## Fichiers concernés

- `src/hypomnesis/language/`
- `src/hypomnesis/ir/core.py`
- `src/hypomnesis/runtime/`

## Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `kanban/README.md`
