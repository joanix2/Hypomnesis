---
title: "HYP-035 · Détection et signalement des conflits"
lane: qa
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P1 · M · Phase 2 — Moteur épistémique · dépend de HYP-033"
priority: P1
tags: [epistemique, moteur-symbolique, python]
---

## Conversation

### user

**Ticket** HYP-035 · **Priorité** P1 · **Taille** M · **Epic** Phase 2 — Moteur épistémique · **Dépend de** HYP-033 · **Labels** python

#### Contexte

Statut `Conflict` (§7.1) : informations incompatibles ; contradictions signalées lors de la révision (§7.3 étape 5).

#### Tâches proposées

- Définir l'incompatibilité : deux valeurs distinctes pour un attribut fonctionnel, violation d'un invariant déclaré.
- Rapport de conflit : faits en cause et leurs provenances.
- Politiques de résolution configurables (préférer le meilleur support, signaler sans trancher).

#### Critères d'acceptation

- Aucun conflit signalé sans incompatibilité réelle (test par construction).
- Le rapport cite les observations à l'origine du conflit.

#### Fichiers concernés

- `src/hypomnesis/epistemics/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`

### agent

HYP-005 adopte les axes du §7.1 de la spécification v0.3. `Conflict` relève
de la cohérence, indépendamment du support. Une préférence pour le meilleur
support ne doit pas masquer les incompatibilités ni effacer leurs provenances.
Les critères historiques de détection restent applicables.

### user

### agent

Plan / todo / implement du lot Mac approuvé, sans sous-agent. HYP-033 est
en QA. Ce ticket est indépendant des preuves HYP-022 ; je le prends après
HYP-010 pour terminer un jalon épistémique local.

Le détecteur sera déclaratif et sans mutation : attributs fonctionnels
identifiés par leur clé, invariants purs fournis par M2/hôte et rapports
immuables citant les faits et sources. Il examinera aussi les faits conservés
dans le journal : deux observations successives de la même clé, dont aucune
source n'est retirée, restent deux assertions concurrentes. Une révision
explicite retire au contraire l'ancienne source.

Les lectures de provenance booléenne et de support existantes seront
réutilisées. Préférer le meilleur support ne supprimera aucun conflit ;
une égalité de supports incompatibles restera sans sélection. Les invariants
violés ne seront jamais déclarés réparés par une préférence. Les règles
incomplètes seront signalées comme non vérifiées, pas comme cohérentes.
La base exposera un rapport vivant, recalculé après toute révision lors de
sa consultation, sans changer les retours existants des opérations de révision.
La preuve Lean de correction reste HYP-037.

### user

### agent

Implémentation terminée : rapports immuables sur les assertions encore étayées
du journal et de la projection courante, attributs fonctionnels déclarés,
invariants purs n-aires et sources originales citées. Une liaison testée
exécute l'invariant dans le vrai interpréteur Hypomnesis ; aucune logique
métier ajoutée au moteur Python.

Le meilleur support réutilise la sélection des métavariables, désormais basée
sur l'égalité typée des instantanés Fact. Les préférences n'écrasent ni faits
ni provenances ; les égalités incompatibles restent explicitement ambiguës.
Les révisions et alternatives de provenance sont couvertes, sans cache périmé.
Les contrôles incomplets restent non vérifiés et les erreurs remontent.

115 tests ciblés verts, dont deux propriétés Hypothesis de 100 exemples
chacune : comparaison avec les assertions vivantes et avec tous les couples
réellement incompatibles d'un invariant. Validation complète verte après la
correction automatique de mise en forme du nouveau fichier de tests :
linters/types, suites cœur/Codegen, audit Lean, 86 tests Lean obligatoires
et 500 termes différentiels. Aucune inférence LLM, aucun sous-agent ni push.
La preuve Lean HYP-037 et la persistance HYP-034 ne sont pas déclarées finies.
Passage en QA proposé ; done reste une décision humaine.

### user

### agent

Validation rapide finale et rafraîchissement du graphe verts. Le formateur a
également harmonisé les deux exemples Python de la documentation ; aucune
modification sémantique supplémentaire. Checklist terminée, commit local,
aucun push.

### user
