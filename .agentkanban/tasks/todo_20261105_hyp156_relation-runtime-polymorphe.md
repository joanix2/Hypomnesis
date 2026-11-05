---
title: "TODO HYP-156 · Relation runtime polymorphe"
lane: todo
created: 2026-11-05T23:31:24+01:00
updated: 2026-11-05T23:31:24+01:00
description: "Relation de valeurs/environnements et sûreté du véritable évaluateur"
priority: P1
tags: [certification, lean, metalangage]
---

# Itération 1

- [ ] Définir précisément la relation de valeurs/environnements pour les schémas et instanciations du fragment retenu.
- [ ] Prouver le pont de typage et de sûreté à tout fuel vers le véritable `Core.eval`, en explicitant les résultats non terminaux.
- [ ] Ajouter les régressions multi-instanciées pour une liaison et une fermeture polymorphes.
- [ ] Auditer les théorèmes, documenter le fragment et ses limites dans le catalogue et `TECHNICAL.md`.
- [ ] Exécuter Lean/audit, `./scripts/validate.sh complet` et `git diff --check`.
- [ ] Satisfaire les critères de HYP-156 ; toute propriété nouvelle est inscrite dans l'audit et la documentation.

# Itération 2 — régression polymorphe concrète, généralité toujours ouverte

- [ ] Définir la relation logique générale de valeurs/environnements polymorphes.
- [ ] Prouver la sûreté du fragment général à tout fuel à partir de cette relation.
- [x] Renforcer l'exemple `let` identité partagé entre `int` et `bool` jusqu'à une preuve de sûreté à tout fuel, en conservant `timeout`.
- [x] Auditer et documenter P49 comme régression concrète ; expliciter pourquoi elle ne satisfait pas le théorème général.
- [x] Exécuter `./scripts/validate.sh lean`, `./scripts/validate.sh complet`, `kanban.py check`, Graphify et `git diff --check`.
- [ ] Satisfaire les critères d'acceptation de HYP-156 ; garder le ticket ouvert tant que les deux premiers items ne sont pas prouvés.

# Itération 3 — relation logique et fragment d'applications de fermetures

- [x] Définir `PolyValueRel`, `PolySchemeRel` et `PolyRuntimeEnvRel` avec interprétation relationnelle universelle des variables liées, transport par substitution et lecture polymorphe.
- [x] Relier la valeur identité source, son effacement réel, le schéma `forall a. a -> a` et ses instanciations `int`/`bool`.
- [x] Prouver, pour toute fermeture et tout argument reliés à un type d'ordre zéro, la sûreté du corps évalué par le véritable `Core.eval` à tout fuel ; timeout, `matchFail` et erreurs explicites restent permis, seul `stuck` est exclu.
- [x] Ajouter les applications runtime `int` et `bool` de la même fermeture, à tout fuel, en complément de P49 sur le `let` complet.
- [x] Auditer les nouveaux théorèmes sous P50 et préciser les frontières du fragment dans `TECHNICAL.md` et le catalogue.
- [x] Exécuter l'audit/build Lean, la validation complète, les contrôles Kanban/Graphify et `git diff --check`.
- [x] Vérifier la frontière contre les critères de HYP-156 : ils sont satisfaits pour le fragment annoncé ; ne pas revendiquer le théorème fondamental sur toutes les dérivations `HasType`.

# Itération 4 — validations finales et portée d'acceptation

- [x] Régénérer les artefacts Lean par `./scripts/validate.sh complet` et confirmer la réussite de l'audit des axiomes P50.
- [x] Exécuter `./scripts/validate.sh graphe`, `./.venv/bin/python scripts/kanban.py check` et `git diff --check`.
- [x] Confirmer que `PolyRuntimeFragment` satisfait la portée d'acceptation de HYP-156 ; les formes exclues restent hors de cette conclusion et du suivi HYP-023/HYP-157/HYP-158.
