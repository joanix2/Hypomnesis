---
title: "HYP-071 · Métriques du §12.4"
lane: qa
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P1 · M · Phase 6 — Observabilité · dépend de HYP-070"
priority: P1
tags: [observabilite, outillage, python]
---

## Conversation

### user

**Ticket** HYP-071 · **Priorité** P1 · **Taille** M · **Epic** Phase 6 — Observabilité · **Dépend de** HYP-070 · **Labels** python, observabilité

#### Contexte

Tableau des métriques du §12.4 ; labels sans identifiants à forte cardinalité.

#### Tâches proposées

- Compteurs et histogrammes listés ; export OTLP.
- Test qui refuse un label de métrique contenant un identifiant de message, de trace ou de connaissance.

#### Critères d'acceptation

- Toutes les métriques du §12.4 sont émises par le scénario MVP.

#### Fichiers concernés

- `src/hypomnesis/observability/metrics.py`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`

### agent

Plan / todo / implement du lot P1 approuvé, après HYP-070 validé et committé
(`bb3c109`). Utiliser un MeterProvider privé et un lecteur mémoire, puis
l'exporteur officiel OTLP HTTP local avec les mêmes restrictions réseau.
Observer les véritables spans terminés pour les durées/appels ; compter les
commandes finales une fois seulement, hors rejeu dédupliqué. Instrumenter le
résultat effectif des validateurs, pas seulement leurs exceptions.

Les dimensions sont une liste fermée de catégories : aucune valeur libre
de plugin, schéma, message, trace, connaissance ou exception dans un label.
Les jetons restent conditionnels : API disponible, aucune consommation
inventée et aucun appel LLM. Tests réels succès/rejet/panne, métriques SDK et
protobuf reçu localement, invariance des résultats, puis validation
complète/rapide/graphe et QA. Le scénario MVP enregistré n'est pas un
benchmark ni une exécution réelle de modèle.

### user

### agent

Implémentation et validation complète vertes : MeterProvider privé,
agrégations SDK mémoire, exporteur officiel OTLP HTTP local, histogrammes
en secondes, catégories fermées sans identifiants individuels. Export
périodique et final ; fermeture même si la construction du traceur échoue.

Les appels sont observés aux véritables fins de spans ; les commandes
comptées une fois à l'état final, sans doublon au rejeu. Les refus du
validateur sont distingués des erreurs logicielles de son checker.
Les 30 tests dédiés couvrent aussi protobuf reçu, refus/redirection,
isolement/désactivation et valeurs/labels invalides. Trois tests MVP réels
supplémentaires couvrent succès, refus de permission et échec d'écriture.
Aucun compteur de rejet/échec ni token n'est inventé dans le succès.
Les jetons restent conditionnels et aucun modèle n'a été exécuté.

Passage en QA après validation complète ; revue humaine pour `done`.
Graphe et validation rapide avant commit local ; aucun push.

### user
