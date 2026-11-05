---
title: "HYP-071 · Métriques bornées et export OTLP"
lane: qa
created: 2026-11-05T14:00:00+01:00
updated: 2026-11-05T14:00:00+01:00
description: "SDK privé, opérations réelles, dimensions fermées."
priority: P1
tags: [observabilite, outillage, python]
---

## Itération 1

- [x] MeterProvider privé, compteurs/histogrammes du §12.4 et mémoire.
- [x] Dimensions fermées et rejet des identifiants à forte cardinalité.
- [x] Émissions réelles aux frontières, commandes dédupliquées et validateurs.
- [x] Export OTLP local borné, sans proxy/redirection, fermeture déterministe.
- [x] Tests succès/rejet/panne, SDK/protobuf, absence de tokens inventés.
- [x] Documentation, validation complète/rapide/graphe, QA et commit local.
