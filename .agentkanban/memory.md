# Mémoire du projet Hypomnesis

## Projet

Métalangage fonctionnel (syntaxe OCaml) pour définir des DSL métiers : connaissances, règles,
contraintes, effets contrôlés. Spécification : `docs/specification/cahier-des-charges-v0.2.md`.
Détails d'implémentation : `TECHNICAL.md`.

## Niveaux d'abstraction (ADR 0008) — règle structurante

- **M3** `src/hypomnesis/` : moteur, métalangage, bibliothèque standard, procédures génériques.
  **Aucun domaine** (test `test_engine_contains_no_domain`).
- **M2** `languages/<langage>/` : langage métier en Hypomnesis (règles, estimateurs, contraintes,
  commandes), contrats, adaptateurs Python vers le monde extérieur seulement, `langage.json`.
- **M1** `programs/<langage>/` : programmes écrits dans un langage M2.
- **M0** `sortie/` : résultats (non versionné).
- Les dépendances ne vont que vers le niveau supérieur. Jamais de logique métier en Python.

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
- Une tâche portant le label `humain` demande une décision de l'utilisateur.
- **Couloirs** `todo → doing → qa → done`. L'agent met une tâche en `doing` quand il la commence
  et en `qa` quand il l'a terminée et validée (`./scripts/validate.sh complet`). Seul l'utilisateur
  passe une tâche de `qa` à `done` après vérification. Une dépendance en `qa` ne bloque plus : on
  peut enchaîner. Une tâche ne peut être `done` que si ses dépendances le sont.
- Tout besoin découvert hors périmètre devient une nouvelle tâche `HYP-NNN`.

## Outils

- Graphe de connaissances : `graphify query|path|explain|affected` sur `graphify-out/` (voir
  `CLAUDE.md`) ; il n'est pas reconstruit automatiquement : `./scripts/validate.sh graphe`.
- Kanban : `python3 scripts/kanban.py status` (tâches prêtes ou bloquées), `check` (validation),
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
