---
title: "TODO HYP-132 · Diagnostics VS Code par LSP"
lane: todo
created: 2026-11-04T16:54:00+01:00
updated: 2026-11-04T16:54:00+01:00
description: "Serveur pygls et client VS Code, diagnostics du compilateur"
priority: P2
tags: [compilateur, dsl, metalangage, outillage, python, vscode]
---

# Itération 1

- [x] Réutiliser les erreurs du compilateur sans exécuter les programmes édités.
- [x] Résoudre le contexte M2 par manifeste proche ou réglage, avec textes non enregistrés.
- [x] Implémenter pygls sur stdio, délai de frappe et annulation des analyses obsolètes.
- [x] Brancher vscode-languageclient, choix de Python et réglages par dossier.
- [x] Tester au protocole LSP les diagnostics, corrections, contexte et positions UTF-16.
- [x] Documenter, générer le VSIX et lancer la validation complète.
