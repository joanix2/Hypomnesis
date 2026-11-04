---
title: "HYP-045 · Démonstration : deux plugins derrière la même interface"
lane: qa
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P1 · S · Phase 3 — Extensions et contrats · dépend de HYP-044"
priority: P1
tags: [capacites, contrats, exemple, moteur-symbolique, python, tests]
---

## Conversation

### user

**Ticket** HYP-045 · **Priorité** P1 · **Taille** S · **Epic** Phase 3 — Extensions et contrats · **Dépend de** HYP-044 · **Labels** python, exemple

#### Contexte

Critère d'acceptation du §16.4 et hypothèse H6.

#### Tâches proposées

- Deux estimateurs d'épaisseur (règle simple, régression) derrière la même interface.
- Le même programme fonctionne avec l'un ou l'autre, sur simple changement de configuration.

#### Critères d'acceptation

- Test d'intégration qui exécute le programme avec chaque plugin sans modifier le source.

#### Fichiers concernés

- `examples/mechanics/`
- `tests/integration/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`

### agent

HYP-044 est en QA. Tranche locale du plan Mac : garder le programme M1
strictement identique et sélectionner un manifeste d'extension depuis
l'hôte. Les deux fournisseurs traversent le même PythonBackend
contractuel en sous-processus : la règle reste Plaque.estimer_regle en
M2, la régression réutilise le backend générique scikit-learn optionnel.
Ni formule de mécanique ni nouvelle pile de plugins dans M3.
La confiance est un choix de démonstration explicite, pas la RMSE
convertie en probabilité ; les faits restent Estimated.

### user

### agent

Les manifestes règle/régression sélectionnent deux fournisseurs réels
derrière la même signature Plaque.demande -> float et les mêmes schémas.
Le programme plaque_plugins.hyp reste strictement identique : seuls le
fichier de configuration et la métadonnée fournisseur changent dans l'hôte.
Règle M2, caractéristique M2 et régression générique existantes réutilisées.
Chaque appel traverse le backend contractuel HYP-044 en sous-processus
avec délai effectif ; préparation statique sans import/démarrage.

Tests réels : règle 3,2 mm, régression proche mais distincte, épaisseur
résolue 3 mm et verdict Valide dans les deux cas. Provenance Estimated,
fournisseur/version et trace du processus vérifiés. Test sans sklearn
pour la règle/statique ; test avec sklearn pour la substitution complète.
Extrapolation refusée explicitement, sans repli sur la règle ; mauvais
rôle de manifeste refusé avant enregistrement.

Validation ciblée : 20 tests backend/substitution verts ; validation
complète verte, y compris les suites globales, types, contrats et Lean.
Commandes et limites documentées, dry-run par défaut. Passage en QA,
done réservé à l'utilisateur. Aucun changement de M3 nécessaire.

### user
