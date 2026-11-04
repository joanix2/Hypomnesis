---
title: "TODO HYP-041 · Registre de capacités et manifestes"
lane: todo
created: 2026-11-04T15:40:00+01:00
updated: 2026-11-04T15:50:39+01:00
description: "Checklist HYP-041 : registre statique, dépendances et CLI"
---

# Iteration 1

- [x] Relire la tâche, les contrats et les conventions existantes.
- [x] Ajouter le registre statique dans `engine/registry.py` : validation, chargement JSON,
      indexation id/rôle/version, protection contre les doublons contradictoires et mutations.
- [x] Résoudre les contraintes de version et dépendances transitives avec diagnostics des
      dépendances absentes, conflits et cycles ; produire l'ordre de chargement.
- [x] Ajouter `hypomnesis plugins list|show` sans import de backend, avec options de manifestes
      explicites et erreurs applicatives cohérentes avec la CLI.
- [x] Tester les manifestes invalides, versions multiples, contraintes, résolution transitive,
      conflits, cycles et inspection sans exécution de Python.
- [x] Documenter l'API et les commandes dans `TECHNICAL.md` et la documentation pertinente.
- [x] Lancer les validations ciblées, puis `rapide` et `complet` ; actualiser le graphe si disponible.
- [x] Consigner le bilan, les limites et les résultats dans la tâche ; laisser la décision
      de passage en `done` à l'utilisateur.
