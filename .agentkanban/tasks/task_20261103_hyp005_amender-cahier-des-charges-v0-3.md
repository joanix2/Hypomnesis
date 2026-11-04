---
title: "HYP-005 · Amender le cahier des charges en v0.3"
lane: qa
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-04T19:18:01+01:00
description: "P1 · S · Fondations et gouvernance · décisions adoptées, ADR 0006 maintenue proposée"
priority: P1
tags: [architecture, documentation, humain, mvp]
---

## Conversation

### user

**Ticket** HYP-005 · **Priorité** P1 · **Taille** S · **Epic** Fondations et gouvernance · **Dépend de** HYP-003 · **Labels** humain, doc

> **Décision humaine requise** : ce ticket ne doit pas être réalisé par un agent seul.

#### Contexte

Deux propositions attendent une décision : l'objectif OBJ-11 « Vérification formelle » et ses critères d'acceptation (§4 de `docs/verification/proprietes.md`), et la décomposition des statuts épistémiques du §7.1 en trois axes (existence, support, cohérence ; §4.3 de `docs/architecture/m3-metalangage.md`).

#### Tâches proposées

- Décider de l'adoption de chaque proposition.
- Créer `docs/specification/cahier-des-charges-v0.3.md` à partir de `docs/specification/cahier-des-charges-v0.2.md`, avec un journal des changements en tête.
- Passer l'ADR 0006 à « acceptée » ou « rejetée ».

#### Critères d'acceptation

- La v0.3 existe ; la v0.2 est conservée telle quelle.
- Les tickets du lot P2-EPISTEMIQUE sont cohérents avec la décision sur les statuts.

#### Fichiers concernés

- `docs/specification/`
- `docs/adr/0006-m3-theorie-des-types-a-deux-niveaux.md`

#### Références

- `docs/verification/proprietes.md`
- `docs/architecture/m3-metalangage.md`
- Conventions et définition de fini : `.agentkanban/memory.md`

### user

« n'utilise pas les sous agents et continue l'implémentation »

### agent

Travail direct sur HYP-005, sans sous-agent. Les trois arbitrages ont été présentés :
OBJ-11 et ses cinq critères, trois axes épistémiques, statut de l'ADR 0006.
L'utilisateur étant indisponible pour répondre, aucune adoption humaine n'est
inventée. Choix prudent : préparer une v0.3 **brouillon**, sans remplacer la
référence v0.2 ni accepter/rejeter l'ADR à sa place.

Plan et checklist : copier intégralement la v0.2 sans modifier l'original,
ajouter un journal des amendements, OBJ-11, les axes proposés et les critères
formels ; distinguer cibles, fonctionnalités réelles et preuves effectivement
établies. L'architecture méta reste une cible proposée, pas un noyau implémenté.
La fermeture du ticket reste conditionnée à la décision humaine.

#### Cohérence du lot P2-EPISTEMIQUE

| Tickets | Effet de la proposition, sans adoption anticipée |
|---|---|
| HYP-030 | Prévoit déjà les trois axes conditionnellement à HYP-005 ; conserver cette réserve |
| HYP-031 | Le support reste une lecture de la provenance ; `Derived` n'ajoute pas un grade |
| HYP-032 | `Unknown` est une métavariable non résolue ; une proposition conserve son propre support |
| HYP-033 | Les événements `Observed`/`Derived` du journal sont des actions historiques, pas des statuts exclusifs |
| HYP-034 | Une future migration doit préserver axes, provenance et historique, sans changer le format actuel par ce seul brouillon |
| HYP-035 | `Conflict` relève de la cohérence, indépendamment du support des faits en cause |
| HYP-036, HYP-037 | Les preuves restent des obligations distinctes ; le brouillon ne les déclare pas réalisées |
| HYP-038 | Le support des dérivations est calculé depuis les prémisses, pas promu automatiquement |

Les tickets existants sont compatibles avec la proposition ; aucun critère
historique ni dépendance n'est réécrit avant arbitrage. La v0.3 indique
explicitement ce qui reste à prouver, dont HYP-021/022/023/027/028/065.

