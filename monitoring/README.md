# Supervision locale — HYP-073

Stack de développement sans LLM : OpenTelemetry Collector contrib, Prometheus,
Grafana OSS et Tempo single-binary. Images officielles fixées par version et
digest, compatibles avec le Mac ARM64. Aucun service cloud requis.

## Démarrer et vérifier

Depuis la racine du dépôt, avec Docker démarré et l'environnement Python du
projet installé, y compris les extras `telemetry`, `sklearn` et le paquet
`packages/codegen` nécessaire au MVP :

```bash
docker compose -f monitoring/docker-compose.yml up -d
.venv/bin/python -m monitoring.verify --timeout 120
```

Le premier téléchargement nécessite Internet. Les exécutions du MVP utilisent
ensuite une transcription enregistrée, pas un modèle ni un appel LLM.

Le vérificateur attend la disponibilité réelle des services, puis lance deux
MVP séquentiels et deux MVP dans des processus simultanés. Il lit les traces et
métriques **via les sources provisionnées dans Grafana** :

- chaque trace doit contenir tous les identifiants de spans du rapport SDK ;
- chaque producteur doit avoir exactement les compteurs attendus ;
- chaque histogramme doit retrouver compte, somme et tous les buckets SDK,
  y compris les buckets vides et `+Inf` ;
- les processus du dernier couple doivent se chevaucher.

Un échec est explicite et ne crée pas de preuve de succès. Le bilan JSON
n'est écrit qu'après réussite dans
`demo/sortie/monitoring-verification/verification.json`. Les quatre rapports
MVP et leurs instantanés `sdk_metrics` restent dans les sous-dossiers `run-N`.
Un bilan plus ancien ne remplace jamais le statut de sortie de la commande
courante.

## Consulter Grafana

Ouvrir <http://127.0.0.1:3000>, puis **Explore** :

- source **Hypomnesis Prometheus** : `sum(hypomnesis_runs_total)` pour les
  compteurs des producteurs actuellement visibles ;
- `sum(hypomnesis_run_duration_seconds_count)` pour le nombre d'observations
  de durée, ou `hypomnesis_plugin_calls_total` pour les catégories d'appels ;
- source **Hypomnesis Tempo** : recherche par un `trace_id` du bilan JSON.

Les deux sources sont provisionnées automatiquement et non éditables.
Aucun tableau de bord P2 ni Loki n'est inclus.

| Service | Adresse locale |
|---|---|
| Grafana | <http://127.0.0.1:3000> |
| Réception OTLP HTTP | `http://127.0.0.1:4318/v1/traces` et `/v1/metrics` |
| Santé Collector | <http://127.0.0.1:13133/> |
| Prometheus | <http://127.0.0.1:9090> |
| Tempo | <http://127.0.0.1:3200/ready> |

Pour exporter une autre exécution :

```bash
HYPOMNESIS_OTLP_TRACES_ENDPOINT=http://127.0.0.1:4318/v1/traces \
HYPOMNESIS_OTLP_METRICS_ENDPOINT=http://127.0.0.1:4318/v1/metrics \
.venv/bin/python -m examples.mechanics.mvp --output demo/sortie/mvp-supervise
```

## Ports et ressources

Tous les ports publiés sont liés à `127.0.0.1`. En cas de conflit, définir
`HYP_GRAFANA_PORT`, `HYP_OTLP_PORT`, `HYP_COLLECTOR_HEALTH_PORT`,
`HYP_PROMETHEUS_PORT` ou `HYP_TEMPO_PORT` avant le démarrage. Adapter aussi
les options `--grafana`, `--otlp` et `--collector-health` du vérificateur ;
les URLs internes des sources Grafana ne changent pas.

Les limites cumulées des quatre conteneurs sont 1,5 Gio et trois CPU.
Elles s'ajoutent aux ressources de Docker et du programme Python. Prometheus
conserve au plus un jour ou 256 Mo d'historique ; Tempo conserve les traces
une heure. Les trois stockages utilisent des volumes Docker nommés.
Les rapports d'usage, contrôles de mises à jour et préinstallations
automatiques de plugins Grafana sont désactivés.

## Identité et rétention des métriques

Chaque fournisseur SDK privé possède une identité standard
`service.instance.id`, exposée par Prometheus comme `instance`. Elle distingue
les producteurs indépendants, y compris simultanés, sans modifier leurs
observations ou horodatages. Voir [ADR 0019](../docs/adr/0019-identite-producteurs-metriques.md).

Les compteurs et histogrammes restent cumulatifs par producteur. Les labels
applicatifs restent fermés ; l'identité technique augmente cependant la
cardinalité, et une CLI courte peut créer de nouvelles séries à chaque
lancement. Cette contrepartie est acceptée explicitement.

Le Collector expire les séries inactives après cinq minutes ; un redémarrage
vide son cache d'exposition. Prometheus conserve l'historique selon sa
rétention. Une somme instantanée peut donc baisser lorsque des producteurs
disparaissent : **ce n'est pas un compteur durable de tous les programmes
exécutés depuis l'installation**. Le vérificateur compare les mesures de
chaque nouveau producteur à son SDK, plutôt qu'une différence globale
potentiellement faussée par l'expiration de producteurs anciens.

## Arrêter et diagnostiquer

```bash
docker compose -f monitoring/docker-compose.yml ps
docker compose -f monitoring/docker-compose.yml logs --tail 50 collector
docker compose -f monitoring/docker-compose.yml stop
# Retirer les conteneurs et le réseau de ce projet, en conservant les volumes :
docker compose -f monitoring/docker-compose.yml down
```

Ne pas ajouter `--volumes` si les données doivent être conservées.
Les redémarrages automatiques sont activés tant que le projet n'est pas arrêté.
Tempo peut rester temporairement indisponible pendant l'initialisation du ring.

Cette configuration **n'est pas destinée à la production** : accès anonyme
Grafana en lecture, HTTP local sans TLS et sans contrôle d'accès entre
utilisateurs de la machine. Elle stocke les télémétries locales et ne remplace
pas une politique de sécurité, de sauvegarde ou de rétention de production.
