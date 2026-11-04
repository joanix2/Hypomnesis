---
title: "TODO HYP-146 · Séparer Codegen du moteur"
lane: todo
created: 2026-11-04T17:27:16+01:00
updated: 2026-11-04T17:27:16+01:00
description: "Extraction du paquet, CLI dédiée et vérification de l'indépendance"
priority: P1
tags: [architecture, llm, moteur-symbolique, outillage, tests]
---

# Itération 1

- [x] Extraire le paquet installable, les ressources et la CLI dédiée.
- [x] Déplacer tests et instantanés LLM sans dépendance inverse dans les tests du moteur.
- [x] Adapter dépendances, CI, validateurs et documentation active.
- [x] Vérifier les roues installées et le fonctionnement du moteur sans Codegen.
- [x] Valider les deux suites, Ruff, Pyright, Lean et rafraîchir le graphe.
