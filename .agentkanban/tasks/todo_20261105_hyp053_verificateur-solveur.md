---
title: "TODO HYP-053 · Vérificateur indépendant de modèles"
lane: qa
created: 2026-11-05T00:15:00+01:00
updated: 2026-11-05T00:15:00+01:00
description: "Domaines et sommes rationnelles, correction Lean, correspondance Python"
priority: P1
tags: [certification, lean, moteur-symbolique, python, solveurs, tests, validateurs]
---

# Itération 1

- [x] Formaliser affectations typées, domaines et évaluation linéaire exacte ; relation sémantique distincte.
- [x] Prouver la correction de l'évaluation et du vérificateur de faisabilité ; ajouter les théorèmes à l'audit.
- [x] Comparer le modèle exécutable au vérificateur Python sur corpus généré, frontières et vrais modèles Z3.
- [x] Refuser un faux modèle avant continuation et enregistrement de connaissance ; préserver les résultats sans promotion automatique.
- [x] Documenter les limites ; valider ciblé, complet, rapide et graphe avant commit/QA.
