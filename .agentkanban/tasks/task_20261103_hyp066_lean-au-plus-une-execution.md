---
title: "HYP-066 · Lean F5b : au plus une exécution des commandes non idempotentes"
lane: qa
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P0 · L · Vérification formelle (Lean) · dépend de HYP-061"
priority: P0
tags: [effets, lean, moteur-symbolique]
---

## Conversation

### user

**Ticket** HYP-066 · **Priorité** P0 · **Taille** L · **Epic** Vérification formelle (Lean) · **Dépend de** HYP-061 · **Labels** lean

#### Contexte

§9.7 et risque « Doubles commandes » (§19).

#### Tâches proposées

- Modéliser automate, journal, relances, pertes et duplications de messages.
- Prouver : une commande non idempotente est exécutée au plus une fois, quelles que soient les pannes modélisées.
- Prouver : les états terminaux sont absorbants.

#### Critères d'acceptation

- Théorèmes sans `sorry`, ajoutés à l'audit.

#### Fichiers concernés

- `formal/Hypomnesis/Effects/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`

### agent

Plan : réutiliser l'automate HYP-065 et le raffiner par le garde de relance
Python (idempotence, état Dispatched et budget). Ajouter explicitement les
pertes de réponse et livraisons dupliquées d'une même commande au dispatcher,
qui ne créent pas de nouvel appel sans transition de relance autorisée.
Prouver la borne d'un appel pour les commandes non idempotentes, le budget
des autres commandes et l'absorption des états terminaux ; auditer les axiomes.

Portée à rendre explicite : un seul dispatcher séquentiel et son journal en
mémoire, conservé pendant l'exécution. Une duplication de requête à cette
frontière est dédupliquée par command_id ; ce n'est pas une duplication
arbitraire effectuée ensuite par le périphérique physique. Ni redémarrage
avec perte du journal ni matériel qui agit deux fois à un appel ne peuvent
être couverts par la garantie actuelle. La propriété sera nommée et documentée
en termes d'appels/handoffs, sans transformer cette limite en promesse physique.

### user

### agent

Preuves compilées et auditées dans `Effects/Commands.lean` :
`non_idempotent_at_most_once`, `attempts_bounded`, `terminal_absorbing`
et `Execution.toRun`. Le modèle contient explicitement pertes de réponse
et doublons d'entrée, avec une trace concrète vérifiée comprenant ces pannes.
La relance exige idempotence, état Dispatched et budget restant.

La propriété porte précisément sur les handoffs du même dispatcher avec
journal conservé ; pas sur une action physique unique après duplication
aval ou redémarrage. Cette limite est détaillée dans
`docs/verification/commandes.md` et le catalogue P19/P20. Les doublons d'entrée
conservent le cache ; une perte peut laisser UnknownOutcome, pas un faux succès.

Comparaison exécutable Lean/Python des 144 transitions, des 12 états terminaux
et de 384 combinaisons de garde de relance. Les tests Hypothesis existants
de pertes, erreurs et duplications d'entrée restent verts.

`./scripts/validate.sh complet` est vert : 843 tests moteur et 77 Codegen,
linters, Pyright, contrats, Kanban, Lean et audit des axiomes.
Passage en QA sur cette portée explicitement documentée ; done reste humain.

### user
