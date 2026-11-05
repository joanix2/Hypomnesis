---
title: "HYP-037 · Lean F4b : pas de faux conflit"
lane: qa
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P2 · M · Vérification formelle (Lean) · dépend de HYP-035, HYP-036"
priority: P2
tags: [epistemique, lean, moteur-symbolique]
---

## Conversation

### user

**Ticket** HYP-037 · **Priorité** P2 · **Taille** M · **Epic** Vérification formelle (Lean) · **Dépend de** HYP-035, HYP-036 · **Labels** lean

#### Contexte

Si le moteur signale `Conflict`, l'incompatibilité est réellement dérivable des faits courants.

#### Tâches proposées

- Modéliser la détection de HYP-035 ; prouver sa correction (et sa complétude si elle est visée).

#### Critères d'acceptation

- Théorème sans `sorry`, ajouté à l'audit.

#### Fichiers concernés

- `formal/Hypomnesis/Epistemics/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`

### agent

HYP-005 adopte OBJ-11 et la spécification v0.3 §7.1 : `Conflict` appartient
à la cohérence, pas au support. La preuve devra établir une incompatibilité
réelle sans confondre estimation, inconnue et contradiction ; elle demeure
à réaliser dans ce ticket.

### user

### agent

Plan / todo / implement du lot Mac approuvé, sans sous-agent. HYP-035 et
HYP-036 sont en QA. Le modèle réutilisera les faits/provenances et la lecture
booléenne de la révision. Rapports fonctionnels et tuples d'invariants seront
comparés à une définition déclarative de compatibilité des assertions actives.
Prouver que tout rapport produit empêche cette compatibilité : valeurs
distinctes d'une clé déclarée fonctionnelle, ou tuple d'assertions refusé par
un invariant déclaré. Ni support faible ni absence de valeur ne suffisent.

Les valeurs seront génériques avec égalité décidable, les invariants des
fonctions booléennes pures de l'hôte. Le pont Python sera testé sur valeurs
typées, historique et retraits. La pureté et la fidélité des liaisons hôte
resteront explicites ; ne pas prétendre prouver une théorie métier ou le
code Python complet. La complétude d'un raisonneur logique général n'est
pas visée.

### user

### agent

Implémentation vérifiée : P31 `Conflicts.no_false_conflict` démontre qu'un
rapport calculé empêche de satisfaire les contraintes déclarées sur les
assertions actives. Les lemmes vérifient les témoins fonctionnels et
l'alignement des tuples d'invariants. Valeurs et prédicats génériques ;
aucun `sorry`, audit limité à `propext` et `Quot.sound`.

48 bases réelles, chacune sous les politiques report et best-support,
concordent avec le détecteur Lean : 96 comparaisons des rapports complets
après effacement explicite des préférences. L'égalité typée est projetée
par `Fact.same_value`, vérifiée sur chaque paire du corpus. Historique,
retraits, sources estimées/hypothétiques et valeurs structurées sont inclus.
Les 28 tests ciblés passent. Le modèle est obligatoire en CI et dans
`validate.sh lean|complet`.

Validation complète verte : linters, Pyright, suites noyau/Codegen, audit
Lean et 89 tests obligatoires, dont 500 termes différentiels. Catalogue,
guide et TECHNICAL documentent les frontières : prédicats hôte supposés
purs/fidèles, pas de preuve du code Python ni de raisonneur universel.
Passage en QA pour revue humaine ; pas de passage agent en done.

### user

### agent

Validation rapide et rafraîchissement Graphify/relations Kanban également
verts après le passage en QA. Jalon prêt au commit local ; aucun push.

### user
