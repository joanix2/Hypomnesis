---
title: "HYP-143 · TODO"
lane: doing
created: 2026-11-04T14:45:00+01:00
updated: 2026-11-04T14:55:00+01:00
description: "Checklist de HYP-143"
priority: P1
tags: [bug, epistemique, moteur-symbolique, python]
---

# Iteration 1

Fichiers : `src/hypomnesis/epistemics/knowledge.py`, `tests/unit/test_knowledge.py` (nouveau ou existant), `tests/property/`, `docs/architecture/` ou `docs/adr/`. Sans GPU.

- [x] Test rouge : `derive("c.k", 1, "constante", [])` puis `support`, `confidence`, `graph()` / export JSON → `KeyError: 'axiome'`
- [x] Test rouge : même fait, puis `observe("a", …)` et `retract_source` de `a` → `c.k` ne doit pas être invalidé
- [x] Option A retenue par l'utilisateur : inscrire le choix dans la fiche et la docstring de `derive`
- [x] Implémenter l'option A dans `derive` : source `axiome` (type `default`, support « par défaut », confiance 1,0) déclarée une fois par base, jamais rétractée ; ajouter une garde : `retract_source("axiome", …)` refusé avec une erreur claire
- [x] Vérifier `_holds` : une source déclarée non rétractée tient ; une source inconnue ne doit plus faire disparaître un fait en silence
- [x] Les deux tests rouges passent ; `explain` d'un fait sans prémisse donne une ligne lisible
- [x] Test de propriétés : rétracter une source ne touche aucun fait dont la provenance ne la mentionne pas
- [x] Documenter la décision (docstring de `derive`, note ou ADR courte) et la propriété correspondante dans `docs/verification/proprietes.md` si P10/P11 changent de formulation (formulation inchangée : fiche + `TECHNICAL.md`, section HYP-008)
- [x] Les tests existants (révision par mesure, réfutation d'hypothèse, rapport M0) restent inchangés (deux tests de `test_knowledge_graph.py` qui figeaient le bug ont été réécrits, cf. fiche)
- [ ] `./scripts/validate.sh rapide` (vert), puis `complet` (bloqué par des erreurs pyright/ruff d'autres agents hors périmètre : à relancer) ; mettre la tâche en `qa` ensuite
