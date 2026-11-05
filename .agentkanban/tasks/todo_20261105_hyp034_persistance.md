---
title: "HYP-034 · Checklist persistance SQLite"
lane: qa
created: 2026-11-05T12:00:00+01:00
updated: 2026-11-05T12:00:00+01:00
description: "Journal versionné et rejeu typé sans exécution métier."
priority: P1
tags: [epistemique, moteur-symbolique, persistance, python]
---

## Itération 1

- [x] Capturer les inconnues des événements et persister le compteur de sources.
- [x] Définir le contrat du journal ; réutiliser schémas/TypeCodec existants.
- [x] Exporter/importer JSON strict et rejouer exactement sans lancer les règles.
- [x] Ajouter SQLite append-only, transactions et migrations versionnées.
- [x] Tester erreurs localisées, rollback, migration non vide, redémarrage et cohérence.
- [x] Documenter et valider ciblé, complet, rapide et graphe avant QA/commit.
