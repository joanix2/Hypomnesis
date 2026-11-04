---
title: "HYP-021 · Lean F1b : records et mise à jour fonctionnelle"
lane: qa
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P1 · M · Vérification formelle (Lean) · dépend de HYP-020"
priority: P1
tags: [certification, lean, metalangage]
---

## Conversation

### user

**Ticket** HYP-021 · **Priorité** P1 · **Taille** M · **Epic** Vérification formelle (Lean) · **Dépend de** HYP-020 · **Labels** lean

#### Contexte

La Core IR a `Record`, `RecordUpdate`, `Field` et le motif `PRecord` ; ils ne sont pas formalisés.

#### Tâches proposées

- Ajouter les types records nominaux à Σ, ainsi que construction, accès, mise à jour et motif.
- Étendre sûreté, correction et complétude de `typeOf`.

#### Critères d'acceptation

- Preuves étendues sans `sorry`.
- Un exemple `#eval` reproduit `examples/basics/tour.hyp` (`deposit`).

#### Fichiers concernés

- `formal/Hypomnesis/Core/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`

### agent

Plan/todo/implémentation, prérequis découvert pour finir HYP-027 :
réutiliser les données nominales monomorphisées de HYP-020. Un record est
une instance nominale à constructeur unique portant un produit de champs
(terminé par unit). Construction, projection et mise à jour sont des formes
dérivées du noyau déjà prouvé, pas des primitives dont on ferait confiance
au certificat. Ajouter leurs lemmes de typage/sûreté et un exemple deposit.

Le décodeur conserve les noms/positions de champs, rejette les doublons,
champs absents/inconnus et mutations de mauvais type ; tous les termes
traduits restent soumis à typeOf. Motifs partiels et ordre source des
variables devront être préservés, pas simplement canonisés au hasard.
Les littéraux string/float restent HYP-150 : ne pas masquer leur refus.

### user

### agent

Implémentation vérifiée, passage en QA (done reste une décision humaine).
Records nominaux à constructeur unique, payload produit/unit ; lemmes de
construction, projection, remplacement, typage et sûreté des opérations
appliquées. Les preuves existantes de correction/complétude restent inchangées.
Deposit calcule 150 et conserve alice, encodée en points de code :
ce n'est pas un support natif des chaînes.

Le pont traite les records génériques/récursifs, mises à jour et motifs
partiels imbriqués. L'ordre source d'évaluation et les emplacements des
variables sont conservés ; la base d'une mise à jour est évaluée une fois.
Les annotations de toutes les définitions émises sont désormais revérifiées,
y compris les valeurs inutilisées, pour interdire la confusion nominale.

Le nouveau test de gardes a révélé un défaut couplé du décodeur : un
`return` dans la branche monadique quittait decCases avant de construire
le case. Corrigé en produisant l'ite avec pure ; garde fausse puis garde
vraie et permutations de champs sont maintenant testées.

Validation : 25 tests d'intégration Lean passent ; validation complète
verte (Python, Codegen, linters, Lean et audit). Aucun sorry/nouvel axiome :
propext et Quot.sound seulement. Catalogue P21–P23 et documentation actualisés.
Couverture remesurée : 1/6 accepté ; plaque atteint désormais string,
plus record Knowledge.t. HYP-027 reste ouvert, sans exemption de succès.

### user
