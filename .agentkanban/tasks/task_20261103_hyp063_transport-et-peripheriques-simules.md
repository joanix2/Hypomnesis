---
title: "HYP-063 · Transport JSON par fichiers et périphériques simulés"
lane: qa
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P0 · M · Phase 5 — Effets et actionneurs · dépend de HYP-062"
priority: P0
tags: [contrats, effets, moteur-symbolique, python]
---

## Conversation

### user

**Ticket** HYP-063 · **Priorité** P0 · **Taille** M · **Epic** Phase 5 — Effets et actionneurs · **Dépend de** HYP-062 · **Labels** python

#### Contexte

§9.5 : fichiers JSON pour le MVP, contrat séparé du transport ; capteurs et actionneurs simulés.

#### Tâches proposées

- Interface de transport ; implémentations mémoire et fichiers.
- Capteur de température simulé, actionneur de ventilateur simulé, avec manifestes et schémas.
- Enregistrement et rejeu de scénarios.

#### Critères d'acceptation

- Tous les messages passent par l'enveloppe `envelope/1.0.0`.
- Un scénario enregistré se rejoue à l'identique.

#### Fichiers concernés

- `src/hypomnesis/effects/transports/`
- `examples/robotics/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`

### agent

Plan puis implémentation dans la chaîne P0 : ajouter une interface FIFO commune
et des transports mémoire/JSONL, validant enveloppe et charge à l'entrée comme
à la lecture. Un fichier append-only est le scénario enregistré ; le rejeu
restitue les messages exacts (identifiants, horodatage, corrélation compris),
sans rejouer d'effet physique ni fabriquer de nouveaux relevés.

Réutiliser la pièce simulée du langage M2 ventilation et ses contrats plutôt
que déplacer le domaine dans le moteur. Tous ses échanges capteur, commande
et réponse traverseront le transport ; le choix mémoire/fichiers appartient
à l'environnement hôte. Ajouter les manifestes des périphériques et un exemple
robotique reproductible. Les transports MVP sont synchrones et mono-processus ;
aucune garantie de concurrence ni de livraison physique unique n'est ajoutée.

### user

### agent

Implémentation validée : interface Transport, FIFO mémoire et FIFO fichiers
JSONL, validation stricte de chaque enveloppe et de sa charge à l'envoi et
à la réception. Les fichiers corrompus, clés dupliquées et lignes incomplètes
sont signalés sans avancer le curseur. Les charges sont détachées.

La pièce simulée M2 ventilation transporte désormais requêtes, relevés,
commandes et réponses corrélées ; contrats et deux manifestes descriptifs
validés. L'hôte choisit mémoire ou fichiers ; chaque exécution fichiers
produit un scénario distinct sans écrasement. Aucun domaine ajouté au moteur.

Le rejeu conserve exactement métadonnées et charges sans réexécuter d'action
physique. L'exemple `examples/robotics/transport.py` a été exécuté dans un
répertoire temporaire : six messages rejoués à l'identique, puis nettoyage.
Les tests couvrent les deux transports, refus avant ajout, FIFO, corruption,
instantanés, rejeu complet et scénario ventilation réel.

`./scripts/validate.sh complet` est vert : 828 tests moteur et 77 Codegen,
linters, Pyright, contrats, Kanban, Lean et audit des axiomes.
Documentation : `docs/architecture/transports.md`. Passage en QA ;
la clôture done reste humaine.

### user
