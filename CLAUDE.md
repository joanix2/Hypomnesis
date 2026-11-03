## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).

## Kanban et graphe des dépendances

Les tâches de `.agentkanban/tasks/` sont injectées dans le graphe Graphify (nœuds `HYP-NNN · titre`) avec les relations `depends_on`, `touches` (fichiers concernés), `references` et `defined_in`.

- `python3 scripts/kanban.py status` : tâches prêtes (dépendances terminées), bloquées, en cours.
- `python3 scripts/kanban.py check` : format et dépendances.
- `graphify affected "HYP-020" --relation depends_on --depth 5` : tâches débloquées, transitivement.
- `graphify affected "infer.py" --relation touches --depth 1` : tâches qui touchent un fichier.
- Le graphe n'est pas reconstruit automatiquement : `./scripts/validate.sh graphe` (Graphify puis réinjection du Kanban).

## Validation

Aucun hook git ne bloque les commits. Lancer les validateurs à la demande avec la skill `/valider` (ou `./scripts/validate.sh rapide|complet|lean|graphe`) : `rapide` avant chaque commit, `complet` avant de déclarer une tâche finie ou de pousser.
