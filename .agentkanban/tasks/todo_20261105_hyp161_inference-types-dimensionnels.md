---
title: "TODO HYP-161 · Inférence dimensionnelle"
lane: todo
created: 2026-11-05T23:31:24+01:00
updated: 2026-11-05T23:31:24+01:00
description: "Représentation, unification AG, diagnostics et régressions"
priority: P2
tags: [compilateur, dsl, metalangage, moteur-symbolique, python]
---

# Itération 1

- [ ] Appliquer l'ADR HYP-160 pour représenter et normaliser les dimensions comme groupe abélien libre.
- [ ] Intégrer l'unification dimensionnelle à l'inférence des types sans introduire de connaissance d'unités dans le noyau.
- [ ] Tester le rejet de `m + s`, l'acceptation de `m / s * s` comme `m` et l'inférence des types principaux.
- [ ] Documenter les limites et exécuter les validations ciblées et `./scripts/validate.sh complet`.
- [ ] Satisfaire HYP-161 ; si un changement de sémantique est requis, demander arbitrage avant de l'introduire.
