---
title: "TODO HYP-152 · Suivi des bindings de services"
lane: todo
created: 2026-11-05T23:31:24+01:00
updated: 2026-11-05T23:31:24+01:00
description: "Contrats, bindings hôte, permissions et vérification statique"
priority: P1
tags: [metalangage, moteur-symbolique, contrats, effets]
---

# Itération 1

- [ ] HYP-165 : établir le contrat typé des capacités, versions, échanges, erreurs et disponibilité.
- [ ] HYP-166 (après HYP-165) : relier les bindings hôte et démontrer la substitution de deux fournisseurs compatibles.
- [ ] HYP-167 (après HYP-165 et HYP-166) : garantir la séparation imports/bindings, les contrôles statiques et les permissions avant appel.
- [ ] Vérifier les échanges réels, erreurs distinctes, absence de succès fictif et absence d'import/démarrage durant check/LSP.
- [ ] Documenter l'intégration avec Effect IR, transport, solveurs/règles sans choisir un transport ou une syntaxe non arbitrés.
- [ ] Exécuter `./scripts/validate.sh complet`, tests ciblés et `git diff --check`.
- [ ] Satisfaire tous les critères de HYP-152 ; garder le parent ouvert jusqu'à vérification utilisateur.
