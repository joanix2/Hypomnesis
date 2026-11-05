---
title: "TODO HYP-170 · Budgets, erreurs et traces"
lane: todo
created: 2026-11-05T23:31:24+01:00
updated: 2026-11-05T23:31:24+01:00
description: "Contrôle des appels de service et observabilité des pipelines"
priority: P1
tags: [moteur-symbolique, effets, observabilite]
---

# Itération 1

- [ ] Définir les budgets/délais bornés et la propagation des erreurs/annulations pour une étape.
- [ ] Tester panne, timeout, réponse invalide et annulation, y compris le nettoyage.
- [ ] Garantir/tester qu'une relance ne répète pas un effet non idempotent.
- [ ] Ajouter des traces corrélées étape/service/demande/résultat/échec et documenter les limites.
- [ ] Exécuter tests ciblés et `./scripts/validate.sh complet`, puis satisfaire HYP-170.
