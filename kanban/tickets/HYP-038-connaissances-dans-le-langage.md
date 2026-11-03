---
id: HYP-038
title: "Exposer les connaissances dans le langage"
status: backlog
priority: P1
size: M
epic: P2-EPISTEMIQUE
depends_on: [HYP-030, HYP-033]
labels: [python]
assignee: 
---

# HYP-038 — Exposer les connaissances dans le langage

## Contexte

Les programmes Hypomnesis doivent pouvoir manipuler les connaissances (§2 OBJ-04, §5) sans effet de bord : lecture d'une base immuable passée en argument, construction de faits dérivés.

## Tâches

- [ ] Bibliothèque `Knowledge` (types et fonctions natives pures) : interroger, dériver, consulter la provenance et le support.
- [ ] Les primitives passent par le registre natif fermé (ADR 0003).
- [ ] Exemple `examples/knowledge/` sur la plaque.

## Critères d'acceptation

- [ ] Un programme dérive un fait dont le support est calculé automatiquement (Estimated si une prémisse l'est).

## Fichiers concernés

- `src/hypomnesis/stdlib/`
- `src/hypomnesis/runtime/natives.py`
- `examples/knowledge/`

## Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `kanban/README.md`
