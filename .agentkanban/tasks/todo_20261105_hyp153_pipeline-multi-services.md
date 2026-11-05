---
title: "TODO HYP-153 · Suivi des pipelines multi-services"
lane: todo
created: 2026-11-05T23:31:24+01:00
updated: 2026-11-05T23:31:24+01:00
description: "Orchestration des capacités, continuité symbolique et erreurs observables"
priority: P1
tags: [moteur-symbolique, metalangage, effets, epistemique]
---

# Itération 1

- [ ] HYP-168 (après HYP-166/167) : exécuter une procédure réelle sur plusieurs fournisseurs et ne pas appeler les services d'une branche évitée.
- [ ] HYP-169 (après HYP-168) : préserver types, identités de faits, provenance, hypothèses et validations aux frontières.
- [ ] HYP-170 (après HYP-168/169) : borner budgets/délais, traiter annulation/erreurs/relances et tracer les étapes/services/résultats.
- [ ] Tester panne, timeout, résultat invalide, annulation, branchement et absence d'autopromotion épistémique.
- [ ] Vérifier que la logique métier reste dans les programmes/DSL et les bindings génériques.
- [ ] Exécuter `./scripts/validate.sh complet`, tests ciblés et `git diff --check`.
- [ ] Satisfaire tous les critères de HYP-153 et garder le parent ouvert jusqu'à vérification utilisateur.
