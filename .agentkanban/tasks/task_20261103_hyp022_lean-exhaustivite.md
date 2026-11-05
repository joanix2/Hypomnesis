---
title: "HYP-022 · Lean F1c : un `match` exhaustif ne lève jamais `Match_failure`"
lane: qa
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P1 · M · Vérification formelle (Lean) · dépend de HYP-020, HYP-010"
priority: P1
tags: [certification, lean, metalangage]
---

## Conversation

### user

**Ticket** HYP-022 · **Priorité** P1 · **Taille** M · **Epic** Vérification formelle (Lean) · **Dépend de** HYP-020, HYP-010 · **Labels** lean

#### Contexte

Une fois l'exhaustivité implémentée côté Python (HYP-010), on prouve sa contrepartie Lean.

#### Tâches proposées

- Définir `exhaustive : Σ → Ty → List Pattern → Bool` (même algorithme que HYP-010).
- Prouver : pour une valeur bien typée, des motifs exhaustifs dont au moins un bras sans garde la couvre, le filtrage réussit.
- Corollaire : un programme dont tous les `match` sont exhaustifs ne rend jamais `matchFailure`.

#### Critères d'acceptation

- Théorème prouvé et ajouté à l'audit.
- Tests croisés : Python et Lean donnent le même verdict sur un corpus.

#### Fichiers concernés

- `formal/Hypomnesis/Core/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`

### agent

Reprise du lot Mac : plan / todo / implement de HYP-022, après les imports
et signatures validés. Travail séquentiel sans sous-agent et sans push.

Conserver l'analyse par matrices de HYP-010 : colonnes typées,
spécialisation des booléens/produits/constructeurs, matrice par défaut
pour les domaines ouverts, gardes exclues de la couverture. La preuve
doit relier un verdict positif à matchPat sur toute valeur bien typée,
pas redéfinir « exhaustif » comme l'hypothèse à démontrer.

Prévoir un budget explicite et un résultat indéterminé si la recherche
l'épuise, sans déclarer un programme couvert. Ajouter preuves Lean et
audit, corpus Python/Lean, documentation exacte de la portée de la preuve,
puis validation complète/rapide/graphe avant QA et commit.
Le corollaire programme entier doit tenir compte des fermetures, gardes,
sous-expressions et appels récursifs ; aucune extrapolation depuis la seule
sélection d'un bras.

### user

### agent

Implémentation et vérification ciblée réalisées :

- Calcul `Coverage.check` par matrices, budget explicite et `Option Bool`.
  L'écart à la signature Bool proposée est intentionnel : l'épuisement du
  budget ne doit jamais être confondu avec une preuve positive.
- Correction positive reliée à `matchPat` et sélection garantie sous gardes
  arbitraires lorsque les bras non gardés couvrent.
- `Certified` renforce le typage de la Core IR réelle, sans nouvel évaluateur.
  `eval_protected` traite sous-expressions, fermetures et récursion ; le
  corollaire clos exclut `matchFail` pour tout budget.
- Exemples Lean : longueur récursive calculant 3 et véritable chaîne gardée
  calculant 1 après une garde fausse, avec preuves de sûreté pour tout budget.
- 31 matrices ciblées et 240 générées concordent entre les vrais sites du
  checker Python et Lean ; quatre limites de budget sont testées.
  Les 41 tests ciblés (pont et régressions HYP-010) passent.
- Catalogue P34–P35 et frontières documentés ; CI et validateur Lean branchés.

Frontière explicite : ni le décodeur de certificats ni `check --strict`
ne construisent encore une dérivation `Certified`. Le corollaire porte sur
les programmes munis de cette dérivation, pas sur tout programme Python
sans avertissement. La normalisation des alias/alternatives du corpus est
testée, pas prouvée, et ne justifie aucune équivalence des alternatives
gardées imbriquées. Terminaison et absence d'erreurs explicites restent hors
garantie. Validation complète, rapide et graphe à exécuter avant QA/commit.

### user

### agent

Validation complète verte : tous les linters/Pyright, suites moteur et
Codegen sans appel LLM, build/audit Lean sans axiome ajouté, certificats
et corpus de couverture exécutés avec Lean obligatoire. Rafraîchissement
Graphify/Kanban vert. Passage en QA pour revue humaine ; aucune clôture
automatique en done. Validation rapide avant le commit local, aucun push.

### user

### agent

Validation rapide et graphe final verts, aucune régression ni `sorry`.
Checklist complète ; jalon prêt au commit local sur main, sans push.
HYP-023 (polymorphisme explicite rang 1) reste la prochaine étape du lot.

### user
