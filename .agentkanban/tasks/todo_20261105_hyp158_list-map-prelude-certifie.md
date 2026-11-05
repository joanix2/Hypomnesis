---
title: "TODO HYP-158 · Vérification du vrai List.map"
lane: todo
created: 2026-11-05T23:31:24+01:00
updated: 2026-11-05T23:31:24+01:00
description: "Prélude, dépendances, vérification polymorphe et régression multi-instanciée"
priority: P1
tags: [certification, lean, compilateur, metalangage]
---

# Itération 1

- [ ] Tracer le corps réel de `List.map` et ses dépendances nécessaires (`rev`, `fold_left`) jusqu'au certificat vérifié.
- [ ] Vérifier ce programme dans le fragment polymorphe prouvé par HYP-156/157, sans le remplacer par un exemple isolé.
- [ ] Ajouter une régression typée/exécutée à plusieurs instanciations dans le même programme.
- [ ] Auditer les propriétés, documenter la portée et vérifier l'absence de `sorry`.
- [ ] Exécuter Lean/audit, les tests ciblés, `./scripts/validate.sh complet` et `git diff --check`.
- [ ] Satisfaire les critères de HYP-158 et consigner le résultat dans le parent HYP-023.
