---
title: "HYP-150 · Lean : réels, chaînes et primitives du fragment certifiable"
lane: todo
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
