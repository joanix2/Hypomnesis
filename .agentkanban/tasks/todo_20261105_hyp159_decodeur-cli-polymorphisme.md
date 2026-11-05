---
title: "TODO HYP-159 · Certificats polymorphes CLI"
lane: todo
created: 2026-11-05T23:31:24+01:00
updated: 2026-11-05T23:31:24+01:00
description: "Décodeur, CLI, compatibilité et refus de certificats invalides"
priority: P1
tags: [certification, compilateur, lean, cli]
---

# Itération 1

- [ ] Décrire le format polymorphe effectivement prouvé avant d'étendre son décodeur.
- [ ] Brancher le vérificateur au chemin CLI utilisé par les programmes élaborés.
- [ ] Tester certificat valide, altéré, hors-fragment et versions historiques 1.0/1.1 sans repli permissif.
- [ ] Auditer et documenter le contrat et les erreurs de refus ; conserver les régressions antérieures.
- [ ] Exécuter tests ciblés, `./scripts/validate.sh complet` et `git diff --check`.
- [ ] Satisfaire les critères de HYP-159 et reporter le résultat au parent HYP-023.
