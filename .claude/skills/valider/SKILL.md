---
name: valider
description: Lance les validateurs du projet Hypomnesis à la demande (lint, types, tests, Kanban, preuves Lean, graphe Graphify). À utiliser avant de déclarer une étape terminée, avant de committer ou de pousser, après une modification de formal/ ou de .agentkanban/, quand l'utilisateur demande de « valider » ou de « vérifier », ou pour rafraîchir le graphe. Arguments possibles : rapide (défaut), complet, lean, graphe.
---

# /valider

Les validateurs ne sont branchés sur aucun hook git : rien ne bloque un commit. C'est à toi de
les lancer au bon moment, avec le mode adapté, via `scripts/validate.sh`.

## Choisir le mode

| Mode | Contenu | Quand |
|---|---|---|
| `rapide` (défaut) | Ruff (lint et format), Kanban, tests | après une modification de code, avant chaque commit |
| `complet` | pre-commit sur tout le dépôt (linters, Pyright, YAML/JSON/TOML, schémas, workflows, Lean), tests, audit des axiomes | avant de déclarer une tâche finie, avant un push |
| `lean` | `lake build`, aucun `sorry`, audit des axiomes | après toute modification de `formal/` |
| `graphe` | `graphify update .` puis réinjection du Kanban dans le graphe | après des changements de code ou de tâches, avant d'interroger Graphify |

Si l'utilisateur a passé un argument (`/valider complet`), utilise ce mode. Sinon choisis selon ce
qui a changé (`git status`, `git diff --stat`) : `formal/` modifié → ajoute `lean` ; fin de
tâche → `complet`.

## Exécuter

```bash
./scripts/validate.sh <mode>
```

Le script exécute toutes les étapes même si l'une échoue, puis affiche un résumé (`ok` / `ÉCHEC`).
Code de sortie 1 s'il y a un échec. En mode `complet`, pre-commit peut corriger seul des détails
de forme (espaces, fins de fichier, Ruff `--fix`) : regarde `git diff` après coup.

## Après

1. Si tout est `ok` : dis-le en une ligne avec le mode lancé.
2. En cas d'`ÉCHEC` : lis la sortie de l'étape concernée, corrige ce qui relève de la tâche en
   cours, puis relance **le même mode**. Ne corrige pas en silence un problème sans rapport avec
   la tâche : signale-le, ou crée un ticket (`HYP-NNN`) s'il est réel.
3. Ne contourne jamais un validateur : pas de `# noqa`, de `type: ignore` ou de test désactivé
   pour faire passer une étape, et jamais de `sorry` en Lean.
4. Rends compte fidèlement : nombre de tests, étapes en échec, ce qui a été corrigé, ce qui reste.
