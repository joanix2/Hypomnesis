---
title: "HYP-152 · Bindings typés vers des services spécialisés"
lane: todo
created: 2026-11-04T23:09:06+01:00
updated: 2026-11-04T23:09:06+01:00
description: "P1 · L · Exécution multi-services · contrats de capacités et bindings hôte"
priority: P1
tags: [metalangage, moteur-symbolique, contrats, effets]
---

## Conversation

### user

**Ticket** HYP-152 · **Priorité** P1 · **Taille** L · **Epic** Exécution multi-services · **Dépend de** HYP-060, HYP-062, HYP-063, HYP-147 · **Labels** metalangage, contrats

« Mon langage doit pouvoir avoir des bindings avec différents services.
Il s'exécute dynamiquement entre différents services, un peu comme des
aires du cerveau ou des fonctions cognitives. »

#### Objectif

Un programme symbolique décrit des opérations typées et peut les déléguer
à des environnements spécialisés : validation Z3, raisonnement de type
Prolog, solveur géométrique/de contraintes et perception OCR, entre autres.
La métaphore cognitive ne prescrit pas une architecture neuronale ou LLM.

#### Tâches proposées

- Définir les capacités exposées par un service : identité/version, contrats
  d'entrée/sortie, erreurs et disponibilité ; séparer capacité et instance.
- Réutiliser les décorateurs Python et le registre d'adaptateurs existants
  pour les bindings hôte, sans FFI arbitraire depuis un fichier .hyp.
- Distinguer imports de bibliothèques symboliques et bindings d'exécution ;
  les imports ne doivent pas accorder de permissions ni lancer un service.
- Prévoir des fournisseurs locaux ou distants sans imposer HTTP, conteneurs
  ou un fournisseur particulier ; l'hôte configure adresses et autorisations.
- Documenter l'articulation avec Effect IR, transport, solveurs et règles
  existants, plutôt que créer une seconde pile parallèle.

#### Critères d'acceptation

- Un même programme s'exécute avec deux implémentations compatibles d'une
  capacité sans changement de sa logique métier.
- Binding absent, contrat incompatible et service indisponible donnent des
  erreurs distinctes ; aucune réponse de succès fictive.
- Validation et permissions précèdent chaque appel ; check/LSP restent
  statiques, sans import d'adaptateur ni démarrage de service.
- Contrats et tests couvrent les échanges, pas seulement la découverte.

### agent

Demande enregistrée en todo ; aucune implémentation lancée. Les choix
de syntaxe et de transport restent à instruire, sans nouvelle DSL imposée.

### user
