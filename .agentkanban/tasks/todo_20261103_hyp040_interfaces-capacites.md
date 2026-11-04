---
title: "HYP-040 · TODO"
lane: todo
created: 2026-11-04T14:30:00+01:00
updated: 2026-11-04T14:30:00+01:00
description: "Checklist de HYP-040"
---

# Iteration 1

Périmètre : module **nouveau** `src/hypomnesis/capabilities/` (aucun fichier existant modifié, sauf `TECHNICAL.md`). Sans GPU. Aucun concept de domaine (test `test_engine_contains_no_domain`).

- [ ] Lire §6 du cahier des charges et §4.4 de `docs/architecture/m3-metalangage.md` ; lister dans le ticket les neuf interfaces retenues (Observer, Estimator, Reasoner, Solver, Validator, Actuator, Explainer, Learner, Resolver : ajuster à la liste exacte du §6) et le rôle type-théorique de chacune
- [ ] `capabilities/result.py` : `Result[T]` immuable (`value`, `certificate`, `diagnostics`, `ok`) et `Diagnostic` (code, message, gravité) ; un appel ne lève jamais d'exception brute
- [ ] `capabilities/protocols.py` : un `typing.Protocol` par interface, signatures typées, indépendant du backend (aucun import de `z3`, `sklearn`, etc.)
- [ ] Docstring de chaque protocole : renvoi au §6 et au §4.4 (estimateur = proposer une métavariable ; validateur = rendre un certificat…)
- [ ] `capabilities/safe.py` : décorateur ou fonction `guarded(call)` qui convertit toute exception d'un plugin en `Result` avec diagnostic (jamais d'exception brute vers le noyau)
- [ ] `capabilities/__init__.py` : exports publics
- [ ] `tests/unit/test_capabilities.py` : un plugin factice par interface passe un test de conformité (`isinstance` sur protocole `runtime_checkable` + appel nominal)
- [ ] Test : un plugin qui lève une exception rend un `Result` en échec avec diagnostic, sans propager
- [ ] Pyright strict sur le module (ajouter `src/hypomnesis/capabilities` à la config stricte si elle est par liste), Ruff
- [ ] Vérifier que `tests/unit` du test d'architecture (aucun domaine dans M3) passe toujours
- [ ] `TECHNICAL.md` : section « Capacités » (interfaces, `Result`, règle « jamais d'exception brute »)
- [ ] Noter dans HYP-041 (registre) la forme retenue des protocoles
- [ ] `./scripts/validate.sh complet`, commit en français, mettre la tâche en `qa`
