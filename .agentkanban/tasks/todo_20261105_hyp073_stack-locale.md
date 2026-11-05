---
title: "HYP-073 · Stack locale réellement vérifiée"
lane: qa
created: 2026-11-05T16:00:00+01:00
updated: 2026-11-05T16:00:00+01:00
description: "Compose ARM64, sources Grafana et preuves bout en bout."
priority: P1
tags: [infra, observabilite, outillage]
---

## Itération 1

- [x] Compose Collector/Prometheus/Grafana/Tempo, versions et digests fixés.
- [x] Ports loopback, ressources limitées, volumes et provisionnement.
- [x] Readiness réelle et deux MVP sans LLM, export OTLP.
- [x] Traces réelles et augmentation des métriques lues via Grafana.
- [x] Tests de configuration/vérificateur et documentation de démarrage/arrêt.
- [x] Validation complète/rapide/graphe, QA et commit local.

## Itération 2 — défaut concurrent découvert

- [x] Vérifier deux MVP séquentiels : deux traces complètes, compteur 0 → 2.
- [x] Tester deux MVP concurrents : défaut constaté, compteur 2 → 3 au lieu de 4.
- [x] Localiser le rejet dans l'agrégateur delta officiel ; 31 tests SDK verts.
- [x] Arbitrer identité des producteurs ou agrégation durable partagée.
- [x] Corriger le modèle retenu et ajouter un test concurrent reproductible.
- [x] Vérifier les comptes et distributions des histogrammes, pas seulement les traces.
