---
title: "HYP-027 · Pont F3d : `hypomnesis check --certify` et certification en CI"
lane: doing
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P0 · S · Vérification formelle (Lean) · dépend de HYP-026, HYP-004"
priority: P0
tags: [certification, ci, compilateur, outillage, python]
---

## Conversation

### user

**Ticket** HYP-027 · **Priorité** P0 · **Taille** S · **Epic** Vérification formelle (Lean) · **Dépend de** HYP-026, HYP-004 · **Labels** python, ci

#### Contexte

Dernière étape du pont : rendre la certification utilisable et systématique.

#### Tâches proposées

- `--certify` : émettre le certificat, appeler `hypomnesis-check`, échouer si refusé.
- Job CI qui certifie tous les fichiers de `examples/`.
- Mettre à jour la ligne P3 de `proprietes.md` (garantie de bout en bout).

#### Critères d'acceptation

- CI verte avec certification ; un exemple volontairement mal élaboré, injecté dans un test, est refusé.

#### Fichiers concernés

- `src/hypomnesis/cli.py`
- `.github/workflows/ci.yml`
- `docs/verification/proprietes.md`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`

### agent

Plan HYP-027 : --certify exporte puis exige l'acceptation du vrai checker
Lean (découverte PATH/build local ou --checker, délai fini, erreurs explicites).
--emit-certificate seul reste un export validé structurellement. La sortie
JSON attend la fin de la certification : aucun succès avant un refus ultérieur.
Renvoyer la session réellement chargée depuis un fichier de langage, pour
ne jamais certifier à tort le seul prélude.

Tester acceptation réelle, injection d'une mauvaise élaboration, codes
1/2/3, exécutable absent, timeout, erreurs d'écriture et nettoyage temporaire.
La CI appellera cette CLI et exercera le pont réel. Attention : les exemples
avec records, floats/strings ou natifs non entiers restent hors du fragment ;
leur couverture totale ne sera pas annoncée ni obtenue par contournement.

### user

### agent

Pont opérationnel et validation complète verte (Python, Codegen, Lean,
audit et CLI certifiante). 31 tests ciblés de certification passent avec
le vrai exécutable. Correction importante : une entrée de langage ne fait
plus exporter par erreur la session préliminaire contenant seulement le prélude.
Diagnostics JSON uniques, délais, choix explicite du checker, refus et
nettoyage temporaire couverts.

La mesure des six exemples est reproductible en CI : certifiable accepté ;
tour refusé sur string ; plaque sur record Knowledge.t ; regles/units/plate
sur float. C'est une couverture des refus, pas six certifications.
P3 précise la frontière terme Lean / runtime Python.
Guide : [certification](../../docs/verification/certification.md).

HYP-027 reste donc doing, sans passage QA global. Les extensions de
records HYP-021 et de scalaires HYP-150 (nouveau prérequis découvert)
sont nécessaires, et d'autres obstacles pourront ensuite apparaître.
On poursuit les prérequis indépendants HYP-080/081/082 du MVP, plutôt que
d'affaiblir la certification ou de revendiquer tous les P0 terminés.

### user
