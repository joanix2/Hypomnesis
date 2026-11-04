---
title: "HYP-154 · Activation et arrêt des services selon le pipeline"
lane: todo
created: 2026-11-04T23:09:06+01:00
updated: 2026-11-04T23:09:06+01:00
description: "P1 · L · Exécution multi-services · acquisition, disponibilité et libération à la demande"
priority: P1
tags: [moteur-symbolique, effets, outillage]
---

## Conversation

### user

**Ticket** HYP-154 · **Priorité** P1 · **Taille** L · **Epic** Exécution multi-services · **Dépend de** HYP-152 · **Labels** effets, outillage

« Les services peuvent s'éteindre ou s'allumer en fonction de la pipeline
qui est exécutée. »

#### Tâches proposées

- Définir un cycle de vie explicite : arrêté, démarrage, prêt, échec,
  arrêt ; distinguer service externe déjà disponible et service géré par l'hôte.
- Acquérir le service au moment où une étape en a réellement besoin,
  attendre sa disponibilité avec délai borné, puis libérer son utilisation.
- Gérer les usages partagés : ne pas arrêter un service encore nécessaire
  à une autre étape/exécution ; définir qui possède le droit de l'arrêter.
- Rendre la politique de maintien à chaud/arrêt configurable par l'hôte,
  avec choix documentés avant implémentation ; pas de délai arbitraire caché.
- Nettoyer après succès, erreur et annulation ; contrôler explicitement
  les autorisations de démarrer/arrêter un processus ou service.

#### Critères d'acceptation

- Un service géré est démarré à la demande, vérifié prêt avant appel et
  arrêté selon la politique lorsque plus personne ne l'utilise.
- Un service inutile au chemin exécuté n'est jamais démarré.
- Les tests couvrent démarrage concurrent/partagé, panne au démarrage,
  timeout, arrêt en échec et annulation sans processus orphelin.
- Aucun arrêt d'un service externe ou partagé sans propriété/autorisation
  explicite ; les transitions sont observables dans les traces.

### agent

Demande adoptée comme besoin produit, pas rangée parmi les hypothèses.
Le mécanisme concret de déploiement reste ouvert : processus local,
service distant ou autre fournisseur de cycle de vie.

### user
