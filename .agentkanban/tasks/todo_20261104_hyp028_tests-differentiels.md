---
title: "TODO HYP-028 · Différentiel Python et Lean"
lane: qa
created: 2026-11-04T23:26:00+01:00
updated: 2026-11-04T23:26:00+01:00
description: "Génération typée, comparaison exacte, budgets explicites et mutation"
priority: P1
tags: [certification, compilateur, lean, metalangage, python, runtime, tests]
---

# Itération 1

- [x] Générer des termes fermés par types, avec portée locale, fonctions, récursion bornée et données structurées.
- [x] Comparer exactement valeurs et erreurs avec le vrai hypomnesis-check eval, sans égalité fondée sur un timeout.
- [x] Exécuter au moins 500 termes en CI avec binaire obligatoire et statistiques.
- [x] Détecter une mutation volontaire de l'interpréteur Python.
- [x] Couvrir motifs/gardes/alternatives, records, scalaires et budgets par régressions explicites.
- [x] Documenter le périmètre et les limites, valider rapide/complet/graphe et proposer QA.
