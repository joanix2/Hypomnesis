---
title: "HYP-073 · Stack Collector, Prometheus, Grafana, Tempo"
lane: qa
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P1 · M · Phase 6 — Observabilité · dépend de HYP-071"
priority: P1
tags: [infra, observabilite, outillage]
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

### agent

Plan / todo / implement du lot P1 approuvé. HYP-071 est QA et committé
(`5fdd847`), HYP-072 aussi (`7bbcee0`). Docker Desktop démarré avec
autorisation ; quatre images officielles ARM64 téléchargées et digests
vérifiés, versions lues depuis les releases officielles : Collector
0.164.0, Prometheus 3.15.1, Grafana OSS 13.3.0, Tempo 2.10.10 (branche
maintenue 2.x pour stockage local/single-binary sans Kafka).

Créer la stack Compose locale avec ressources limitées, ports loopback,
sources Grafana provisionnées et stockage persistant. Désactiver les
rapports d'usage/contrôles de mises à jour des composants. Pas de LLM,
de cloud, de Loki ou de dashboards P2.

Vérificateur reproductible : readiness réelle, deux exécutions du MVP
enregistré via les endpoints OTLP, lecture de chaque trace et des compteurs
par le proxy des sources Grafana. Exiger une hausse réelle du nombre
d'exécutions, pas seulement la présence du nom d'une métrique. Aucun
passage QA sur la seule validité YAML.

### user

### agent

Point de validation : les quatre services locaux fonctionnent, avec versions
et digests fixés, ports loopback et limites de ressources. La vérification
par les sources Grafana a retrouvé deux traces complètes de 35 spans et
une progression réelle du compteur de 0 à 2 pour deux MVP séquentiels.
Les 31 tests unitaires des métriques passent.

Le test supplémentaire de deux MVP concurrents révèle cependant un défaut :
les deux programmes et leurs traces aboutissent, mais le compteur passe
seulement de 2 à 3, au lieu de 4. Le passage OTLP en DELTA corrige le cas
séquentiel, pas ce cas concurrent. HYP-073 reste en cours, non validé
globalement et non committé.

Cause vérifiée dans l'implémentation officielle du Collector 0.164.0 :
`delta_to_cumulative` suppose un producteur par série. Il rejette un point
dont le début précède celui de la série déjà retenue, ou dont la fin
n'est pas postérieure au dernier point traité. Nos fournisseurs SDK
indépendants utilisent actuellement la même identité de ressource ; leurs
points peuvent donc se concurrencer. Ce n'est pas simplement un délai
de scrape ou un problème d'affichage.

Source :
[agrégation delta officielle](https://github.com/open-telemetry/opentelemetry-collector-contrib/blob/v0.164.0/processor/deltatocumulativeprocessor/internal/delta/delta.go).
Le connecteur `signaltometrics` ne fournit pas une solution générale de
remplacement : il agrège par requête entrante, sans agrégation temporelle
avec état. Reconstituer les histogrammes à partir de moyennes perdrait
leurs distributions ; cette piste n'est pas retenue.

Arbitrage à demander avant de modifier le modèle :

1. Accepter l'identité standard OpenTelemetry de chaque producteur
   indépendant, puis regrouper les résultats dans Grafana. C'est l'approche
   standard pour plusieurs producteurs. Elle ajoute des séries techniques ;
   avec les CLI courtes, leur nombre peut suivre le nombre de lancements.
   Ne pas présenter cette identité comme un label de cardinalité bornée,
   ni simplement rebaptiser un identifiant de run.
2. Conserver l'objectif strict d'absence de séries par producteur : revoir
   l'architecture autour d'une agrégation durable partagée, y compris entre
   processus CLI. Un singleton Python ne suffit pas entre processus.
   Cette option demande une évolution de l'architecture approuvée.
3. Différer cet arbitrage et poursuivre les P1 indépendants du moteur
   symbolique et des services ; garder HYP-073 explicitement ouvert.

Aucun compteur artificiel, changement des horodatages ou identifiant de
run déguisé n'a été ajouté pour faire passer le test. Aucune clôture
globale des P1 n'est annoncée.

### user

standard-producer-identity

### agent

Décision appliquée et consignée dans l'ADR 0019 : identité UUID distincte
par fournisseur SDK, stable pendant sa vie, indépendante de run/trace ;
labels applicatifs toujours fermés. Coût explicite accepté : une CLI
courte peut créer de nouvelles séries à chaque lancement. Pas de nouvelle
infrastructure ni de fournisseur SDK global.

Retour aux métriques SDK cumulatives ; suppression du convertisseur DELTA.
Prometheus conserve l'identité standard du producteur (`honor_labels`).
Le vérificateur compare séparément chaque producteur à l'instantané
SDK persisté dans le rapport MVP, afin que l'expiration d'anciens producteurs
ne fausse pas un test fondé uniquement sur une différence globale.

Première vérification réelle corrigée : quatre MVP, dont deux processus
simultanés, quatre traces complètes de 35 spans. Compteur visible 0 → 4,
et égalité de 128 échantillons par producteur avec le SDK : compteurs,
comptes/sommes et tous les buckets d'histogrammes, sans approximation.
Les 69 tests ciblés passent avant les deux cas additionnels de rejet
des identités techniques dans les labels applicatifs.

Documentation de démarrage/arrêt, limites de stockage, cardinalité et
frontière développement/production ajoutée. Validation complète et
graphe encore à exécuter ; pas encore de passage QA.

### user

### agent

Validation complète verte : tous les linters et types, tests moteur et
Codegen, audit Lean des axiomes et vérificateur de certificats. Le
différentiel inclut 500 exemples générés sans échec. Graphe AST/relations
Kanban reconstruit.

La vérification réelle a été relancée avec la configuration finale :
quatre MVP réussis, deux processus concurrents, quatre traces complètes
de 35 spans et 512 échantillons de métriques contrôlés au total
(128 par producteur). Compteur visible 0 → 4, aucun comptage perdu.
Contrôle via les API des sources Grafana ; pas de contrôle visuel du
navigateur revendiqué.

HYP-073 passe en QA, pas en done. Le guide de démarrage et le vérificateur
sont versionnés dans monitoring ; la stack Docker locale reste disponible
sur http://127.0.0.1:3000. Commit local après le contrôle rapide, sans push.
Ce jalon termine HYP-070–073, pas l'ensemble du lot P1.

### user
