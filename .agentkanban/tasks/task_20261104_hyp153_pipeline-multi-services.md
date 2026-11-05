---
title: "HYP-153 · Exécution dynamique de pipelines entre services"
lane: todo
created: 2026-11-04T23:09:06+01:00
updated: 2026-11-04T23:09:06+01:00
description: "P1 · L · Exécution multi-services · orchestration des appels et continuité symbolique"
priority: P1
tags: [moteur-symbolique, metalangage, effets, epistemique]
---

## Conversation

### user

### agent

HYP-153 reste en `todo` comme ticket de suivi. Ses critères (pipeline réelle,
branche non exécutée, continuité symbolique, erreurs/annulation et traces)
sont répartis sans imposer d'ordonnanceur distribué :

- HYP-168 : exécution des étapes liées aux capacités et branchement paresseux,
  après les bindings HYP-166/HYP-167.
- HYP-169 : conservation des valeurs typées, faits, provenance, hypothèses et
  résultats de validation, après HYP-168.
- HYP-170 : budgets, délais, annulation, propagation/relance et traces,
  après HYP-168 et HYP-169.

La checklist parent agrège les critères d'acceptation et les validations ;
aucune dépendance existante ni lane n'est modifiée.

### user

**Ticket** HYP-153 · **Priorité** P1 · **Taille** L · **Epic** Exécution multi-services · **Dépend de** HYP-152 · **Labels** moteur-symbolique, effets

« On peut exécuter le programme entre ces différents services [...]
en fonction de la pipeline qui est exécutée. »

#### Objectif

Le programme conserve son sens et son état symbolique lorsque ses étapes
sont exécutées par différents environnements. Il ne s'agit pas de faire
migrer arbitrairement l'interpréteur ou de recopier du code chez un tiers :
les frontières d'appel, données et résultats doivent être explicites.

#### Tâches proposées

- Articuler la procédure existante avec des étapes liées aux capacités :
  enchaînement, branchements et dépendances de données réellement exécutées.
- Résoudre les bindings selon la configuration et les capacités disponibles ;
  refuser les choix ambigus, sans substitution silencieuse de solveur.
- Préserver les valeurs typées, identités de faits, provenance, hypothèses
  et résultats de validation à chaque frontière.
- Fixer budgets, délais, annulation et propagation des erreurs ; une relance
  ne doit pas dupliquer une action non idempotente.
- Tracer étape, service, demande, résultat et cause d'échec. Ne pas
  introduire un ordonnanceur distribué général sans besoin démontré.

#### Critères d'acceptation

- Une procédure réelle traverse plusieurs fournisseurs, puis réutilise
  leurs résultats dans un calcul symbolique et un branchement.
- Un branchement non exécuté ne déclenche aucun appel à son service.
- Panne, timeout, résultat invalide et annulation sont testés ; pas
  d'autopromotion d'une estimation ou d'une hypothèse en observation.
- La logique métier reste dans les programmes/DSL ; les bindings Python
  ne contiennent que l'intégration et les contrôles génériques.

### agent

Ticket lié aux bindings HYP-152 et au cycle de vie HYP-154. La parallélisation
des étapes indépendantes est à évaluer, pas assimilée à la demande actuelle
ni imposée comme prérequis d'une première exécution multi-services.

### user
