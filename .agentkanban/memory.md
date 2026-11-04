# Mémoire du projet Hypomnesis

## Projet

Métalangage fonctionnel (syntaxe OCaml) pour définir des DSL métiers : connaissances, règles,
contraintes, effets contrôlés. Spécification : `docs/specification/cahier-des-charges-v0.2.md`.
Détails d'implémentation : `TECHNICAL.md`.

## Niveaux d'abstraction (ADR 0008) — règle structurante

- **M3** `src/hypomnesis/` : moteur, métalangage, bibliothèque standard, procédures génériques.
  **Aucun domaine** (test `test_engine_contains_no_domain`).
- **M2** `demo/languages/<langage>/` : langage métier en Hypomnesis (règles, estimateurs, contraintes,
  commandes), contrats, adaptateurs Python vers le monde extérieur seulement, `langage.hyp`.
- **M1** `demo/programs/<langage>/` : programmes écrits dans un langage M2.
- **M0** `demo/sortie/` : résultats (non versionné).
- Les dépendances ne vont que vers le niveau supérieur. Jamais de logique métier en Python.

## Couches symboliques (ADR 0013, HYP-147)

- Déclaration native `language nom = { version = "..."; imports = ["../base"]; … }` dans
  le fichier d'entrée `.hyp` (par convention `langage.hyp`). Plus de lecture de `langage.json`.
- Imports locaux de fichiers/dossiers, DAG dépendance → utilisateur, déduplication des diamants,
  cycles/identités/collisions refusés. Bibliothèques sans procédure autorisées.
- Les I/O Python sont déclarées par `@sensor`, `@actuator`, `@environment`, `@transcriber`
  depuis `hypomnesis.engine.adapters`. La déclaration ne liste que les modules dans `adapters`.
- Aucun module Python d'adaptateur n'est importé pendant `check` ou le LSP ; les définitions
  statiques ne sont pas évaluées. `hypomnesis layers LANGAGE` exporte le DAG et ses couches.
- `engine/layers.py` partage le plan avec CLI, LSP (overlays transitifs) et Codegen ; les
  configurations I/O et permissions des dépendances ne sont jamais héritées implicitement.

## Génération de programmes (ADR 0012, HYP-146)

- Distribution optionnelle `hypomnesis-codegen` sous `packages/codegen/`, module Python
  `hypomnesis_codegen` : catalogue de prompt, prompting, RAG, Ollama, traduction, banc et graphiques.
- Codegen dépend du moteur ; aucun import inverse, ni dépendance LLM dans le moteur ou son extra
  `dev`. Le compilateur, la documentation structurée, les solveurs, certificats et LSP restent au cœur.
- CLI dédiée `hypomnesis-codegen decrire|benchmark-llm|graphiques-llm` ; anciennes commandes et
  imports `hypomnesis.llm.*` retirés sans alias.
- Installation globale : `pip install -e '.[dev]' -e packages/codegen`. `pytest tests` teste le
  moteur seul ; `pytest packages/codegen/tests` teste Codegen sans appel LLM. Les validateurs
  `rapide` et `complet` couvrent les deux suites et exigent l'installation des deux paquets.

## Conventions

