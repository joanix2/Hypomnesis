---
title: "HYP-132 · Extension VS Code : linter du DSL par serveur de langage"
lane: qa
created: 2026-11-04T08:56:00+01:00
updated: 2026-11-04T18:19:29+01:00
description: "P2 · M · Outillage et visualisation · dépend de HYP-130, HYP-131"
priority: P2
tags: [compilateur, dsl, metalangage, outillage, python, vscode]
---

## Conversation

### user

**Ticket** HYP-132 · **Priorité** P2 · **Taille** M · **Epic** Outillage et visualisation · **Dépend de** HYP-130, HYP-131 · **Labels** python, vscode, outillage

#### Contexte

Voir les erreurs du DSL directement dans l'éditeur, en réutilisant le vrai compilateur plutôt qu'une seconde analyse. Le protocole LSP évite de lier cet outillage à VS Code.

#### Tâches proposées

- Serveur de langage Python avec `pygls`, qui appelle le compilateur et publie ses diagnostics ; client `vscode-languageclient` dans l'extension.
- Trouver le langage M2 d'un programme M1 (`langage.json` le plus proche, ou réglage de l'extension).
- Vérifier à la frappe avec un délai d'attente, et annuler les analyses devenues obsolètes.
- Hors périmètre, à ouvrir en ticket si utile : survol des types, complétion, aller à la définition.

#### Critères d'acceptation

- Une erreur de syntaxe ou de type apparaît soulignée au bon endroit et dans l'onglet Problèmes, puis disparaît une fois corrigée.
- Les messages sont identiques à ceux de `hypomnesis check`.
- Tests du serveur sans VS Code, au niveau du protocole.
- `./scripts/validate.sh complet` vert.

#### Fichiers concernés

- `editors/vscode/`
- `src/hypomnesis/lsp/`
- `pyproject.toml`

#### Références

- Conventions et définition de fini : `.agentkanban/memory.md`

### agent

Note (HYP-130) : le format de diagnostic à consommer est le contrat `diagnostics/1.0.0` (`src/hypomnesis/contracts/schemas/diagnostics-1.0.0.json`), produit par `hypomnesis check --format json [--langage DOSSIER]` ou, en Python, par `HypomnesisError.to_diagnostic(fichier)` + `diagnostics_document([...])` (`hypomnesis.language.errors`). Positions 1-based, fin exclusive, `null` sans étendue ; `stage` ∈ `syntax|name|type|runtime|error`. Limites d'étendue : voir `TECHNICAL.md` § « Diagnostics structurés ».

### user

### agent

Demande utilisateur : coloration et linter intégrés. Plan : serveur pygls optionnel
(`hypomnesis[lsp]`) et client VS Code, transport stdio, positions UTF-16. Chaque analyse
utilise une session neuve du compilateur en vérification statique uniquement, dans un
processus annulable après délai de frappe ; aucun adaptateur métier ni programme utilisateur
n'est exécuté. Contexte M2 détecté par manifeste proche ou `programs/<nom>` vers
`languages/<nom>`, surcharge par réglage. Les sources M2 ouvertes sont superposées à leur
contenu disque ; les diagnostics réutilisent les messages et étendues du compilateur.
Tests prévus au protocole, sans VS Code, puis génération du VSIX et validation complète.
Checklist créée ; couloirs conservés.

### user

### agent

Serveur pygls livré sous `src/hypomnesis/lsp/`, accessible par `hypomnesis-lsp` ou
`python -m hypomnesis.lsp.server` après installation de l'extra `lsp` (également inclus
dans `dev`). Le client VS Code utilise `.venv` automatiquement ou `hypomnesis.pythonPath`.
Contexte M2 automatique ou réglable, superposition des sources non enregistrées,
vérification statique uniquement. Les sous-processus de compilation sont annulés et
récoltés ; arrêt du serveur attend leur fin. Délai par défaut 300 ms, limite d'analyse 30 s.

Seize tests Python nouveaux réussis : messages identiques au compilateur, diagnostics
de syntaxe/type/nom, disparition après correction et fermeture, frappe rapide sans
publication obsolète, source M2 non enregistrée, configuration explicite, erreurs de
manifeste, absence d'évaluation et annulation effective du sous-processus.
Le protocole stdio est exercé avec positions UTF-16 et négociation UTF-8/32, dont une
édition incrémentale après un caractère Unicode hors BMP.

Le test réel d'hôte VS Code confirme une erreur de type à la colonne attendue, puis son
effacement après correction non enregistrée. Le VSIX a été installé localement et son
identifiant confirmé. Validation complète : 671 tests, Ruff, Pyright, schémas, Kanban,
Lean et audit des axiomes verts ; six tests TextMate et audit npm verts. Graphe mis à jour.
Documentation et checklists complétées ; aucun survol, complétion ou navigation ajouté.
Couloir conservé sous contrôle utilisateur ; changements non poussés.

### user

### agent

Commit demandé explicitement par l'utilisateur : enregistrement du lot HYP-131/132
(extension, serveur, tests, dépendances, CI et documentation associée).
Les autres changements Kanban et outillage restent séparés ; aucun push demandé ici.

### user

### agent

Mise à jour du Kanban demandée : passage en `qa`. LSP enregistré dans `befd715`,
puis raccordé aux déclarations natives et imports transitifs dans `6e2962f`.
Le contexte se découvre désormais via `langage.hyp`, et non `langage.json`.
Dernière validation intégrée verte : 735 tests Python, Python/Lean et hôte VS Code
réel. Checklist complète ; validation humaine finale non effectuée par l'agent.

### user
