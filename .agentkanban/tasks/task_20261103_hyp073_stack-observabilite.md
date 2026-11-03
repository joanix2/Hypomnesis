---
title: "HYP-073 · Stack Collector, Prometheus, Grafana, Tempo"
lane: todo
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P1 · M · Phase 6 — Observabilité · dépend de HYP-071"
---

## Conversation

### user

**Ticket** HYP-073 · **Priorité** P1 · **Taille** M · **Epic** Phase 6 — Observabilité · **Dépend de** HYP-071 · **Labels** infra, observabilité

#### Contexte

§12.6 : stack de référence.

#### Tâches proposées

- `monitoring/docker-compose.yml` avec OpenTelemetry Collector, Prometheus, Grafana, Tempo (ou Jaeger).
- Provisionnement automatique des sources de données Grafana.
- Documentation de démarrage.

#### Critères d'acceptation

- `docker compose up` puis le scénario MVP : traces et métriques visibles dans Grafana.

#### Fichiers concernés

- `monitoring/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`
