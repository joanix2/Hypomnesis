---
title: "TODO HYP-042 · Types et JSON Schema"
lane: todo
created: 2026-11-04T16:10:00+01:00
updated: 2026-11-04T16:10:00+01:00
description: "Codec réversible, contrats et migration JSON"
---

# Iteration 1

- [ ] Rédiger l'ADR du format, des limites et de la migration.
- [ ] Générer les schémas depuis les types et implémenter encode/decode stricts.
- [ ] Vérifier les signatures et contrats des manifestes sans exécution de backend.
- [ ] Migrer les ponts JSON et préserver options imbriquées et grands entiers.
- [ ] Tester avec Hypothesis les aller-retours JSON et la conformité aux schémas.
- [ ] Tester les refus, la compatibilité directionnelle et les scénarios M2 existants.
- [ ] Mettre à jour la documentation et actualiser Graphify.
- [ ] Valider rapide/complet, consigner le bilan et publier sans changer le couloir.
