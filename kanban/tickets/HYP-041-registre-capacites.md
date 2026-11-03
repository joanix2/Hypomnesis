---
id: HYP-041
title: "Registre de capacités et manifestes"
status: backlog
priority: P0
size: M
epic: P3-EXTENSIONS
depends_on: [HYP-040]
labels: [python, contrats]
assignee: 
---

# HYP-041 — Registre de capacités et manifestes

## Contexte

§6.1 : une extension doit être découvrable et inspectable sans exécuter son code métier. Le schéma `extension-manifest/1.0.0` existe déjà dans `src/hypomnesis/contracts/schemas/`.

## Tâches

- [ ] `engine/registry.py` : charger des manifestes JSON, les valider, indexer par identifiant, rôle et version.
- [ ] Résolution de dépendances entre extensions avec contraintes de version.
- [ ] `hypomnesis plugins list|show` dans la CLI.

## Critères d'acceptation

- [ ] Un manifeste invalide est refusé à l'enregistrement.
- [ ] L'inspection ne charge pas le code Python de l'extension (vérifié par test).

## Fichiers concernés

- `src/hypomnesis/engine/registry.py`
- `src/hypomnesis/cli.py`

## Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `kanban/README.md`
