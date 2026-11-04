---
title: "TODO HYP-147 · Couches déclarées en .hyp et DAG d'imports"
lane: qa
created: 2026-11-04T17:47:20+01:00
updated: 2026-11-04T18:19:29+01:00
description: "Déclaration native du langage, composition et migration sans manifeste JSON"
priority: P1
tags: [architecture, dsl, metalangage, moteur-symbolique, tests]
---

# Itération 1

- [x] Ajouter déclaration statique `language`, AST et validation sans évaluation.
- [x] Résoudre imports locaux, cycles, identités, collisions et diamants ; exporter le DAG.
- [x] Partager le plan avec CLI, LSP (overlays compris) et Codegen.
- [x] Migrer toutes les démonstrations hors des manifestes JSON.
- [x] Démontrer logique booléenne et arithmétique partagées entre deux langages.
- [x] Tester erreurs, indépendance des branches, typage et absence d'exécution statique.
- [x] Documenter syntaxe, migration et API ; valider Python, Lean et graphe.
