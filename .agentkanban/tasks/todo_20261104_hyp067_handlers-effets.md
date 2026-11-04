---
title: "TODO HYP-067 · Handlers du même terme"
lane: qa
created: 2026-11-04T23:55:00+01:00
updated: 2026-11-04T23:55:00+01:00
description: "Effets typés, absence de dispatch, réponses et continuations"
priority: P1
tags: [effets, lean, moteur-symbolique]
---

# Itération 1

- [x] Formaliser opérations/continuations typées, état hôte et budgets sans mode dans le terme.
- [x] Prouver dry-run/simulation sans dispatch et dry-run sans appel des callbacks d'action.
- [x] Prouver effacement vers un même fold et congruence sous mêmes réponses/transitions.
- [x] Tester le modèle Lean exécutable contre les modes Python, refus, échéances et une continuation réelle dépendant de la réponse.
- [x] Auditer les théorèmes et documenter le périmètre, sans prétendre au raffinement Python complet.
- [x] Valider ciblé, complet, rapide et graphe ; commit et QA seulement.
