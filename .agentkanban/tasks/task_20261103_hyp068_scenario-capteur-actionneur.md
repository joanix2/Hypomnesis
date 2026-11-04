---
title: "HYP-068 · Scénario MVP secondaire : température → ventilateur"
lane: qa
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P0 · M · Phase 5 — Effets et actionneurs · dépend de HYP-063, HYP-050"
priority: P0
tags: [dsl, effets, exemple, moteur-symbolique, mvp, python]
---

## Conversation

### user

**Ticket** HYP-068 · **Priorité** P0 · **Taille** M · **Epic** Phase 5 — Effets et actionneurs · **Dépend de** HYP-063, HYP-050 · **Labels** python, exemple

#### Contexte

§16.3 : un capteur simulé donne une température, une règle produit une commande de ventilateur, un second capteur confirme ou réfute l'effet.

#### Tâches proposées

- Programme d'exemple ; règle métier ; boucle de rétroaction bornée (§11.9).
- Cas d'échec : l'effet attendu n'est pas observé, l'hypothèse est réfutée et révisée.

#### Critères d'acceptation

- Test d'intégration couvrant succès et réfutation.
- La frontière noyau pur / effets est visible dans la trace.

#### Fichiers concernés

- `examples/robotics/`
- `tests/integration/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`

### agent

Plan HYP-068 : compléter le scénario existant plutôt que dupliquer son
orchestrateur. Règle et boucle restent en Hypomnesis ; ajouter un capteur de
confirmation distinct avec API compatible pour les programmes existants.
Tracer séparément reprise pure de continuation, lectures et dispatch effectif.

Corriger les cas limites liés : pas de réfutation si la commande n'a pas
été exécutée (dry-run, simulation, rejet ou résultat indéterminé) ; seuil
atteint à la dernière action reconnu avant épuisement du budget ; budget
négatif et température absente refusés explicitement. Les tests couvriront
succès, réfutation, limites et provenance, avec exemple exécutable et
transcript de transport. Les observations restent celles d'un environnement
simulé, pas une preuve de sûreté du matériel.

### user

### agent

HYP-068 terminé, proposé en QA. Le programme M1 lit thermo-1 puis confirme
avec thermo-2, via reguler_avec_confirmation ; reguler reste compatible.
La règle métier et la boucle bornée restent entièrement en Hypomnesis.
Une baisse effectivement observée est distinguée d'un effet attendu
Hypothesis ; une réfutation retire la source et invalide ses dépendants.

Dry-run, simulation, rejet, Failed et UnknownOutcome n'engendrent plus de
fausse réfutation physique. Le seuil atteint à la dernière action est
reconnu, le budget zéro n'agit pas et le budget négatif est une erreur.
La lecture M2 ne transforme plus une température absente en zéro.

Trace : procedure.resume marque la construction pure du prochain effet ;
observer.read, command.dispatch et actuator.execute délimitent les I/O.
Les capteurs restent simulés, sans prétention de causalité ou de sûreté réelle.
L'adaptateur de règle HYP-050 exécute la même fonction M2 sans copie Python.

Vérifications : 13 nouveaux cas d'intégration, 84 tests ciblés verts,
exemple examples/robotics/feedback.py exécuté avec succès et panne,
transcripts à six messages, provenance et invalidations exactes.
Validation complète verte. Catalogue Codegen ajusté pour la nouvelle API
publique ; ce changement de catalogue rend les anciens bancs LLM non
strictement comparables sans réexécution. Guide rétroaction et TECHNICAL
à jour. Aucun sous-agent, passage en done laissé à l'utilisateur.

### user
