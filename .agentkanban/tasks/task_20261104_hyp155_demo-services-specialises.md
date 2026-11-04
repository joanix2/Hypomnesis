---
title: "HYP-155 · Démonstration multi-services : Z3, logique, contraintes et OCR"
lane: todo
created: 2026-11-04T23:09:06+01:00
updated: 2026-11-04T23:09:06+01:00
description: "P1 · L · Exécution multi-services · intégrations réelles et démonstration du cycle de vie"
priority: P1
tags: [dsl, moteur-symbolique, solveur, validation, exemples]
---

## Conversation

### user

**Ticket** HYP-155 · **Priorité** P1 · **Taille** L · **Epic** Exécution multi-services · **Dépend de** HYP-050, HYP-052, HYP-153, HYP-154 · **Labels** dsl, solveur, validation

« Un environnement qui va valider les contraintes avec Z3, un environnement
qui va être capable de faire du raisonnement à la Prolog, un environnement
qui va avoir un solver de contraintes, Solverspace, un environnement [...]
avec de l'OCR. »

#### Tâches proposées

- Construire un scénario reproductible reliant perception d'une donnée,
  raisonnement logique, résolution de contraintes et validation.
- Réutiliser le backend Z3 existant, distinguer sa validation d'un résultat
  du rôle d'un solveur géométrique/de contraintes.
- Préciser le fragment logique attendu (règles existantes ou véritable
  Prolog avec unification/recherche) avant de choisir son fournisseur.
- Confirmer le produit nommé « Solverspace » : possiblement SolveSpace,
  sans figer cette interprétation ni inventer un binding disponible.
- Choisir un fournisseur OCR optionnel et documenter installation,
  données locales de test et limites ; aucune dépendance lourde imposée au noyau.
- Montrer démarrage/arrêt selon les branches du pipeline et réutilisation
  d'un service partagé ; conserver les traces et résultats rejouables.

#### Critères d'acceptation

- Les quatre rôles sont démontrés avec des intégrations réelles choisies
  et documentées ; les doublures sont identifiées comme telles dans les tests.
- Les résultats OCR non étayés restent des hypothèses/estimations :
  extraction réussie ne signifie pas vérité de la donnée extraite.
- Une contrainte invalide, une panne de fournisseur et une branche évitée
  donnent les comportements attendus sans résultat de secours trompeur.
- La démo fonctionne sans LLM, n'envoie aucune donnée à un service tiers
  sans autorisation et ne met pas de logique métier dans le noyau M3.
- Documentation : commandes reproductibles, services requis, politique
  de cycle de vie, limites et traces d'une exécution.

### agent

Cibles conservées telles que demandées ; choix de produits et éventuels
accès réseau à arbitrer pendant la planification, pas pendant cette
création de tickets. Aucun fournisseur installé ni service lancé.

### user
