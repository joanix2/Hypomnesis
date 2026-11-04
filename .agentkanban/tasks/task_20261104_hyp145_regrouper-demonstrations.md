---
title: "HYP-145 · Regrouper les démonstrations et isoler les sorties"
lane: qa
created: 2026-11-04T17:15:45+01:00
updated: 2026-11-04T18:19:29+01:00
description: "P2 · S · Outillage · rangement demandé par l'utilisateur"
priority: P2
tags: [documentation, outillage, tests]
---

## Conversation

### user

**Ticket** HYP-145 · **Priorité** P2 · **Taille** S · **Epic** Outillage · **Labels** outillage, tests, documentation

Regrouper les langages métier, programmes et exemples dans `demo/`, sans déplacer le moteur.
Supprimer les résultats générés existants et les ignorer dans Git : ils sont le fruit
de l'exécution. Périmètre et destination confirmés explicitement par l'utilisateur.

#### Fichiers concernés

- `demo/`
- `tests/`
- `src/hypomnesis/lsp/analysis.py`
- `src/hypomnesis/cli.py`
- `scripts/validate.sh`
- `.github/workflows/ci.yml`
- `.gitignore`

### agent

Plan : déplacer ensemble `languages/`, `programs/` et `examples/` sous `demo/` afin de
préserver leurs chemins relatifs internes. Mettre à jour les références actives (tests,
documentation, CI, validation Lean et TextMate). Adapter la découverte M1→M2 du LSP
pour accepter une paire `programs/` et `languages/` sous tout dossier du workspace,
y compris `demo/`, sans perdre le fonctionnement des projets externes.
Les sorties CLI par défaut deviennent `demo/sortie/`, ignoré dans Git ; l'ancien
`sortie/rapport.json`, identifié comme rapport généré, sera supprimé puis son dossier
vide retiré. Les conversations historiques des tickets restent inchangées.
Pas de commit ni de push inclus dans cette demande.

### user

### agent

Rangement terminé : 25 sources déplacées sous `demo/languages/`, `demo/programs/` et
`demo/examples/`. Contenus métier comparés aux versions Git et préservés ; seuls les
commentaires d'invocation des exemples ont changé. Les références relatives des bancs
vers leurs programmes fonctionnent sans modification. Moteur conservé dans `src/`.

Tests, CI, certificat Lean, TextMate, documentation et mémoire projet mis à jour.
ADR 0011 précise les nouveaux emplacements sans réécrire l'ADR 0008 acceptée.
Le LSP retrouve les programmes depuis la racine du dépôt, depuis `demo/` et dans les
dispositions externes antérieures ; les sorties par défaut CLI, moteur et banc sont
maintenant sous `demo/sortie/`, ignoré dans Git.

Le rapport généré existant a été supprimé, ainsi que son dossier vide. Deux helpers de
tests écrivaient auparavant des rapports dans le dépôt : ils utilisent désormais
`tmp_path`. Après validation complète, ni `sortie/` ni `demo/sortie/` ne sont recréés.

Validation complète verte : 675 tests Python, Ruff, Pyright, schémas, Kanban,
compilation Lean, audit des axiomes et vérificateur de certificats. Six tests TextMate,
construction VSIX et test dans un hôte VS Code réel réussis. Graphe rafraîchi.
Aucun couloir modifié, aucun commit ni push ; changements préexistants conservés.

### user

### agent

L'utilisateur demande maintenant de tout committer : inclure le rangement des démonstrations,
les correctifs d'outillage en attente, les tags et priorités et les comptes rendus du Kanban.
Les caches, résultats d'exécution, dépendances installées et VSIX généré restent ignorés.
Validation avant commit ; aucun push demandé.

### user

### agent

Mise à jour du Kanban demandée : passage en `qa`. Rangement enregistré dans
`9e70271`, puis démonstrations migrées aux déclarations natives dans `6e2962f`.
Checklist complète ; dernière validation intégrée verte (735 tests et Lean),
sans résultat généré versionné. Validation humaine finale laissée à l'utilisateur.

### user
