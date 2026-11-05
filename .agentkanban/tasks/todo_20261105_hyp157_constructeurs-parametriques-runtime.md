---
title: "TODO HYP-157 · Constructeurs paramétriques et motifs runtime"
lane: todo
created: 2026-11-05T23:31:24+01:00
updated: 2026-11-05T23:31:24+01:00
description: "Pont de sûreté nominal, records et couverture certifiée"
priority: P1
tags: [certification, lean, metalangage]
---

# Itération 1

- [ ] Raccorder les signatures nominales et motifs paramétriques au fragment de HYP-156.
- [ ] Prouver le transport des payloads paramétriques et préserver les garanties de records, exhaustivité et `Coverage.Certified`.
- [ ] Ajouter les tests Lean d'exécution et de refus de signatures/arités incompatibles.
- [ ] Auditer et documenter les théorèmes et les limites sans `sorry`.
- [ ] Exécuter Lean/audit, `./scripts/validate.sh complet` et `git diff --check`.
- [ ] Satisfaire les critères de HYP-157 et reporter le résultat au parent HYP-023.
