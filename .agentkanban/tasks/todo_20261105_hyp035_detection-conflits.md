---
title: "HYP-035 · Checklist détection des conflits"
lane: qa
created: 2026-11-05T12:00:00+01:00
updated: 2026-11-05T12:00:00+01:00
description: "Implémentation locale, sans effacement des contradictions."
priority: P1
tags: [epistemique, moteur-symbolique, python]
---

## Itération 1

- [x] Collecter les assertions encore étayées, y compris les instantanés historiques.
- [x] Détecter attributs fonctionnels et invariants déclarés ; citer faits et sources.
- [x] Réutiliser la sélection du meilleur support ; conserver conflits et égalités ambiguës.
- [x] Intégrer le rapport vivant dans KnowledgeBase sans modifier la révision existante.
- [x] Tester construction sans faux positifs, révisions, alternatives et invariants M2.
- [x] Documenter les limites et valider ciblé, complet, rapide et graphe avant QA/commit.
