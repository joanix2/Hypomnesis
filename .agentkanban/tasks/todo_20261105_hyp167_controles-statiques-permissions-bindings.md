---
title: "TODO HYP-167 · Contrôles statiques et permissions"
lane: todo
created: 2026-11-05T23:31:24+01:00
updated: 2026-11-05T23:31:24+01:00
description: "Imports symboliques, check/LSP statiques et validation avant appel"
priority: P1
tags: [metalangage, contrats, securite, lsp]
---

# Itération 1

- [ ] Distinguer les imports de bibliothèques et les bindings d'exécution dans les contrats existants.
- [ ] Tester que imports, check et LSP ne chargent aucun adaptateur et ne démarrent aucun service.
- [ ] Tester le refus d'un appel sans permission ou avec un contrat incompatible avant dispatch.
- [ ] Documenter le comportement et exécuter tests ciblés puis `./scripts/validate.sh complet`.
- [ ] Satisfaire HYP-167 et reporter les résultats au parent HYP-152.
