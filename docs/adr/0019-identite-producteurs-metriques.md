# ADR 0019 — Identité des producteurs de métriques

- Statut : acceptée par l'utilisateur (HYP-073, choix `standard-producer-identity`).

## Contexte

Chaque `Tracer` possède son propre `MeterProvider` OpenTelemetry, fermé
explicitement avec lui. Plusieurs fournisseurs peuvent fonctionner en parallèle
dans un processus ou dans des processus CLI distincts.

Une série cumulative ne peut pas avoir plusieurs producteurs indépendants
indistinguables : les compteurs se remplacent au lieu de s'additionner.
Le passage en DELTA ne résout pas ce problème général : le convertisseur
`delta_to_cumulative` du Collector rejette certains points plus anciens ou
désordonnés. Deux MVP concurrents ont reproduit une perte de comptage.

## Décision

Conserver les fournisseurs privés et les exports SDK cumulatifs. Chaque
fournisseur reçoit une ressource `service.instance.id` UUID aléatoire,
stable pendant sa vie et indépendante des identifiants de run, de trace,
de message et de connaissance. `service.name` reste `hypomnesis`.
Ni nom de machine ni PID n'est utilisé.

Le Collector et Prometheus conservent cette identité standard sous le label
technique `instance`. `honor_labels: true` empêche le scrape de la remplacer
par l'adresse du Collector. Les requêtes Grafana peuvent ensuite agréger
les producteurs, par exemple `sum(hypomnesis_runs_total)`.

Les labels applicatifs restent limités aux énumérations fermées
`status`, `kind`, `mode`, `state`, `direction`. L'identité de ressource est
une exception technique explicite, pas une dimension de cardinalité bornée.
Aucun horodatage ni aucune observation n'est réécrit.

## Conséquences et limites

- Des producteurs simultanés ne s'écrasent plus ; les histogrammes conservent
  leurs comptes, sommes et buckets SDK.
- Les labels techniques augmentent la cardinalité. Avec une CLI courte,
  le nombre de séries peut suivre le nombre de lancements. Ce coût est
  accepté, et non caché sous un autre nom.
- La stack est une référence locale : expiration des séries inactives du
  Collector après cinq minutes, historique Prometheus limité à un jour et
  256 Mo, ressources des conteneurs limitées. Ces limites de rétention ne
  constituent pas une garantie de cardinalité constante.
- La somme instantanée des producteurs visibles n'est pas un registre
  durable du nombre total d'exécutions depuis l'installation. Redémarrages,
  expiration et rétention s'appliquent ; les séries historiques restent
  consultables selon cette rétention.
- Le vérificateur utilise les identités des nouveaux producteurs pour
  contrôler exactement leurs mesures, sans dépendre de l'expiration
  éventuelle d'anciennes séries.
- Une future agrégation durable partagée entre processus serait une autre
  architecture, à arbitrer séparément. Aucun service supplémentaire n'est
  introduit ici.
