---
id: HYP-012
title: "Signatures de modules (`module type`, contrainte `M : S`)"
status: backlog
priority: P1
size: L
epic: LANG
depends_on: [HYP-002]
labels: [python]
assignee: 
---

# HYP-012 — Signatures de modules (`module type`, contrainte `M : S`)

## Contexte

Les signatures de modules sont le point d'entrée des théories du niveau M3 (§4.1 de `docs/architecture/m3-metalangage.md` : « une signature de module est déjà une théorie sans équations »). Elles sont aussi nécessaires pour typer statiquement les interfaces d'extensions (§13.2).

## Tâches

- [ ] Grammaire : `module type S = sig val f : t  type t ... end` et `module M : S = struct ... end`.
- [ ] Types abstraits dans les signatures (`type t` sans définition) : rendre `M.t` abstrait hors du module.
- [ ] Vérifier qu'une structure satisfait une signature (sous-typage de signatures, ordre des champs libre).

## Critères d'acceptation

- [ ] Un module qui n'implémente pas une valeur de sa signature est rejeté, avec un message positionné.
- [ ] Un type abstrait ne peut pas être déconstruit hors du module.
- [ ] La référence du langage est mise à jour.

## Fichiers concernés

- `src/hypomnesis/language/grammar/hypomnesis.lark`
- `src/hypomnesis/language/typesystem/infer.py`
- `docs/language/reference.md`

## Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `kanban/README.md`
