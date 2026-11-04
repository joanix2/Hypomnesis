---
title: "HYP-055 · Validateurs et contre-exemples"
lane: qa
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P1 · M · Phase 4 — Raisonnement hybride · dépend de HYP-052"
priority: P1
tags: [capacites, moteur-symbolique, python, solveurs, tests, validateurs]
---

## Conversation

### user

**Ticket** HYP-055 · **Priorité** P1 · **Taille** M · **Epic** Phase 4 — Raisonnement hybride · **Dépend de** HYP-052 · **Labels** python

#### Contexte

§11.6 : vérification des résultats et production éventuelle de contre-exemples.

#### Tâches proposées

- Interface `Validator` concrète : rend une preuve d'acceptation ou un contre-exemple vérifiable.
- Validateur géométrique pour la plaque.

#### Critères d'acceptation

- Un rejet est toujours accompagné d'un contre-exemple que l'on peut revérifier indépendamment.

#### Fichiers concernés

- `src/hypomnesis/engine/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`

### agent

Plan HYP-055 : Validator générique de fonction Hypomnesis pure, entrée
nominale fermée contrôlée par TypeCodec, sortie liste de violations.
Acceptation avec certificat rejouable, rejet logique avec contre-exemple
contenant l'entrée complète et les violations. Le rejeu utilise une fonction
de confiance configurée par l'hôte, jamais du code désigné par le certificat.
Erreurs d'entrée et panne du vérificateur restent distinctes d'une réfutation.

Le validateur géométrique est un adaptateur de Plaque.verifier en M2,
sans logique de plaque dans le moteur. Corriger le cas épaisseur zéro
(division avant rejet) et les dimensions non positives. Tester le rejeu
dans une session indépendante et la falsification des témoins, puis
validation complète et QA. Le certificat est computationnel, pas Lean.

### user

### agent

HYP-055 terminé et proposé en QA. LanguageValidator respecte le protocole
Validator, contrôle et capture l'entrée par TypeCodec, puis exécute une
fonction M2 pure. Chaque rejet logique contient la proposition complète et
les violations ; chaque acceptation possède un certificat rejouable.
Le rejeu recalcule les violations avec le vérificateur de confiance de
l'hôte, jamais une fonction choisie par le témoin.

Plaque.verifier_proposition est le validateur géométrique concret, sans
règle métier Python. Dimensions/masse maximale non positives et épaisseur
nulle sont rejetées explicitement, sans division par zéro. Erreur d'entrée
ou panne du vérificateur est diagnostiquée séparément, sans être transformée
en réfutation mathématique. Une acceptation ne promeut pas le support.

18 tests unitaires nouveaux, incluant huit rejets géométriques rejoués dans
une session indépendante, falsification des témoins, erreurs et conservation
du support Estimated. Tests ciblés et validation complète verts (moteur,
Codegen, types, schémas, Lean et certificat). Guide validateurs et TECHNICAL
mis à jour ; aucune preuve Lean nouvelle revendiquée, aucun sous-agent.

### user
