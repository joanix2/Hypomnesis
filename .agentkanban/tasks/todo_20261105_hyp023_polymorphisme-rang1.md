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
- [ ] Généralisation, instanciation et typage des termes et environnements.
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
