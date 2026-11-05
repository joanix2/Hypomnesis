---
title: "HYP-151 · Checklist coloration et arbitrage"
lane: qa
created: 2026-11-05T03:00:00+01:00
updated: 2026-11-05T03:00:00+01:00
description: "Coloration vérifiée sur Mac, syntaxe réservée à l'arbitrage humain."
priority: P2
tags: [metalangage, dsl, outillage, vscode]
---

## Itération 1

- [x] Vérifier extension installée, association et grammaire effectivement contribuée.
- [x] Colorer le nom déclaré et les métadonnées sans modifier le parseur.
- [x] Tester le bloc exact, imbrication et absence de débordement.
- [x] Vérifier association, activation et tokenisation dans un hôte VS Code réel.
- [x] Documenter le diagnostic local, installation/rechargement et choix syntaxiques.
- [x] Valider complet, rapide et graphe, committer le volet indépendant.
- [x] Obtenir l'arbitrage humain avant toute harmonisation incompatible.

## Itération 2 — remplacement adopté

- [x] Documenter l'arbitrage et l'ADR struct/let/end sans compatibilité ancienne.
- [x] Adapter grammaire et AST statique, tester refus, doublons et positions.
- [x] Migrer toutes les déclarations actives, fixtures, générateurs et documentation.
- [x] Adapter TextMate et tester la portée jusqu'à end, y compris records imbriqués.
- [x] Valider Python, Node et hôte réel, reconstruire et installer l'extension.
- [x] Valider complet, rapide et graphe ; consigner les preuves et committer.
