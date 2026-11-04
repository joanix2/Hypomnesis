---
title: "HYP-052 · Backend Z3 depuis la Problem IR"
lane: qa
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P0 · M · Phase 4 — Raisonnement hybride · dépend de HYP-051, HYP-044"
priority: P0
tags: [moteur-symbolique, python, solveurs]
---

## Conversation

### user

**Ticket** HYP-052 · **Priorité** P0 · **Taille** M · **Epic** Phase 4 — Raisonnement hybride · **Dépend de** HYP-051, HYP-044 · **Labels** python

#### Contexte

Solveur initial du §15.1. Z3 n'est pas digne de confiance : il rend un certificat (modèle) vérifié ensuite.

#### Tâches proposées

- Traduire la Problem IR en Z3 (entiers, réels, booléens, contraintes linéaires).
- Rendre `sat` avec un modèle, `unsat`, ou `unknown`, avec la durée.

#### Critères d'acceptation

- Le scénario MVP est résolu ; le modèle est renvoyé dans les types Hypomnesis.

#### Fichiers concernés

- `src/hypomnesis/backends/z3/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`

### agent

Plan HYP-052 : préserver les problèmes réels existants, ajouter domaines
int/bool explicites, modèle exact (Fraction/int/bool), durée et raison
d'unknown, limite de temps Z3. Les booléens interviennent dans les contraintes
linéaires par l'encodage explicite faux=0/vrai=1, pas comme nombres ambigus.
Le vérificateur indépendant contrôle aussi le type de chaque affectation.

Versionner l'échange Problem IR en 1.1 tout en relisant 1.0. Ajouter une
enveloppe Problem.typed_problem et Effect.solve_typed sans casser solve.
Le résultat Hypomnesis garde les réels comme rationnels numérateur/dénominateur,
afin de ne pas transformer un modèle exact en float arrondi non vérifié.
Tester les trois domaines, statuts, délais et refus de modèles altérés.

### user

### agent

HYP-052 terminé et proposé en QA. Domaines real/int/bool natifs Z3,
affectations Fraction/int/bool, limite de temps configurable, durée et raison
d'unknown. Les contraintes linéaires utilisent explicitement booléen=0/1 ;
le modèle conserve le type bool, sans confusion avec l'entier.
La variable auxiliaire d'objectif est fraîche.

Problem IR 1.1 est versionnée ; lecture 1.0 préservée, schéma historique
intact. Contrôle indépendant des types/domaines/contraintes, y compris
variables supplémentaires. Le noyau revérifie le modèle même si le plugin
annonce zéro violation.

Problem.typed_problem et Effect.solve_typed restituent un résultat nominal
avec Sat/Unsat/Unknown, scalaires typés et réel rationnel exact (1/3 reste
1/3). Effect.solve garde son API historique, projection float comprise.
Aucun nouveau natif ni forme Core IR ; aucun théorème supplémentaire de
raffinement Python/Lean, d'optimalité ou d'insatisfiabilité n'est revendiqué.

24 tests unitaires nouveaux et 4 tests d'intégration ; 84 tests ciblés
verts. Scénario mécanique préservé et nouveau M1 solveur/domaines.hyp
renvoyant 2, 1/3 et true. Validation complète verte, dont Lean et certificat.
TECHNICAL et guide Problem IR mis à jour. Aucun sous-agent.

### user
