<!-- BEGIN AGENT KANBAN — DO NOT EDIT THIS SECTION -->
## Agent Kanban

Read `.agentkanban/INSTRUCTION.md` for task workflow rules.
Read `.agentkanban/memory.md` for project context.

If a task file (`.agentkanban/tasks/**/*.md`) was referenced earlier in this conversation, re-read it before responding and always respond in and at the end the task file.
<!-- END AGENT KANBAN -->

## Agents du projet

Sous-agents Claude Code définis dans `.claude/agents/`, alignés sur le workflow plan → todo → implement :

| Agent | Rôle | Écrit dans |
|---|---|---|
| `hyp-planner` | choisit la tâche prête suivante, planifie, produit la checklist, crée les tickets | `.agentkanban/` uniquement |
| `hyp-implementer` | implémente une tâche Python dont la checklist existe, commits réguliers | `src/`, `tests/`, `demo/examples/`, docs |
| `hyp-prover` | preuves Lean 4, sans `sorry`, axiomes audités | `formal/`, `docs/verification/` |
| `hyp-reviewer` | vérifie une tâche contre ses critères et la définition de fini | rien (lecture seule) |

Enchaînement type : `hyp-planner` (plan, todo) → `hyp-implementer` et/ou `hyp-prover` (implement) → `hyp-reviewer` → décision humaine de passer la tâche en `done`.
