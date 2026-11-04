---
title: "HYP-027 · Pont F3d : `hypomnesis check --certify` et certification en CI"
lane: qa
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

### agent

Reprise de la couverture globale après HYP-021 et HYP-150, tous deux QA
et validés. Cinq exemples sur six sont acceptés ; le premier obstacle
restant de tour est le motif alternatif racine.

Plan de l'itération finale : traduire les alternatives racines en chaînes
de case du noyau existant, sans ajouter une primitive de confiance.
Vérifier la même signature de variables par slot entre alternatives,
même permutées. Si une alternative correspond mais sa garde est fausse,
passer au cas source suivant, jamais réessayer l'autre alternative.
Les alternatives imbriquées et alias non modélisés restent explicitement
refusés ; aucune prétention de preuve d'exhaustivité HYP-022.

Exiger alors six acceptations réelles, via checker et pont CLI, sans statut
d'exemption. Renforcer le validateur et la CI sur ces tests après build,
puis validation complète, audit, rapide, graphe et commit.

### user

### agent

Couverture globale effectivement obtenue : les six exemples actuels sont
acceptés par le vrai checker ET par check --certify. Le test d'inventaire
interdit désormais les exemptions hors fragment ; chaque nouveau fichier
doit être couvert et accepté. Les formes non modélisées continuent à
échouer explicitement (test alias), et l'élaboration falsifiée est refusée.

Les alternatives racines sont dérivées en case, avec contrôle du même type
par slot et permutations. Tests différentiels : garde fausse sans réessai
de l'autre alternative, alternatives chaînées et signatures incompatibles
même si les variables sont inutilisées. Le tour complet calcule bien 42,
220 et le compte alice à 150, comme Python.

Validation complète verte, dont 52 tests d'intégration Lean après rebuild
du checker ; audit sans sorry/axiome non autorisé. CI et validateur local
exigent désormais cette couverture après build. Les preuves restent celles
du fragment traduit ; ni exhaustivité générale ni raffinement Python complet
ne sont revendiqués. Documentation des limites maintenue.

HYP-027 passe en QA, pas done : les passages done restent humains. C'est
le dernier P0 qui restait en cours ; les autres P0 sont déjà QA/done.

### user

### agent

Contrôle final : validations complète, rapide et graphe vertes ; inventaire
Kanban vérifié, 30 P0 au total, 27 en QA et 3 done, aucun P0 restant dans
todo/doing. Travail effectué sans sous-agent. Les changements sont regroupés
en trois jalons committés : records HYP-021, scalaires HYP-150 et clôture de
la couverture HYP-027. Aucun push effectué.

### user