### user

Créer une colonne hypothèse et y ajouter la proposition partagée sur les
solveurs génériques et la recherche constructive.

### agent

Demande enregistrée séparément sous HYP-149 dans le nouveau couloir `hypothese`.
Le texte original est conservé avec ses exemples d'interfaces et les réserves
sur SMT, génération de candidats, typage et conformité à l'intention.
La proposition reste non adoptée et ne tranche pas les décisions de HYP-005.

Contrôle du brouillon HYP-005 : v0.2 identique à HEAD, 22 chapitres conservés
en v0.3, liens relatifs valides et cinq critères OBJ-11 présents.
La validation complète du dépôt est verte (785 tests et contrôles Python/Lean).
La tâche demeure en `doing`, non déclarée terminée : les arbitrages humains
et l'adoption finale restent ouverts.

### user

continue

### agent

Relecture du ticket et de sa checklist. Le brouillon et les contrôles sont
déjà terminés ; seules les décisions humaines restent à prendre.
Les trois choix ont été soumis de nouveau, mais aucune réponse de l'utilisateur
n'est disponible. La consigne automatique de choisir une option pragmatique
n'est pas enregistrée comme une adoption humaine.

HYP-005 reste donc en attente d'arbitrage : OBJ-11, trois axes épistémiques,
acceptation ou rejet de l'ADR 0006. Aucun changement de statut de l'ADR,
aucune promotion de la v0.3 en référence et aucun passage en `qa`.
Pas de sous-agent ni de modification du moteur dans cette reprise.

### user

fait moi prendre les décision alors

### agent

Présentation des décisions avec conséquences et recommandations :

1. **Adopter OBJ-11 et ses cinq critères** : exigences de vérification Lean
   pour le noyau, sans affirmer que leur couverture est déjà complète.
2. **Adopter les trois axes épistémiques** : existence, support et cohérence
   indépendants ; une information estimée peut aussi être contradictoire.
   `Derived` désigne la justification, pas une fiabilité supplémentaire.
3. **Garder l'ADR 0006 proposée et expérimenter**, recommandation prudente :
   ne pas engager tout le calcul méta dépendant/modal/graduel pour avancer sur
   le moteur. Alternative : accepter explicitement toute l'ADR comme cible.

Le formulaire ne renvoie encore qu'une indication automatique d'indisponibilité,
pas les choix de l'utilisateur. Aucune décision adoptée. Une réponse explicite
dans la conversation permettra de consigner les arbitrages sans dépendre du formulaire.

### user

je suis d'accord vas y

### agent

Accord explicite sur les recommandations présentées : **adopter OBJ-11 et
ses cinq critères**, **adopter les trois axes épistémiques**, **garder l'ADR
0006 proposée pour expérimentation**.

Ce dernier choix remplace, par décision humaine, l'alternative initiale
« acceptée ou rejetée » du ticket. Il ne reste donc pas un arbitrage bloquant :
l'architecture complète n'est ni adoptée ni rejetée, son expérimentation est
autorisée. L'index ADR et la note M3 précisent l'adoption partielle des axes.

La v0.3 devient référence ; la v0.2 reste inchangée. Les pointeurs courants,
le catalogue de propriétés et les tickets HYP-030 à HYP-038 sont alignés
par ajouts sans réécriture de leurs échanges historiques.
Les critères formels restent des obligations cibles et non de nouvelles
garanties prouvées. Aucun code moteur ou preuve Lean n'est modifié.

Validation finale : v0.2 identique à sa version avant les amendements ;
22 chapitres et cinq critères formels conservés ; liens relatifs vérifiés ;
neuf tickets épistémiques alignés. Validation complète verte : 785 tests
(708 cœur, 77 Codegen), linters, Pyright, schémas, build Lean, audit et
vérificateur de certificats. Le validateur a aussi ajouté la fin de ligne
manquante au ticket HYP-149, sans modifier sa proposition.
HYP-005 et sa checklist passent en `qa`, pas en `done`.

### user
