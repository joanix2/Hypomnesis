---
id: HYP-004
title: "Pousser la branche et valider la CI (Python et preuves)"
status: backlog
priority: P0
size: S
epic: FONDATIONS
depends_on: [HYP-003]
labels: [humain, ci]
assignee: 
---

# HYP-004 — Pousser la branche et valider la CI (Python et preuves)

## Contexte

La branche `phase-0-1-langage-minimal` n'a jamais été poussée : le workflow `.github/workflows/ci.yml` (jobs `test` et `proofs`) n'a donc jamais tourné sur GitHub. Le job `proofs` installe elan et lance `lake build`.

## Tâches

- [ ] Pousser la branche vers `origin` (décision humaine).
- [ ] Observer les deux jobs ; corriger ce qui échoue (versions Python 3.11/3.13, installation d'elan, cache).

## Critères d'acceptation

- [ ] Les jobs `test` et `proofs` sont verts sur la branche.
- [ ] Le job `proofs` échoue si l'on introduit volontairement un `sorry` (vérifié une fois puis annulé).

## Fichiers concernés

- `.github/workflows/ci.yml`

## Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `kanban/README.md`
