---
title: "HYP-024 · TODO"
lane: todo
created: 2026-11-03T18:30:00+01:00
updated: 2026-11-03T18:30:00+01:00
description: "Checklist de HYP-024"
---

# Iteration 1

- [x] `generalize` rend les variables quantifiées ; `instantiate` rend les arguments
- [x] Champs d'annotation dans `ir/core.py` (compare=False, défauts neutres)
- [x] Remplissage par le `Checker` : lambdas, let, let rec, variables, constructeurs, records, let-motifs, définitions
- [x] Passe `close` (défaut `unit`) et vérificateur `annotation_problems`
- [x] Tests : invariant sur le prélude et tous les exemples, cas ciblés (polymorphisme, instanciation, défaut)
- [x] Note de correspondance dans `formal/Hypomnesis/Core/Syntax.lean`
- [x] `./scripts/validate.sh complet`, commit
