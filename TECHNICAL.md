# Hypomnesis — document technique

Référence d'implémentation pour les agents et les humains. Les décisions sont dans
`docs/adr/`, la vision dans `docs/specification/`, l'avancement dans `.agentkanban/tasks/`.

## Pipeline du langage

| Étape | Fichier | Rôle |
|---|---|---|
| Grammaire | `src/hypomnesis/language/grammar/hypomnesis.lark` | Lark LALR(1), points d'entrée `start` et `expr` |
| Parser | `src/hypomnesis/language/parser.py` | arbre Lark → AST (`language/ast.py`) |
| Types | `src/hypomnesis/language/typesystem/types.py` | termes, unification à niveaux, schémas, affichage |
| Vérification | `src/hypomnesis/language/typesystem/infer.py` | résolution des noms, HM, élaboration vers la Core IR ; incrémental et transactionnel |
| Core IR | `src/hypomnesis/ir/core.py` | IR résolue exécutée par le runtime ; annotée par les types inférés (paramètres, quantificateurs, instanciations) |
| Annotations | `src/hypomnesis/language/typesystem/annotations.py` | fermeture des variables non contraintes (`unit`) et vérification de l'invariant « toute variable de type est liée » |
| Runtime | `src/hypomnesis/runtime/interpreter.py` | nœuds compilés en fermetures ; appels terminaux par trampoline |
| Primitives | `src/hypomnesis/runtime/natives.py` | registre fermé de primitives pures |
| Prélude | `src/hypomnesis/stdlib/prelude.hyp` | bibliothèque standard en Hypomnesis |
| Session | `src/hypomnesis/session.py` | enchaîne tout ; pile de 512 Mo pour la récursion profonde |
| CLI | `src/hypomnesis/cli.py` | `run`, `check`, `repl` |

## Moteur générique et langages (ADR 0008)

`src/hypomnesis/engine/` (M3) charge un langage M2 et exécute un programme M1 :

| Module | Rôle |
|---|---|
| `engine/language.py` | chargement d'un paquet `languages/<langage>/` : manifeste validé (`language-manifest/1.0.0`), sources Hypomnesis, contrats, adaptateurs confinés au paquet |
| `engine/design.py` | procédure générique `constrained-design` : connu/inconnu, estimation, `Problem.problem` → Z3 → vérification, validation, actions, révision |
| `engine/feedback.py` | procédure générique `feedback-loop` : capteur, décision, actionneur, vérification sous hypothèse, budget |
| `engine/bridge.py` | valeur Hypomnesis → JSON (commandes) ; `Problem.problem` → Problem IR |

Briques M3 utilisées : `epistemics/` (provenance, connaissances), `ir/problem.py`,
`backends/z3_solver.py`, `effects/dispatcher.py`, `observability/trace.py`, et le module
`Problem` de la bibliothèque standard.

Convention des fonctions M2 appelées par `constrained-design` : elles reçoivent la demande
puis la valeur de chaque champ déclaré dans `estimators`, dans l'ordre du manifeste.

CLI : `hypomnesis lancer LANGAGE [PROGRAMME] [--demande …] [--estimateur …] [--mode …]
[--observer champ=valeur] [--env cle=valeur] [--sortie DIR]`.

## Certificats

`src/hypomnesis/certify/` exporte la Core IR élaborée et annotée (prélude compris) en JSON,
format `certificate/1.0.0` validé par `contracts/schemas/certificate-1.0.0.json` :

- les variables locales sont des indices de de Bruijn (0 = lieur le plus proche) ;
- les variables de motif sont des emplacements numérotés (`{"bind": k}`) ;
- les variables de type sont nommées par définition et liées par des listes `forall` ;
- les littéraux portent leur sorte.

