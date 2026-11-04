---
title: "HYP-090 · Scénario MVP principal : plaque de bout en bout"
lane: qa
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P0 · L · Phase 8 — Stabilisation · dépend de HYP-054, HYP-052, HYP-055, HYP-063, HYP-082"
priority: P0
tags: [dsl, estimateurs, exemple, moteur-symbolique, mvp, python, solveurs]
---

## Conversation

### user

**Ticket** HYP-090 · **Priorité** P0 · **Taille** L · **Epic** Phase 8 — Stabilisation · **Dépend de** HYP-054, HYP-052, HYP-055, HYP-063, HYP-082 · **Labels** python, exemple

#### Contexte

§16.2 : « Crée une plaque de 120 × 80 mm, estime son épaisseur, vérifie sa validité et exporte sa géométrie. » Dix étapes.

#### Tâches proposées

- Enchaîner transcription, compilation, normalisation des dimensions, estimation, résolution, validation, commande d'export, résultat JSON.
- Actionneur logiciel d'export de géométrie (fichier).
- Trace et métriques enregistrées.

#### Critères d'acceptation

- Test de bout en bout avec réponse LLM enregistrée.
- Chaque étape du §16.2 est identifiable dans la trace et la provenance.

#### Fichiers concernés

- `examples/mechanics/`
- `tests/e2e/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`

### agent

Plan/todo/implémentation : ajouter un hôte d'assemblage exécutable dans
`examples/mechanics/`, sans formule métier Python. M2 garde normalisation,
caractéristiques d'estimation, problème, validation et commande géométrique.
Réutiliser la réponse figée M1 existante, Codegen, MetaVar, modèle sklearn
versionné, Z3 typé/revérifié, LanguageValidator, dispatcher et FileTransport.

Le candidat fournit uniquement une donnée passée au codec de confiance.
Une session M2 distincte exécute les fonctions choisies par l'hôte : le M1
ne peut pas remplacer le validateur, le solveur ou la commande. Les assertions
issues de la transcription restent Hypothesis ; une commande autorisée et
un résultat logiciel observé ne prouvent pas une validité physique absolue.

Dix étapes effectives du §16.2, chacune tracée, avec liens vers les faits/
témoins ou les métriques (qui restent séparées du raisonnement, ADR 0005).
L'estimation continue et la solution standard peuvent diverger : conserver
les propositions et résoudre explicitement, pas effacer un conflit.
E2E sous `tests/optional` : exige Codegen et sklearn, absents du job core-only.
Tester aussi refus de permission, épaisseur inventée, mauvaise compilation,
normalisation et erreur d'estimateur avant tout export.

### user

### agent

Terminé, validation complète verte. Hôte exécutable :
`python -m examples.mechanics.mvp --output demo/sortie/mvp-mecanique`.
Réponse figée explicitement identifiée, compilation statique, données
matérialisées puis contrôlées par le codec M2 de confiance. La session du
candidat est distincte : même une redéfinition de Plaque dans M1 ne peut
remplacer le validateur de l'hôte.

Exécution réelle des dix étapes : normalisation M2 (mm/cm/m), MetaVar sans
valeur inventée, sklearn versionné (environ 3,214 mm), Z3 typé/rationnel
revérifié (standard 3 mm), certificat de validation rejouable puis commande,
transport JSONL et fichier 120 × 80 × 3 mm. Trace, métriques, provenance,
journal et résultat JSON round-trip identique persistés dans rapport_mvp.json.
L'export logiciel est observé ; la validité issue d'entrées non étayées
reste Hypothesis. Les propositions d'estimation et de résolution sont
conservées, divergence et choix explicite compris.

11 tests E2E et 61 ciblés passent : chemin heureux, cm, remplacement du
checker par M1, permission absente, panne d'écriture, chemin invalide,
typage, épaisseur inventée, unité inconnue, extrapolation et unsat.
Un refus ne produit aucun fichier géométrique ni faux succès ; le rapport
d'échec et la trace restent disponibles. Aucun appel LLM réseau, aucune
preuve mécanique ou couverture Lean totale revendiquée.
Guide : [scénario mécanique](../../docs/architecture/scenario-mecanique.md).

HYP-090 en QA ; done réservé à la vérification humaine. Tous les P0 du
tableau sont désormais en QA/done sauf HYP-027, encore partiel sur la
couverture totale du fragment formel (HYP-021/HYP-150).

### user
