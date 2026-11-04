---
title: "TODO HYP-044 · Backend Python contractuel"
lane: qa
created: 2026-11-04T18:22:06+01:00
updated: 2026-11-04T18:22:06+01:00
description: "Contrats, primitive explicite, sous-processus et timeout effectif"
priority: P0
tags: [capacites, contrats, moteur-symbolique, python]
---

# Itération 1

- [x] Réutiliser PreparedExtension et les codecs ; valider avant import et après appel.
- [x] Exécuter un entry point explicite en sous-processus, avec timeout et récolte.
- [x] Exposer une primitive fermée typée et des erreurs exploitables par le langage.
- [x] Journaliser succès, contrat invalide, exception, crash et dépassement.
- [x] Tester refus avant import, appel .hyp, contrat de sortie et absence de processus survivant.
- [x] Documenter les limites et valider tests ciblés, Ruff, Pyright et validation complète.