`load.py` fait l'opération inverse ; les tests vérifient `export(load(c)) = c` et que le programme
réimporté calcule les mêmes valeurs. CLI : `hypomnesis check FICHIERS --emit-certificate cert.json`.
Le vérificateur Lean `hypomnesis-check` (`formal/Main.lean`, `formal/Hypomnesis/Certificate.lean`)
les relit : `cd formal && lake build hypomnesis-check`, puis
`lake exe hypomnesis-check check cert.json` (codes : 0 accepté, 1 rejeté par `typeOf`, 2 hors du
fragment, 3 illisible) ou `eval cert.json` (sémantique de référence). Exemple entièrement dans
le fragment : `examples/basics/certifiable.hyp`.

## Contrats

`src/hypomnesis/contracts/` : schémas JSON Schema 2020-12 (enveloppe, manifeste d'extension) et
`SchemaRegistry` (validation des schémas à l'enregistrement, enveloppe puis payload).

## Vérification formelle

`formal/` (Lean 4.35, sans dépendance) : fragment de la Core IR, typage, évaluateur à budget,
preuves de sûreté, vérificateur correct et complet, monotonie du budget, provenance en
semi-anneau. Propriétés : `docs/verification/proprietes.md`. Stratégie : `docs/verification/strategie.md`.

## Exemples

- `examples/basics/`, `examples/mechanics/` : tour du langage, plaque du §4.2.

## Graphe de connaissances (Graphify)

`graphify-out/` (non versionné) contient le graphe du dépôt : code, docs, tickets. Il n'est
reconstruit qu'à la demande : `./scripts/validate.sh graphe` (Graphify puis réinjection du
Kanban). `CLAUDE.md` demande aux agents de l'interroger avant d'explorer le code.

```bash
graphify update .                     # reconstruire le graphe du code (sans LLM)
graphify query "comment est typé un match ?"
graphify path "Checker" "Interpreter"
graphify explain "Session"
```

Pour enrichir les relations sémantiques des documents (spécification, notes, tickets), lancer
`/graphify . --update` dans Claude Code : cette étape utilise des sous-agents.

## Kanban

`scripts/kanban.py` (bibliothèque standard uniquement) lit `.agentkanban/tasks/` :

| Commande | Rôle |
|---|---|
| `check` | format des tâches, couloirs, dépendances inconnues, cycles, tâche démarrée avant ses dépendances |
| `status [--json]` | tâches en cours, prêtes (avec ce qu'elles débloquent), bloquées (avec ce qu'elles attendent), en `qa` (à vérifier par l'utilisateur) |
| `graph [--wait]` | injecte tâches et relations (`depends_on`, `touches`, `references`, `defined_in`, `contains`) dans `graphify-out/graph.json`, sous le verrou de reconstruction de Graphify ; idempotent |

Les éléments injectés portent `_origin: "kanban"` et `source_file: .agentkanban/board.yaml`.
Une reconstruction incrémentale de Graphify conserve les nœuds mais perd les relations vers les
fichiers qu'elle réextrait : réinjecter après chaque `graphify update .`, ce que fait
`./scripts/validate.sh graphe`. L'injection prend le verrou de reconstruction de Graphify ;
`--wait` attend la fin d'une reconstruction en cours.

## Validation

Aucun hook git : les validateurs se lancent à la demande, via la skill `/valider`
(`.claude/skills/valider/`) ou `./scripts/validate.sh <mode>` :

| Mode | Contenu |
|---|---|
| `rapide` (défaut) | Ruff (lint, format), Kanban, tests |
| `complet` | pre-commit sur tout le dépôt (linters, Pyright, schémas, workflows, Lean), tests, audit des axiomes |
| `lean` | `lake build`, aucun `sorry`, audit des axiomes |
| `graphe` | `graphify update .` puis réinjection du Kanban |

La CI exécute les mêmes linters à chaque push.

## Commandes

```bash
./scripts/validate.sh                   # rapide : Ruff, Kanban, tests
./scripts/validate.sh complet           # tous les validateurs
./scripts/validate.sh graphe            # reconstruire le graphe Graphify + Kanban
python3 scripts/kanban.py status        # tâches prêtes et bloquées
.venv/bin/hypomnesis run examples/basics/tour.hyp
```
