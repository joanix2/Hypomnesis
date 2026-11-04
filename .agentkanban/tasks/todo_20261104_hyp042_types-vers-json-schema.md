---
title: "TODO HYP-042 · Types et JSON Schema"
lane: todo
created: 2026-11-04T16:10:00+01:00
updated: 2026-11-04T16:10:00+01:00
description: "Codec réversible, contrats et migration JSON"
---

# Iteration 1

- [x] Rédiger l'ADR du format, des limites et de la migration.
- [x] Générer les schémas depuis les types et implémenter encode/decode stricts.
- [x] Vérifier les signatures et contrats des manifestes sans exécution de backend.
- [x] Migrer les ponts JSON et préserver options imbriquées et grands entiers.
- [x] Tester avec Hypothesis les aller-retours JSON et la conformité aux schémas.
- [x] Tester les refus, la compatibilité directionnelle et les scénarios M2 existants.
- [x] Mettre à jour la documentation ; tenter Graphify et signaler le refus connu HYP-144.
- [x] Valider rapide/complet, consigner le bilan et préparer la publication sans changer le couloir.
