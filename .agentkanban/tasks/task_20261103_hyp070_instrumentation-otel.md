---
title: "HYP-070 · Instrumentation OpenTelemetry (traces)"
lane: qa
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P1 · M · Phase 6 — Observabilité · dépend de HYP-044"
priority: P1
tags: [observabilite, outillage, python]
---

## Conversation

### user

**Ticket** HYP-070 · **Priorité** P1 · **Taille** M · **Epic** Phase 6 — Observabilité · **Dépend de** HYP-044 · **Labels** python, observabilité

#### Contexte

§12.3 : un identifiant d'exécution et les spans `hypomnesis.run`, `language.parse`, `language.typecheck`, `observer.read`, … ; ADR 0005.

#### Tâches proposées

- `observability/tracing.py` ; spans aux étapes listées au §12.3, avec les attributs recommandés.
- Propagation du `trace_context` dans l'enveloppe de message.
- Désactivable sans changer aucun résultat.

#### Critères d'acceptation

- Une exécution du scénario produit l'arbre de spans du §12.3.
- Résultats identiques avec ou sans télémétrie (test).

#### Fichiers concernés

- `src/hypomnesis/observability/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`

### agent

Plan / todo / implement du lot P1 approuvé. Étendre la façade Tracer
existante, conserver ses fournisseurs privés et son format de rapport.
Racine couvrant parsing/typage/exécution ; instrumentation aux opérations
réelles, extraction/injection W3C et OTLP local explicite. Pas de span LLM
fictif. Activer/désactiver via configuration hôte/CLI ; exporter avec délai
borné, signaler les erreurs de télémétrie sans modifier les résultats.

Tests : arbre réel du MVP, contexte distant et invalide, isolation
concurrente, export OTLP reçu par un collecteur local de test et comparaison
des résultats/faits/journal/commandes avec et sans télémétrie. Validation
complète/rapide/graphe avant QA et commit ; aucun push.

### user

### agent

Implémentation en place : façade ContextVar, configuration hôte/CLI par
environnement, providers fermés, exporteur officiel OTLP HTTP local
(requêtes bornées, sans proxy ni redirection), propagation des enveloppes
et extraction W3C/tracestate. Les spans des fonctions pures sont déclarés
en M2 par `tracing`, contrôlés statiquement et ouverts à l'application
réelle de la valeur, sans arguments/résultats. Les capteurs, schémas,
solveur, connaissances, autorisations, exécutions et vérifications restent
instrumentés aux frontières existantes.

Les tests ciblés passent, dont une vraie réception de protobuf OTLP par
un serveur HTTP local, refus/redirection, threads/tâches asynchrones,
capteur/export réels, rejeu, absence d'appel doublonné et invariance
des résultats. La première validation complète a révélé trois régressions
de topologie dans les tests existants : suppression d'un niveau de span
superflu et déduplication du wrapper historique `trace_actuator`.
Les tests d'origine sont maintenant verts sans modifier leurs attentes.
Nouvelle validation complète requise avant QA ; le lot P1 n'est pas terminé.

### user

### agent

La nouvelle validation complète est verte (linters/types, suites moteur et
Codegen, noyau Lean et corpus différentiels). Les tests de régression de
topologie et les tests OTLP locaux sont verts. Graphe AST/relations Kanban
reconstruits sans appel LLM. Passage en QA pour revue humaine ; la clôture
`done` n'est pas automatique. Commit local du jalon, sans push.

### user
