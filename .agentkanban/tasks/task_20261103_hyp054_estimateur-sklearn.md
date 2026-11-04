---
title: "HYP-054 · Estimateur scikit-learn (épaisseur de plaque)"
lane: qa
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P0 · M · Phase 4 — Raisonnement hybride · dépend de HYP-044, HYP-032"
priority: P0
tags: [capacites, estimateurs, moteur-symbolique, python]
---

## Conversation

### user

**Ticket** HYP-054 · **Priorité** P0 · **Taille** M · **Epic** Phase 4 — Raisonnement hybride · **Dépend de** HYP-044, HYP-032 · **Labels** python

#### Contexte

Estimateur initial (§15.1) ; il propose une valeur pour la métavariable « épaisseur » du scénario MVP.

#### Tâches proposées

- Petit modèle entraîné sur un jeu synthétique documenté, versionné.
- Résultat de support `Estimated`, avec modèle, version et incertitude dans la provenance (§7.2).

#### Critères d'acceptation

- La provenance de l'épaisseur estimée contient le modèle et sa version.

#### Fichiers concernés

- `src/hypomnesis/backends/sklearn/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`

### agent

Plan HYP-054 : backend de régression scikit-learn générique optionnel
(extra sklearn, pas de dépendance du noyau). Jeu synthétique M2 versionné,
entraînement et validation séparés et déterministes. Résultat typé avec
identité/version du modèle, domaine d'entraînement et RMSE de validation ;
cette incertitude empirique n'est pas une probabilité ni une certification.
Les requêtes hors domaine sont refusées explicitement.

L'hôte enregistre la proposition comme Estimated, avec modèle/version/RMSE
dans l'origine de sa source ; il ne l'observe pas et ne résout pas la
métavariable implicitement. La logique métier et le jeu de plaque restent
dans la démonstration M2. Tests optionnels exécutés dans la validation
complète, sans rendre scikit-learn obligatoire dans le job core-only.

### user

### agent

HYP-054 terminé et proposé en QA. Backend générique RegressionEstimator,
extra sklearn séparé des dépendances de base/dev, prédictions typées Result,
domaine explicite et refus de l'extrapolation. Jeu synthétique M2
plaque-epaisseur-synthetique@1.0.0 versionné ; validation disjointe,
RMSE empirique ≈ 0,01617 mm. Ce chiffre n'est ni une probabilité ni une
borne garantie, et le modèle ne certifie pas un dimensionnement réel.

Exemple examples/knowledge/estimate.py : proposition float Estimated,
identité/version/RMSE dans l'origine de la source, sans résolution implicite
de la MetaVar. 28 tests optionnels couvrent reproductibilité, données invalides,
bornes, diagnostics, multicaractéristiques et import paresseux. Tests de
frontière adaptés uniquement pour cet extra scientifique ; Codegen reste
strictement séparé.

Validation complète verte. Environnement isolé sans sklearn, NumPy, SciPy,
Ollama ou Codegen : import du noyau et de la façade du backend, puis Pyright
verts. README, TECHNICAL, guide des estimateurs et précision ADR 0012 à jour.
Aucun sous-agent. Fermeture done laissée à l'utilisateur.

### user
