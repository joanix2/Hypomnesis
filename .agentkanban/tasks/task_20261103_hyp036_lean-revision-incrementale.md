---
title: "HYP-036 · Lean F4a : révision incrémentale = recalcul complet"
lane: qa
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P1 · L · Vérification formelle (Lean) · dépend de HYP-033, HYP-003"
priority: P1
tags: [epistemique, lean, moteur-symbolique]
---

## Conversation

### user

**Ticket** HYP-036 · **Priorité** P1 · **Taille** L · **Epic** Vérification formelle (Lean) · **Dépend de** HYP-033, HYP-003 · **Labels** lean

#### Contexte

Prouver sur un modèle du moteur que l'algorithme de HYP-033 est exact, et que le journal n'est jamais détruit.

#### Tâches proposées

- Modéliser l'état (faits, provenances, index inverse) et l'opération de révision incrémentale.
- Prouver : `revise_incr s x = recompute (retract s x)`.
- Prouver : le journal après révision étend le journal précédent (préfixe).

#### Critères d'acceptation

- Théorèmes sans `sorry`, ajoutés à l'audit et à `proprietes.md` (lot F4).

#### Fichiers concernés

- `formal/Hypomnesis/Epistemics/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`

### agent

HYP-005 adopte OBJ-11 et les axes épistémiques en spécification v0.3.
Le modèle de révision devra respecter cette séparation et le journal en ajout
seul. La correction incrémentale reste une obligation de ce ticket, non une
preuve acquise par l'adoption de la spécification.

### user

### agent

Plan / todo / implement du lot Mac approuvé, sans sous-agent. Modèle fidèle
de l'index inverse, des candidats, de l'évaluation booléenne, de la projection
révisée et des instantanés ajoutés au journal. Les valeurs et métadonnées des
faits conservés seront des paramètres opaques inchangés, pas un domaine jouet.
Les rétractions d'axiome seront refusées comme dans l'API.

Le générateur historique ne couvre ni zéro ni un. Avant de prouver
l'équivalence, vérifier ce fragment aussi : une provenance zéro peut être
publiée mais n'a aucune observation dans l'index. Ne pas contourner le cas
par une hypothèse artificielle sur les données. Toute correction touchera
aussi le rejeu SQLite et sera testée contre la vraie version Lean.

### user

### agent

Implémentation et preuve terminées. Le contre-exemple ZERO a d'abord été
reproduit par un test rouge, puis corrigé sans exclure ces termes du modèle.
Les termes contenant zéro sont des candidats conservatifs ; seule une
évaluation booléenne fausse entraîne l'invalidation. Les faits non concernés
sans zéro ne sont pas évalués. Le rejeu suit cette règle et les événements
ne citent plus à tort la dernière source comme cause unique.

Quatre théorèmes audités, sans sorry ni axiome maison : complétude des
candidats, égalité des invalidations, égalité des états révisés et préfixe du
journal. P29–P30 ajoutés au catalogue. Valeurs et contexte génériques,
ordre des faits, inconnues, instantanés et refus d'axiome représentés.
Les dictionnaires réels sont projetés en listes à clés uniques.

160 cas réels Python/Lean passants, dont 40 refus d'axiome ; comparaison
de chaque champ de l'état et du journal. Propriété générée sur toute
l'algèbre ZERO/ONE/obs/plus/times et régression de localité ajoutées.
La correspondance est obligatoire en CI des preuves et validation Lean.
Validation complète verte, avec types/schémas, suites cœur/Codegen, audit,
88 tests Lean obligatoires et toujours 500 termes différentiels.
Ce n'est pas une preuve du code Python ni de durabilité SQLite ; aucune
règle métier n'est recalculée implicitement. QA proposée, done humain.
Aucun sous-agent, LLM ou push.

### user

### agent

Validation rapide finale et graphe verts. Checklist terminée, commit local
de la preuve et du correctif associé ; aucun push.

### user
