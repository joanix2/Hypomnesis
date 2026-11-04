---
title: "HYP-082 · Sorties LLM au grade `Hypothesis` et détection des manques"
lane: qa
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P1 · M · Phase 7 — Intégration LLM · dépend de HYP-081, HYP-032"
priority: P1
tags: [epistemique, llm, python]
---

## Conversation

### user

**Ticket** HYP-082 · **Priorité** P1 · **Taille** M · **Epic** Phase 7 — Intégration LLM · **Dépend de** HYP-081, HYP-032 · **Labels** python, llm

#### Contexte

§14.4 : les informations manquantes restent explicites ; le LLM ne doit pas inventer les valeurs. Propriété P12 (monotonie du support).

#### Tâches proposées

- Toute valeur littérale introduite par le LLM sans source a le support `Hypothesis`.
- Les valeurs absentes deviennent des métavariables à résoudre par les estimateurs.
- Rapport des informations manquantes à l'utilisateur.

#### Critères d'acceptation

- « Estime son épaisseur » produit une métavariable résolue par l'estimateur, et non une valeur inventée par le LLM.

#### Fichiers concernés

- `src/hypomnesis/llm/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`

### agent

Plan/todo/implémentation : ingestion typée générique dans Codegen, sans
logique de mécanique. Les valeurs concrètes du candidat sont des hypothèses ;
les options None deviennent des MetaVar typées persistantes, sans proposition
inventée. Une estimation de confiance doit être ajoutée et résolue par l'hôte.

Fermer aussi la frontière d'exécution : mode `generated=True` choisi par
l'hôte, jamais par M1. Dans ce mode, tous les Record du programme restent
Hypothesis, même s'ils revendiquent Given, Estimated ou Derived ; les vrais
Observe validés restent Observed. C'est volontairement conservateur, y compris
pour les Record d'un M2 appelé depuis le candidat : le moteur ne prouve pas
encore leur dérivation. Préserver le comportement des programmes écrits et
déclarés de confiance par l'hôte.

Brancher ce mode dans le banc Codegen, la CLI --demande, et proposer un
marquage explicite --generated pour les fichiers enregistrés. La vérification
statique seule ne confère aucun grade.

### user

### agent

Terminé, validation complète verte. `Codegen.hypotheses.capture_input`
valide la donnée fermée puis conserve les feuilles au support Hypothesis ;
None devient un MetaVar typé sans proposition ni valeur. Alias, records,
variants imbriqués, listes et tuples couverts. Le rapport expose chemins,
types et états. Une proposition d'estimateur de l'hôte reste séparée et
nécessite une résolution explicite.

Le moteur reçoit l'origine `generated` depuis l'hôte : Given/Estimated/
Assumed/Derived ne peuvent plus promouvoir les Record du candidat.
Observe reste Observed seulement après lecture/validation effective.
Branchement CLI --demande, --generated pour fichiers et banc Codegen.
Le mode de confiance historique est préservé ; un fichier seul ne peut
révéler son auteur. Les Record de M2 transitant dans le mode généré sont
eux aussi conservativement Hypothesis, faute de preuve de dérivation.

23 cas ciblés (ingestion et rétroaction) passent, puis tous les validateurs.
Cette itération ne prouve pas le raffinement Python ni une vérification
sémantique de la demande humaine ; aucun appel LLM réel.
QA, done réservé à la vérification humaine.

### user
