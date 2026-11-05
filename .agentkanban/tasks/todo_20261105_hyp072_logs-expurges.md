---
title: "HYP-072 · Logs JSON corrélés et expurgés"
lane: qa
created: 2026-11-05T15:00:00+01:00
updated: 2026-11-05T15:00:00+01:00
description: "Événements réels, métadonnées positives et erreurs sans contenu brut."
priority: P1
tags: [observabilite, outillage, python, securite]
---

## Itération 1

- [x] Format JSON, corrélation run/trace/span et désactivation hôte/CLI.
- [x] Expurgation par défaut, structures imbriquées et politique renforçable.
- [x] Événements aux frontières réelles et exceptions de traces expurgées.
- [x] Diagnostics d'export sans corps de réponse ni exception brute.
- [x] Tests fuite de prompts/données, concurrence et stdout CLI préservé.
- [x] Documentation, validation complète/rapide/graphe, QA et commit local.
