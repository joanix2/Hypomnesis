# ADR 0005 — Provenance épistémique et observabilité restent distinctes

- **Statut :** acceptée
- **Date :** 2026-11-03

## Contexte

Le §12.8 distingue la provenance (pourquoi une conclusion est tenue) de l'observabilité
(comment une opération s'est déroulée).

## Décision

- La provenance est une donnée du domaine : elle vivra dans le moteur épistémique (phase 2)
  sous forme de structures immuables et d'un journal d'événements, persistés en SQLite.
- L'observabilité utilise OpenTelemetry (traces, métriques, logs) et n'est jamais lue par le
  moteur de raisonnement.
- Le seul lien entre les deux est un identifiant de corrélation : une connaissance, une
  hypothèse ou une commande peut référencer le `trace_id` de l'exécution qui l'a produite, et
  l'enveloppe de message transporte le `trace_context`.

## Conséquences

- Désactiver ou échantillonner la télémétrie ne change aucune conclusion du système.
- Les labels de métriques n'incluent pas d'identifiants à forte cardinalité (§12.4).
