---
id: HYP-070
title: "Instrumentation OpenTelemetry (traces)"
status: backlog
priority: P1
size: M
epic: P6-OBSERVABILITE
depends_on: [HYP-044]
labels: [python, observabilité]
assignee: 
---

# HYP-070 — Instrumentation OpenTelemetry (traces)

## Contexte

§12.3 : un identifiant d'exécution et les spans `hypomnesis.run`, `language.parse`, `language.typecheck`, `observer.read`, … ; ADR 0005.

## Tâches

- [ ] `observability/tracing.py` ; spans aux étapes listées au §12.3, avec les attributs recommandés.
- [ ] Propagation du `trace_context` dans l'enveloppe de message.
- [ ] Désactivable sans changer aucun résultat.

## Critères d'acceptation

- [ ] Une exécution du scénario produit l'arbre de spans du §12.3.
- [ ] Résultats identiques avec ou sans télémétrie (test).

## Fichiers concernés

- `src/hypomnesis/observability/`

## Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `kanban/README.md`
