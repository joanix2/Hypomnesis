---
title: "HYP-044 · Adaptateur de backend Python générique"
lane: doing
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-04T18:22:06+01:00
description: "P0 · M · Phase 3 — Extensions et contrats · dépend de HYP-041, HYP-042"
priority: P0
tags: [capacites, contrats, moteur-symbolique, python]
---

## Conversation

### user

**Ticket** HYP-044 · **Priorité** P0 · **Taille** M · **Epic** Phase 3 — Extensions et contrats · **Dépend de** HYP-041, HYP-042 · **Labels** python

#### Contexte

§6.2 : premier backend. Un appel valide l'entrée, appelle l'adaptateur, valide la sortie et enregistre le résultat.

#### Tâches proposées

- Charger l'`entry_point` du manifeste ; isoler les erreurs ; appliquer `timeout_seconds`.
- Validation JSON Schema en entrée et en sortie de chaque appel.
- Rendre l'appel disponible au langage via une primitive déclarée (pas d'accès Python arbitraire).

#### Critères d'acceptation

- Une sortie non conforme est rejetée et journalisée ; le programme reçoit une erreur typée.

#### Fichiers concernés

- `src/hypomnesis/backends/python/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`

### agent

Plan parallèle approuvé : HYP-044, HYP-051 et HYP-148 sur trois branches/worktrees,
intégration locale séquentielle, aucun push. HYP-044 réutilise PreparedExtension,
TypeCodec et NativeRegistry sans modifier leur API partagée. Un sous-processus
par appel assure un timeout réel (démarrage/import compris), avec arrêt et récolte ;
ce n'est pas un bac à sable de sécurité. Contrats avant import et après appel,
erreurs typées accessibles au langage et trace structurée. Les analyses statiques
ne chargent aucun plugin. Pas de changement Core IR ni de sémantique du runtime.

Surfaces réservées : `src/hypomnesis/backends/python/`, tests dédiés et
`docs/architecture/backend-python.md`. Le coordinateur conserve les tickets,
checklists, documents centraux et reconstructions Graphify. Toute adaptation
d'interface commune doit lui être signalée. Checklist créée avant implémentation.

### user
