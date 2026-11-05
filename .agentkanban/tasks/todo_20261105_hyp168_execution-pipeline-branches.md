---
title: "TODO HYP-168 · Exécution des pipelines"
lane: todo
created: 2026-11-05T23:31:24+01:00
updated: 2026-11-05T23:31:24+01:00
description: "Étapes par capacité, réutilisation des résultats et branchements"
priority: P1
tags: [moteur-symbolique, metalangage, effets]
---

# Itération 1

- [ ] Relier la procédure existante aux capacités configurées par l'hôte sans déplacer l'interpréteur chez un fournisseur.
- [ ] Implémenter l'enchaînement explicite des résultats de plusieurs fournisseurs vers calcul symbolique et branchement.
- [ ] Tester qu'une branche non exécutée n'appelle aucun service et qu'un choix ambigu est refusé.
- [ ] Documenter les frontières et exécuter tests ciblés puis `./scripts/validate.sh complet`.
- [ ] Satisfaire HYP-168 sans introduire d'ordonnanceur distribué général.
