---
title: "TODO HYP-166 · Bindings hôte"
lane: todo
created: 2026-11-05T23:31:24+01:00
updated: 2026-11-05T23:31:24+01:00
description: "Adaptateurs existants, résolution configurable, deux fournisseurs compatibles"
priority: P1
tags: [metalangage, moteur-symbolique, contrats, effets]
---

# Itération 1

- [ ] Reprendre les contrats de HYP-165 et le registre/décorateurs d'adaptateurs existants.
- [ ] Laisser l'hôte configurer les instances et résoudre un binding sans FFI arbitraire depuis `.hyp`.
- [ ] Tester le même programme avec deux fournisseurs compatibles et les erreurs de binding/contrat/indisponibilité.
- [ ] Documenter l'articulation avec les adaptateurs existants et exécuter tests ciblés puis `./scripts/validate.sh complet`.
- [ ] Satisfaire HYP-166 sans imposer de protocole ou fournisseur non demandé.
