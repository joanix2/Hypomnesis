---
title: "HYP-020 · TODO"
lane: todo
created: 2026-11-03T19:30:00+01:00
updated: 2026-11-03T19:30:00+01:00
description: "Checklist de HYP-020"
---

# Iteration 1

- [x] Syntaxe : `Ty.data`, `Pat`, `Expr.construct/case/fail`, signature `Sig`
- [x] Typage : `PatTy`, `HasType Σ`
- [x] Évaluation : `Val.con`, `Res.matchFail`, `matchPat`
- [x] Sûreté : `ValTy Σ`, lemme de filtrage, `eval_safe` étendu
- [x] Vérificateur : `patTypeOf`, `typeOf Σ` correct et complet, unicité, décidabilité
- [x] Budget : `eval_fuel_mono` étendu
- [x] Exemple : longueur d'une liste d'entiers (`#eval`)
- [x] `proprietes.md`, audit, `./scripts/validate.sh lean` puis `complet`, commit
