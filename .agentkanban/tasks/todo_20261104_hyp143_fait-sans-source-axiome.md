---
title: "HYP-143 · TODO"
lane: todo
created: 2026-11-04T14:45:00+01:00
updated: 2026-11-04T14:45:00+01:00
description: "Checklist de HYP-143"
---

# Iteration 1

Fichiers : `src/hypomnesis/epistemics/knowledge.py`, `tests/unit/test_knowledge.py` (nouveau ou existant), `tests/property/`, `docs/architecture/` ou `docs/adr/`. Sans GPU.

- [ ] Test rouge : `derive("c.k", 1, "constante", [])` puis `support`, `confidence`, `graph()` / export JSON → `KeyError: 'axiome'`
- [ ] Test rouge : même fait, puis `observe("a", …)` et `retract_source` de `a` → `c.k` ne doit pas être invalidé
- [ ] Trancher entre l'option A (source `axiome` déclarée, support `Defaulted`, jamais rétractée) et l'option B (refus explicite) ; inscrire le choix dans la fiche
- [ ] Implémenter l'option retenue dans `derive` (et, pour A, déclarer la source une seule fois par base ; identifiant stable `axiome`)
- [ ] Vérifier `_holds` : une source déclarée non rétractée tient ; une source inconnue ne doit plus faire disparaître un fait en silence
- [ ] Les deux tests rouges passent ; `explain` d'un fait sans prémisse donne une ligne lisible
- [ ] Test de propriétés : rétracter une source ne touche aucun fait dont la provenance ne la mentionne pas
- [ ] Documenter la décision (docstring de `derive`, note ou ADR courte) et la propriété correspondante dans `docs/verification/proprietes.md` si P10/P11 changent de formulation
- [ ] Les tests existants (révision par mesure, réfutation d'hypothèse, rapport M0) restent inchangés
- [ ] `./scripts/validate.sh rapide`, puis `complet` ; commit en français, mettre la tâche en `qa`
