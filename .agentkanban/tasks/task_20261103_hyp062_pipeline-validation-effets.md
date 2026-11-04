---
title: "HYP-062 · Permissions et pipeline de validation des effets"
lane: qa
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P0 · M · Phase 5 — Effets et actionneurs · dépend de HYP-061, HYP-042"
priority: P0
tags: [contrats, effets, moteur-symbolique, python, securite, validateurs]
---

## Conversation

### user

**Ticket** HYP-062 · **Priorité** P0 · **Taille** M · **Epic** Phase 5 — Effets et actionneurs · **Dépend de** HYP-061, HYP-042 · **Labels** python

#### Contexte

§9.8 : structure JSON, contrat, permissions, contraintes métier, sécurité, puis exécution ; validation humaine possible.

#### Tâches proposées

- `effects/permissions.py` : politiques de permissions déclaratives.
- `effects/dispatcher.py` : applique les étapes 1 à 9 du §9.8 dans l'ordre, journalise chacune.
- Point d'extension pour une validation humaine obligatoire.

#### Critères d'acceptation

- Une commande invalide est rejetée avant tout appel d'actionneur (critère §16.4).
- Une action non autorisée ne peut pas être exécutée (critère §16.4).
- Le journal permet de reconstruire la trace de chaque commande.

#### Fichiers concernés

- `src/hypomnesis/effects/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`

### user

objectif finir les P0

### agent

Réutiliser le dispatcher et son automate validés par HYP-061. Compléter
les étapes absentes : structure JSON stricte, journal de contrôles, politique
déclarative, sécurité, validation humaine et observation finale. Préserver
les signatures existantes par défaut et tester la réponse simulée comme la
réponse réelle. Les nouvelles extensions seront synchrones et explicites ;
une absence d'approbation obligatoire doit refuser la commande.

### user

### agent

Implémentation vérifiée : politique déclarative exacte avec refus prioritaire,
contrôle JSON strict et contrats avant appel, contraintes métier, sécurité et
accord humain explicite fourni seulement par l'hôte. Les réponses simulées et
réelles passent la même frontière JSON/contrat ; les erreurs de validation ou
de simulation sont des refus explicites, jamais des succès partiels réutilisables.

Le journal `Outcome.checks`, exporté dans `commands[].checks`, complète
l'historique de l'automate. Après exécution, le résultat est enregistré avant
l'observation réelle optionnelle ; un échec d'observation conserve ce résultat
et termine en Failed sans rejouer l'action. `run_procedure` expose la politique
et l'accord humain à l'hôte. Déduplication et relances existantes préservées.

Tests ajoutés : ordre exact, refus à chaque précondition sans appel d'actionneur,
refus prioritaires, accord strictement True, identité de commande, copies des
charges pour validation, erreurs des callbacks, schémas manquants, réponses JSON
non conformes même sous contrat ouvert, simulation, observation et rapport réel.

`./scripts/validate.sh complet` est vert : 798 tests moteur + 77 Codegen,
linters, Pyright, contrats, Kanban, Lean et audit des axiomes. Guide :
`docs/architecture/validation-effets.md`. Aucune nouvelle garantie Lean n'est
revendiquée ; les preuves HYP-065/066 restent à traiter. Passage en QA,
clôture done réservée à l'utilisateur.

### user
