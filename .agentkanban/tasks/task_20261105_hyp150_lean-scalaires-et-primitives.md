---
title: "HYP-150 · Lean : réels, chaînes et primitives du fragment certifiable"
lane: qa
created: 2026-11-05T00:30:00+01:00
updated: 2026-11-05T00:30:00+01:00
description: "P1 · L · Vérification formelle — prérequis de couverture totale HYP-027"
priority: P1
tags: [certification, compilateur, lean, metalangage]
---

## Conversation

### user

**Ticket** HYP-150 · **Priorité** P1 · **Taille** L · **Epic** Vérification formelle · **Dépend de** HYP-020, HYP-026 · **Labels** lean

#### Contexte

Le pont HYP-027 appelle réellement Lean mais cinq des six exemples actuels
sont hors fragment. L'audit indépendant rencontre d'abord string dans tour,
float dans units/plate/regles et un record Knowledge.t dans plaque.
Les records relèvent de HYP-021 ; ce ticket couvre le manque scalaire,
sans transformer les refus en acceptations de confiance.

#### Tâches proposées

- Fixer explicitement la sémantique des flottants/réels et des chaînes.
- Étendre syntaxe, valeurs, typage, évaluation et preuves de sûreté/correction.
- Déclarer les signatures et le comportement des primitives couvertes,
  sans autoriser une signature arbitraire fournie par le certificat.
- Étendre le décodeur et les tests différentiels ; préserver les codes
  distincts pour les autres formes encore hors fragment.

#### Critères d'acceptation

- Preuves sans sorry ni axiome supplémentaire non audité.
- Exemples scalaires acceptés par le vrai checker, certificats altérés refusés.
- Couverture mesurée des exemples mise à jour ; aucune garantie de raffinement
  Python non prouvée.

#### Fichiers concernés

- `formal/Hypomnesis/Core/`
- `formal/Hypomnesis/Certificate.lean`
- `docs/verification/`
- `tests/integration/test_lean_checker.py`

### agent

Besoin découvert pendant l'implémentation HYP-027 ; non implémenté ici.
L'élargissement formel ne peut pas être remplacé par une validation Python
ou une liste d'exemptions. À combiner avec HYP-021 et les autres limites
rencontrées ensuite pour obtenir réellement tous les exemples certifiés.

### user

### agent

Plan/todo/implémentation, après HYP-021 validé et committé 3ced042.
Choix scalaire : Float Lean 4.35 (binary64, pas des réels mathématiques),
dont add/sub/mul/div possèdent maintenant un modèle logique dans Lean ;
String Lean (séquences Unicode, pas des octets). Les comparaisons IEEE
et l'ordre total de compare doivent rester distincts, notamment pour NaN.
Ne pas remplacer les chaînes par des listes dans le certificat.

Étendre les primitives par un catalogue fermé de signatures et des règles
de typage réelles, avec une erreur runtime explicite pour division entière
par zéro et failwith ; ne pas assimiler ces erreurs à stuck/Match_failure.
Conserver P1–P7, étendre les preuves et l'audit sans sorry. Tester les résultats
Python/Lean (arrondis, zéro signé, NaN, Unicode, refus des mutations) avant
de remesurer les exemples. Implémenter d'abord les opérations atteignables ;
toute primitive non modélisée doit continuer à être refusée.

Les autres limites révélées ensuite (motifs alternatifs/alias, comparaison
structurelle, racines polymorphes) devront être traitées explicitement,
pas contournées par une modification des exemples ou des racines.

### user

### agent

Implémentation scalaire terminée et validation complète verte : passage QA.
Float binary64, String Unicode, motifs littéraux et catalogue fermé de
primitives ; sûreté, correction/complétude, unicité et budgets étendus.
Les erreurs explicites de division/modulo entiers et failwith ne sont ni
stuck ni Match_failure. L'ordre des NaN reproduit compare du runtime,
y compris pour <, <=, >, >= ; l'égalité reste IEEE.

Le format 1.1 est nécessaire pour conserver le zéro négatif : le parseur
JSON Lean perdait son signe. Bits finis bornés et concordance vérifiés ;
ancien schéma 1.0 intact, loader Python compatible, réexport requis pour
ses anciens floats côté Lean. ADR 0015 proposée pour revue, pas adoptée
à la place de l'utilisateur.

68 tests ciblés de certification/round-trip passent, dont sous-normaux,
arrondis, débordement, NaN, -0.0, Unicode, erreurs et mutations. Validation
complète : linters/Pyright configuré, Python, Codegen, Lean et audit verts.
L'audit inclut désormais Classical.choice du modèle Float standard, déjà
autorisé par la politique ; aucun sorry ni axiome maison.

Couverture mesurée : 5/6 exemples acceptés. Tour est maintenant bloqué
uniquement sur le premier motif alternatif rencontré. HYP-027 reste doing ;
la dernière extension du décodeur devra conserver l'ordre des alternatives
et ne pas essayer la seconde après une première correspondance à garde fausse.

### user
