---
id: HYP-073
title: "Stack Collector, Prometheus, Grafana, Tempo"
status: backlog
priority: P1
size: M
epic: P6-OBSERVABILITE
depends_on: [HYP-071]
labels: [infra, observabilité]
assignee: 
---

# HYP-073 — Stack Collector, Prometheus, Grafana, Tempo

## Contexte

§12.6 : stack de référence.

## Tâches

- [ ] `monitoring/docker-compose.yml` avec OpenTelemetry Collector, Prometheus, Grafana, Tempo (ou Jaeger).
- [ ] Provisionnement automatique des sources de données Grafana.
- [ ] Documentation de démarrage.

## Critères d'acceptation

- [ ] `docker compose up` puis le scénario MVP : traces et métriques visibles dans Grafana.

## Fichiers concernés

- `monitoring/`

## Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `kanban/README.md`
