---
title: "HYP-023 · Polymorphisme de rang 1 prouvé et branché"
lane: doing
created: 2026-11-05T15:27:39+01:00
updated: 2026-11-05T15:27:39+01:00
description: "Types paramétriques, schémas, preuves et vrai List.map via le checker."
priority: P1
tags: [certification, lean, metalangage]
---

## Itération 1 — plan approuvé

- [x] Fixer le périmètre : rang 1, arguments et récursion monomorphes, pas de preuve de W.
- [x] Inventorier le vrai List.map, ses dépendances et la monomorphisation actuelle.
- [x] Types ouverts et données paramétriques ; substitutions sans capture et portées prouvées.
- [x] Généralisation, instanciation et typage des termes et environnements.
- [ ] Préservation par substitution, sûreté, correction/complétude de typeOf.
- [ ] Conserver les preuves records, couverture/Certified, motifs et fuel.
- [ ] Brancher le décodeur de certificats et le vrai CLI, compatibilité 1.0/1.1.
- [ ] Vérifier le véritable List.map, ses dépendances et plusieurs types dans un même programme.
- [ ] Vérifier let-polymorphe local, captures, certificats altérés et refus hors fragment.
- [ ] Documentation, catalogue, audit ; validations Lean/complet/graphe/rapide.
- [ ] QA après satisfaction des critères, commit local sans push ; done humain.

## Itération 2 — jalon des fondations

- [x] Lois d'identité/composition, renommage, protection des variables liées et portées.
- [x] Instanciation des schémas : arité, bonne portée et commutation avec la substitution.
- [x] Déclarations nominales paramétriques et portée des arguments de constructeurs.
- [x] Régressions Lean positives/négatives, import central, catalogue et audit.
- [x] Valider le jalon avec Lean, contrôle rapide et graphe ; commit local.

## Itération 3 — environnements de schémas

- [x] Représenter les contextes de variables par des schémas instanciables.
- [x] Prouver la conservation de portée et la commutation substitution/instanciation dans un contexte.
- [x] Ajouter les régressions map int→bool, arité invalide et variable de type extérieure.
- [x] Documenter et auditer les propriétés de contexte P40.
- [ ] Étendre les termes et le jugement de typage polymorphe ; brancher cette vérification au noyau.
- [x] Valider le jalon : Lean/audit, 500 différentiels, validation rapide et graphe.
- [x] Committer le jalon localement, sans push (9bc234e).

## Itération 4 — termes et checker déclaratif

- [x] Ajouter les termes à instanciation explicite et les liaisons let-polymorphes.
- [x] Implémenter le checker exécutable et le jugement déclaratif, avec les portées vérifiées.
- [x] Prouver l'équivalence correction/complétude sous une signature bien formée et un environnement bien scopé.
- [x] Prouver que l'égalité booléenne des types reflète l'égalité structurelle.
- [x] Ajouter les régressions positives/négatives, l'audit d'axiomes et la documentation P41.
- [x] Prouver la préservation du typage par substitution des types dans les termes et environnements.
- [ ] Relier la sûreté au véritable évaluateur en préservant les preuves de motifs, records, couverture et fuel.
- [ ] Brancher le décodeur/CLI et vérifier le véritable `List.map` avec plusieurs instanciations.
- [x] Valider le jalon avec Lean/audit, cohérence Kanban et mise à jour Graphify ; garder HYP-023 en `doing`.

## Itération 5 — sûreté du runtime polymorphe

- [x] Analyser le modèle Core de sûreté et confirmer qu'un effacement monomorphe direct ne couvre pas plusieurs instanciations d'un même schéma ou d'une donnée paramétrique.
- [x] Ajouter une régression combinant le type vérifié et l'évaluation Core d'un `let` identité utilisé à `int` et `bool` dans le même programme.
- [x] Prouver que l'effacement et l'évaluation Core commutent avec la substitution de types, et transporter conditionnellement l'absence de `stuck`.
- [x] Établir un pont de sûreté vérifié pour le fragment sans fonction ni liaison (constantes, conditions, produits, projections, opérations binaires).
- [x] Étendre le pont aux `let` monomorphes inutilisés, avant d'ajouter la lecture de variables, et prouver la sûreté du véritable évaluateur à tout fuel.
- [x] Étendre le fragment aux lectures de variables sous schémas d'arité zéro et ajouter une régression d'un `let` mono utilisé.
- [x] Étendre le fragment aux lambdas et applications monomorphes, préserver l'évaluation des fermetures et prouver un cas de capture lexicale.
- [x] Étendre le fragment aux fermetures récursives monomorphes et prouver la sûreté à tout fuel d'un compte à rebours typé.
- [x] Vérifier la sûreté de la valeur concrète produite par le `let` identité utilisé à `int` et `bool` à fuel fixé, sans la présenter comme un théorème général.
- [x] Ajouter un terme récursif `List.map`-équivalent vérifié puis exécuté avec deux instanciations dans un programme Lean.
- [x] Définir la relation `RuntimeEnvRel` entre valeurs Core et environnements de schémas monomorphes d'arité zéro.
- [x] Prouver la sûreté à fuel arbitraire pour le véritable `Core.eval` sur le fragment runtime monomorphe borné, en préservant timeout/erreur/matchFail.
- [ ] Définir une relation polymorphe de valeurs et d'environnements qui interprète les schémas sous toutes leurs instanciations, y compris les fermetures polymorphes.
- [ ] Étendre la sûreté à fuel arbitraire au fragment polymorphe général, sans réduire la sûreté des motifs, records, couverture certifiée ou fuel.
- [ ] Étendre le pont aux motifs, records et `Coverage.Certified` sans affaiblir les garanties existantes.
- [ ] Ajouter l'audit d'axiomes, les régressions de let-polymorphe multi-instancié et de données paramétriques, puis documenter le pont prouvé.