- **Bibliothèques plutôt que code maison** (préférence de l'utilisateur) : utiliser les
  bibliothèques courantes dès qu'elles couvrent le besoin — NetworkX (graphes), NumPy, SciPy,
  scikit-learn, matplotlib, Typer (CLI), le client officiel `ollama`, OpenTelemetry, etc. — tant
  qu'elles restent raisonnables en poids. Ne réimplémenter que ce qui est propre à Hypomnesis
  (langage, typage, IR, sémantique). Le noyau prouvé (Lean) reste sans dépendance.

- Documentation et tickets en **français** ; code, identifiants et commentaires de code en **anglais**
  (sauf les exemples `.hyp` de domaines métiers francophones).
- Python ≥ 3.11, environnement `.venv/` ; Lean 4.35 dans `formal/` (sans Mathlib).
- **Commits réguliers** (demande explicite de l'utilisateur, prioritaire sur la règle par défaut
  d'`INSTRUCTION.md`) : un commit par étape logique terminée et vérifiée, message en français,
  terminé par la ligne `Co-Authored-By` de l'agent.
- **Fusion automatique** (demande de l'utilisateur, 2026-11-03) : après `./scripts/validate.sh complet`
  vert, fusionner la branche de travail dans `main` en avance rapide et pousser. Objectif : itérer
  vite vers un MVP démontrable.
- **Validation à la demande** (aucun hook git) : skill `/valider` ou `./scripts/validate.sh <mode>`
  (`rapide` avant chaque commit, `complet` avant de déclarer une tâche finie ou de pousser, `lean`
  après une modification de `formal/`, `graphe` pour rafraîchir Graphify). Ne jamais contourner
  un validateur (`noqa`, `type: ignore`, test désactivé, `sorry`).
- Les tâches portent un identifiant `HYP-NNN` dans leur titre ; priorité, taille, epic et
  dépendances sont en tête du premier message `### user` de chaque tâche.
- Les métadonnées YAML des tickets et de leurs checklists portent aussi `priority: P0|P1|P2|P3`
  (même priorité que dans le premier message) et `tags: [...]`. Les tags thématiques sont en
  minuscules ASCII avec tirets : `moteur-symbolique`, `metalangage`, `epistemique`, `contrats`,
  `lean`, `llm`, `dsl`, `outillage`, etc. Les checklists reprennent les tags et la priorité
  de leur ticket ; les labels historiques du corps restent conservés.
- Une tâche portant le label `humain` demande une décision de l'utilisateur.
- **Couloirs** `todo → doing → qa → done`. L'agent met une tâche en `doing` quand il la commence
  et en `qa` quand il l'a terminée et validée (`./scripts/validate.sh complet`). Seul l'utilisateur
  passe une tâche de `qa` à `done` après vérification. Une dépendance en `qa` ne bloque plus : on
  peut enchaîner. Une tâche ne peut être `done` que si ses dépendances le sont.
- Tout besoin découvert hors périmètre devient une nouvelle tâche `HYP-NNN`.

## Outils

- Graphe de connaissances : `graphify query|path|explain|affected` sur `graphify-out/` (voir
  `CLAUDE.md`) ; il n'est pas reconstruit automatiquement : `./scripts/validate.sh graphe`.
- Kanban : `.venv/bin/python scripts/kanban.py status` (tâches prêtes ou bloquées, chemin critique vers P0), `check` (validation),
  `graph` (injection dans Graphify ; voir `CLAUDE.md`).
- Sous-agents : `.claude/agents/` (`hyp-planner`, `hyp-implementer`, `hyp-prover`, `hyp-reviewer`), voir `AGENTS.md`.

## Définition de fini (toutes tâches)

- Critères d'acceptation de la tâche satisfaits.
- `./scripts/validate.sh complet` passe (linters, Pyright, schémas, workflows, tests, Lean et
  audit des axiomes).
- Si la Core IR (`src/hypomnesis/ir/core.py`) ou la sémantique de l'interpréteur change : la
  formalisation Lean est mise à jour dans le même changement (`docs/verification/strategie.md`).
- Toute propriété nouvellement prouvée est ajoutée à `docs/verification/proprietes.md` et à
  `formal/Audit.lean`.
- Toute décision structurante fait l'objet d'une ADR dans `docs/adr/`.

## Décisions clés

- ADR 0001 : prototype Python, grammaire Lark LALR(1).
- ADR 0002 : inférence HM sur l'AST, élaboration vers la Core IR ; le runtime n'exécute que la Core IR.
- ADR 0003 : noyau pur ; primitives par `external` liées à un registre natif fermé.
- ADR 0004 : contrats JSON Schema 2020-12, enveloppe indépendante du transport.
- ADR 0005 : provenance épistémique et observabilité distinctes.
- ADR 0006 (proposée) : M3 = théorie des types à deux niveaux, modale et graduée (`docs/architecture/m3-metalangage.md`).
- ADR 0007 : sémantique de référence Lean ; on prouve le vérificateur (certificats), pas le compilateur.

## État (2026-11-03)

- Faits : HYP-001 (fondations), HYP-002 (langage minimal), HYP-003 (preuves Lean initiales).
- Chemin critique vers des garanties sur les vrais programmes : HYP-020 → HYP-024 → HYP-025 → HYP-026 → HYP-027.
- Branche de travail : `phase-0-1-langage-minimal` (non poussée).
