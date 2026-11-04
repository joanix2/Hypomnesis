---
title: "TODO HYP-066 · Au plus un appel non idempotent"
lane: qa
created: 2026-11-04T22:00:00+01:00
updated: 2026-11-04T22:00:00+01:00
description: "Relances gardées, pertes, duplications et états terminaux"
priority: P0
tags: [effets, lean, moteur-symbolique]
---

# Itération 1

- [x] Raffiner l'automate avec garde de relance et événements de transport.
- [x] Prouver au plus un handoff pour une commande non idempotente.
- [x] Prouver budget de relance et absence de sortie des états terminaux.
- [x] Auditer les théorèmes et documenter les hypothèses physiques et de persistance.
- [x] Comparer les gardes Lean/Python et tester les duplications après perte.
- [x] Valider intégralement avant QA.
