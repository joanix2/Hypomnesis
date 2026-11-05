---
title: "HYP-011 · Import entre fichiers"
lane: qa
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P2 · M · Langage · dépend de HYP-002"
priority: P2
tags: [compilateur, metalangage, python]
---

## Conversation

### user

**Ticket** HYP-011 · **Priorité** P2 · **Taille** M · **Epic** Langage · **Dépend de** HYP-002 · **Labels** python

#### Contexte

La CLI charge les fichiers dans l'ordre donné ; il n'existe pas de dépendance déclarée entre fichiers (§4.1 « Modules et imports »). `examples/mechanics/plate.hyp` dépend implicitement de `units.hyp`.

#### Tâches proposées

- Concevoir la syntaxe (ADR) : par exemple, un fichier `units.hyp` définit le module `Units` et `open Units` le charge à la demande.
- Résoudre les chemins relativement au fichier et à un chemin de recherche ; détecter les cycles.
- Charger chaque fichier une seule fois par session.

#### Critères d'acceptation

- `hypomnesis run examples/mechanics/plate.hyp` fonctionne seul.
- Un import circulaire donne une erreur claire.
- ADR rédigée.

#### Fichiers concernés

- `src/hypomnesis/session.py`
- `src/hypomnesis/cli.py`
- `examples/mechanics/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`

### agent

Plan / todo / implement du lot Mac approuvé. Arbitrage utilisateur :
syntaxe Python pour les imports seulement : `import units`,
`import physique.units as mesures`, `from units import mm`,
`from units import mm as millimetres`. Les autres constructions restent
fonctionnelles, sans migration générale vers Python.

Résolution locale relative au fichier importeur, qualification des exports
par le module importé, alias locaux, chargement unique par chemin canonique
et session, cycles explicitement refusés. Aucun import étoile ni téléchargement.
`open` ne charge pas de fichier. Un fichier déclarant `module Length`
exporte `units.Length`, pas automatiquement `units.mm`. Aucun code Python
ni programme utilisateur exécuté par check/LSP/catalogue.

Implémentation : grammaire/AST, résolution et environnement de modules,
Session, CLI, LSP/overlays, couches et catalogue, certificats et coloration.
Réutiliser les mécanismes de DAG applicables sans détourner les règles
de confinement des couches. Migrer la démo désormais située dans
demo/examples/mechanics. ADR, tests de chemins/alias/types/cycles/diamants/
échecs et non-exécution, puis complet/rapide/graphe avant QA.

### user

### agent

Implémentation HYP-011 terminée et validation complète verte : imports
Python locaux, alias et espaces de noms, identité partagée des types,
isolation des dépendances, cache canonique, cycles et collisions explicites.
Les échecs statiques sont transactionnels ; un échec d'évaluation impliquant
un import exige une nouvelle session pour ne pas rejouer ses effets.

Les frontends partagent le chargeur : CLI run/check et lancer des programmes
M1, couches confinées, LSP avec overlays transitifs et catalogue documentaire
Codegen. Les origines des programmes M1 sont conservées même si le répertoire
courant diffère. L'analyse statique n'exécute ni expressions ni adaptateurs.
La démo demo/examples/mechanics/plate.hyp fonctionne seule et conserve
aire = 9600, volume = Some 38400 et valid = true.

ADR 0017, référence et documentation technique actualisées. Aucun changement
de Core IR ni de sémantique Lean : les imports s'élaborent vers les
constructions existantes ; un programme importé passe le vrai checker Lean.
28 cas de tests d'import dédiés, intégrations CLI/LSP/catalogue/certificat,
101 tests ciblés finaux et validation complète (linters, types, schémas,
tests noyau/Codegen, construction Lean et audit des axiomes) verts.
Le client de test LSP conserve maintenant les notifications d'autres URI,
au lieu de les perdre dans une course révélée par les imports transitifs.

Coloration : 12 tests TextMate et hôte VS Code réel verts, y compris une
dépendance modifiée sans enregistrement. Extension 0.1.3 installée sans
recharger la fenêtre utilisateur. Passage en QA, done reste humain.
Validation rapide et rafraîchissement du graphe avant le commit local ;
aucun push. Le lot Mac n'est pas fini : HYP-012 est le jalon suivant.

### user
