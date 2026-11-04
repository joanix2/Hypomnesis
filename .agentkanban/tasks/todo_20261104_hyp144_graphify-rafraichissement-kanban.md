---
title: "TODO HYP-144 · Rafraîchissement Graphify après injection du Kanban"
lane: todo
created: 2026-11-04T16:43:39+01:00
updated: 2026-11-04T16:43:39+01:00
description: "Checklist HYP-144 : migration des chemins synthétiques et rafraîchissement répété"
priority: P2
tags: [graphify, kanban, outillage]
---

# Itération 1

- [x] Identifier la déduplication des chemins synthétiques comme doublons de fichiers AST.
- [x] Distinguer les libellés de chemins et conserver le chemin dans `referenced_path`.
- [x] Migrer les injections existantes avant de reconstruire, sans contourner le garde-fou.
- [x] Vérifier les tests de migration, de résolution vers un vrai fichier et d'idempotence.
- [x] Exécuter deux cycles réels de rafraîchissement puis injection.
- [x] Vérifier la validation complète et documenter le résultat.
