---
id: HYP-026
title: "Pont F3c : exécutable Lean `hypomnesis-check`"
status: backlog
priority: P0
size: M
epic: FORMEL
depends_on: [HYP-025, HYP-020]
labels: [lean]
assignee: 
---

# HYP-026 — Pont F3c : exécutable Lean `hypomnesis-check`

## Contexte

Le vérificateur `typeOf`, prouvé correct, doit pouvoir lire un certificat JSON produit par Python.

## Tâches

- [ ] Ajouter une cible `lean_exe hypomnesis-check` dans `formal/lakefile.toml`.
- [ ] Décoder le JSON (`Lean.Json`) vers `Expr`, `Ty` et Σ ; retourner un code de sortie et un diagnostic en cas de refus.
- [ ] Sous-commande `eval` exposant l'interpréteur de référence (utilisée par HYP-028).

## Critères d'acceptation

- [ ] `lake exe hypomnesis-check cert.json` accepte les certificats des exemples et refuse un certificat altéré à la main.
- [ ] Le décodeur est séparé du noyau prouvé : seul `typeOf` fait partie de la base de confiance.

## Fichiers concernés

- `formal/lakefile.toml`
- `formal/Main.lean`
- `formal/Hypomnesis/Certificate.lean`

## Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `kanban/README.md`
