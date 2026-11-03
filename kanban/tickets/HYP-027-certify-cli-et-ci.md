---
id: HYP-027
title: "Pont F3d : `hypomnesis check --certify` et certification en CI"
status: backlog
priority: P0
size: S
epic: FORMEL
depends_on: [HYP-026, HYP-004]
labels: [python, ci]
assignee: 
---

# HYP-027 — Pont F3d : `hypomnesis check --certify` et certification en CI

## Contexte

Dernière étape du pont : rendre la certification utilisable et systématique.

## Tâches

- [ ] `--certify` : émettre le certificat, appeler `hypomnesis-check`, échouer si refusé.
- [ ] Job CI qui certifie tous les fichiers de `examples/`.
- [ ] Mettre à jour la ligne P3 de `proprietes.md` (garantie de bout en bout).

## Critères d'acceptation

- [ ] CI verte avec certification ; un exemple volontairement mal élaboré, injecté dans un test, est refusé.

## Fichiers concernés

- `src/hypomnesis/cli.py`
- `.github/workflows/ci.yml`
- `docs/verification/proprietes.md`

## Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `kanban/README.md`
