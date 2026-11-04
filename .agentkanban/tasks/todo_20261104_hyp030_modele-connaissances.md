---
title: "TODO HYP-030 · Modèle de données des connaissances"
lane: qa
created: 2026-11-04T19:25:09+01:00
updated: 2026-11-04T19:25:09+01:00
description: "Compléter les structures existantes et leur frontière JSON typée"
priority: P0
tags: [epistemique, moteur-symbolique, python]
---

# Itération 1

- [x] Réutiliser Fact, Source, Unknown et le calcul de support existants ; préserver les appels du moteur.
- [x] Garantir des instantanés immuables, y compris les valeurs composites, et valider les métadonnées.
- [x] Ajouter Observation liée à sa source et garder Unknown comme métavariable explicite.
- [x] Ajouter le contrat knowledge/1.0.0 et les échanges réversibles avec TypeCodec pour les types fermés.
- [x] Tester mutations, statuts, identifiants, provenance, erreurs et aller-retour JSON sur scalaires et types structurés.
- [x] Documenter le périmètre, valider le dépôt, rafraîchir le graphe et passer en QA.
