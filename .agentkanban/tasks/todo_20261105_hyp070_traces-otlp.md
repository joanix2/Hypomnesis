---
title: "HYP-070 · Traces corrélées et export OTLP"
lane: qa
created: 2026-11-05T13:40:00+01:00
updated: 2026-11-05T13:40:00+01:00
description: "Étendre le SDK existant et tracer les frontières réelles."
priority: P1
tags: [observabilite, outillage, python]
---

## Itération 1

- [x] Façade isolée/concurrente, configuration hôte et export OTLP borné.
- [x] Arbre racine réel parsing/typage/exécution et étapes du MVP.
- [x] Propagation W3C aux enveloppes et extraction à réception.
- [x] Tests arbre, concurrence, export reçu, erreurs et invariance des résultats.
- [x] Documentation, validation complète/rapide/graphe puis QA et commit local.
