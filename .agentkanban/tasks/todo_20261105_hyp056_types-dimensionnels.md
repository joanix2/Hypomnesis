---
title: "TODO HYP-056 · Suivi des types dimensionnels"
lane: todo
created: 2026-11-05T23:31:24+01:00
updated: 2026-11-05T23:31:24+01:00
description: "ADR, unification AG, bibliothèque Units et exemple mécanique"
priority: P2
tags: [compilateur, dsl, metalangage, moteur-symbolique, python]
---

# Itération 1

- [ ] HYP-160 : rédiger l'ADR de conception, y compris les options et limites, sans décision métier ajoutée.
- [ ] HYP-161 (après HYP-160) : implémenter/types et tests d'unification dimensionnelle ; rejeter `m + s` et normaliser `m / s * s` en `m`.
- [ ] HYP-162 (après HYP-161) : livrer la bibliothèque `Units`, conversions, exemple `units.hyp` et tests des types principaux inférés.
- [ ] Vérifier que le noyau reste indépendant des unités et documenter l'architecture.
- [ ] Exécuter `./scripts/validate.sh complet`, tests ciblés et `git diff --check`.
- [ ] Satisfaire tous les critères initiaux de HYP-056 ; garder le parent ouvert jusqu'à vérification utilisateur.
