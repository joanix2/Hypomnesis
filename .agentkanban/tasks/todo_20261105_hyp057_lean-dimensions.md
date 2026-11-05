---
title: "TODO HYP-057 · Suivi de la preuve dimensionnelle"
lane: todo
created: 2026-11-05T23:31:24+01:00
updated: 2026-11-05T23:31:24+01:00
description: "Formalisation, sûreté et invariance d'échelle"
priority: P2
tags: [lean, metalangage, moteur-symbolique]
---

# Itération 1

- [ ] HYP-163 (après HYP-156 et HYP-161) : formaliser le fragment dimensionnel et prouver sa sûreté.
- [ ] HYP-164 (après HYP-163) : prouver la commutation par changement d'échelle pour les fonctions polymorphes en dimension.
- [ ] Auditer les théorèmes et ajouter toute nouvelle propriété à l'audit formel du projet, sans `sorry`.
- [ ] Documenter hypothèses, fragment et limites ; conserver les critères initiaux de HYP-057.
- [ ] Exécuter Lean/audit, `./scripts/validate.sh complet` et `git diff --check`.
- [ ] Garder le parent en suivi jusqu'à vérification utilisateur ; ne pas passer automatiquement en QA/done.
