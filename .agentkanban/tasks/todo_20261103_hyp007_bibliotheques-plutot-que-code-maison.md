---
title: "HYP-007 · TODO"
lane: todo
created: 2026-11-04T15:00:00+01:00
updated: 2026-11-04T16:55:00+01:00
description: "Checklist de coordination de HYP-007 (lot 0, ordre des lots, clôture)"
priority: P1
tags: [architecture, coordination, dette, outillage, python]
---

# Iteration 1

Rôle : ticket de coordination des sept migrations (HYP-006, 008, 009, 014, 015, 016, 017). Il porte le **Lot 0** (dépendances, seul à toucher `pyproject.toml`) et la clôture. Sans GPU.

État des lieux : `pyproject.toml` ne déclare aujourd'hui que `lark`, `jsonschema[format-nongpl]`, `referencing`, `z3-solver` ; extra `llm` = `jinja2`, `scikit-learn` ; extra `dev` = idem + `pytest`, `hypothesis`, `ruff`, `pyright`, `pre-commit`. `.venv` contient PyYAML 6.0.3 (via pre-commit) mais ni typer, rich, networkx, ollama, opentelemetry, matplotlib.

Ordre et lots (fichiers disjoints au sein d'un lot) :
- Lot 0 : dépendances (ce ticket).
- Lot A (parallèle) : HYP-017 (`certify/load.py`), HYP-009 (`scripts/kanban.py`, `validate.sh`, `.pre-commit-config.yaml`), HYP-014 (`llm/ollama.py`).
- Lot B (parallèle, après le Lot 0) : HYP-006 (`cli.py`), HYP-008 (`epistemics/knowledge.py`, `engine/procedure.py` pour l'export du graphe), HYP-015 (`observability/trace.py`, façade, `procedure.py` intact). Les lots A et B peuvent aussi tourner ensemble : aucun fichier commun.
- Lot C (après HYP-006) : HYP-016 (`llm/plots.py` peut être écrit plus tôt ; seule l'option CLI attend).
- Clôture : HYP-007.

Règles pour travailler à plusieurs dans le même arbre : chaque ticket ne `git add` que **ses** fichiers ; `validate.sh rapide` peut échouer à cause du travail en cours d'un autre ticket (utiliser `pytest <ses tests>` et `ruff check <ses fichiers>` entre-temps) ; `complet` se lance une fois par lot, arbre stable ; `TECHNICAL.md` : chaque ticket ne modifie que sa propre ligne ou section. `ruff` interdit `noqa` et `type: ignore`.

- [x] `pyproject.toml`, dépendances d'exécution : `typer>=0.12` (apporte Click et Rich), `networkx>=3.2`, `opentelemetry-api>=1.25`, `opentelemetry-sdk>=1.25`
- [x] `pyproject.toml`, extra `llm` : `ollama>=0.3`, `matplotlib>=3.8` (en plus de `jinja2`, `scikit-learn`)
- [x] `pyproject.toml`, extra `dev` : reprendre `llm` + `pyyaml>=6` (scripts/kanban.py), éventuellement `types-networkx` si Pyright se plaint (jamais `type: ignore`)
- [x] `pip install -e '.[dev]'` dans `.venv` ; noter les versions installées dans la fiche ; vérifier `import typer, networkx, ollama, opentelemetry.sdk.trace, matplotlib, yaml`
- [x] Vérifier que `.github/workflows/ci.yml` (`pip install -e '.[dev]'`) suffit ; sinon l'adapter
- [x] `./scripts/validate.sh rapide` vert avant de lancer les lots ; commit « Dépendances des migrations vers bibliothèques » en français
- [x] Après chaque lot : mettre à jour la colonne « Remplacement » du tableau de la fiche HYP-007 (fait / reste), relire `git status` pour détecter un fichier modifié par deux tickets
- [ ] Clôture : tous les tickets en `qa` ; `./scripts/validate.sh complet` vert sur l'arbre final ; `memory.md` (Outils, Conventions) à jour ; mettre HYP-007 en `qa`

# Iteration 2

État au 2026-11-04 14:40 : HYP-006, 008, 009, 015, 017 en `qa` ; HYP-014 en `doing` (validation finale) ; HYP-016 en cours. HYP-143 (bug de provenance découvert en HYP-008) n'est pas une migration et ne bloque pas la clôture.

Inventaire du code maison encore présent, lu dans le code (`graphify query` puis lecture). Pour chaque ligne : cocher quand la décision est consignée dans la fiche HYP-007 (section « Inventaire »), ou quand le ticket cité a traité le cas.

- [x] `language/docs.py` — expressions régulières `_DOC`/`_TAG` appliquées au texte source pour retrouver `(** … *)`. Candidat : callbacks du lexeur Lark (`lexer_callbacks` sur `COMMENT`, positions exactes). Risque de la regex actuelle : un `(**` à l'intérieur d'une chaîne ou d'un commentaire imbriqué. À examiner avec HYP-137 ; garder `parse_doc` (format de balises propre au projet)
- [x] `llm/benchmark.py` — intervalles de confiance du banc (reste de HYP-139) : ne pas les écrire à la main ; `scipy.stats.binomtest(k, n).proportion_ci(method="wilson")`. SciPy est déjà installé par scikit-learn : ajouter `scipy` explicitement dans l'extra `llm` si utilisé. Le tableau Markdown de `summary()` (≈ 30 lignes) : garder (une bibliothèque de tableaux n'apporte pas assez)
- [x] `effects/dispatcher.py` (+ HYP-061) — automate d'états et relances. Candidats : `transitions` ou `python-statemachine` pour l'automate, `tenacity` pour les relances. Raison probable de garder : la table de transitions doit être lisible et miroir de la preuve Lean (HYP-066), et la règle « jamais de relance d'une commande non idempotente » est de la logique du projet. Décision à consigner dans HYP-061 (une bibliothèque de relance ne se justifie que pour le délai exponentiel)
- [x] `scripts/kanban.py` — verrou `flock` (`graph_lock`, `_lock_busy`) copié du protocole de Graphify : candidat `filelock`, mais le protocole doit rester celui de Graphify (fichier supprimé à la libération) → garder. Analyse des sections Markdown par expressions régulières (`_section_paths`, `_meta`, L96-128) : format maison simple → garder (un analyseur Markdown complet serait disproportionné)
- [x] `observability/trace.py` — reste maison : le rendu `tree()` et le format d'`export()` au-dessus du SDK OpenTelemetry. Garder la façade jusqu'à HYP-070 (export OTLP), puis réexaminer sa suppression
- [x] `cli.py` — boucle `repl` maison (tampon jusqu'à `;;`, Ctrl-D) : candidats `prompt_toolkit` (historique, édition multiligne) ; lourd pour un gain faible → garder, priorité P3. Rendu des rapports (`engine/procedure.py::render`, `kanban.py status`) : Rich est déjà installé par Typer ; mise en forme optionnelle, hors périmètre
- [x] `llm/translation.py` — extraction du code dans la réponse du modèle (`re.findall` des blocs ```, `_PROGRAM_START`) : quelques lignes, spécifique à notre langage → garder. Boucle de réparation : logique du projet
- [x] `languages/mecanique/adaptateurs/transcription.py` — transcription par expressions régulières : adaptateur M2 de remplacement du LLM, remplacé à terme par HYP-081 → garder
- [x] `llm/retrieval.py` (TF-IDF) et `llm/describe.py` (Jinja2) — déjà `scikit-learn` et `jinja2` : rien à faire (le `_normalise` par regex est une règle métier du banc)
- [x] `contracts/registry.py` — mince adaptateur au-dessus de `jsonschema` et `referencing` : garder
- [x] `engine/bridge.py`, `runtime/natives.py::to_json_value`, `certify/export.py` — conversions entre valeurs Hypomnesis et JSON, propres au projet (le certificat est lu par Lean) : garder
- [x] `session.py::run_deep` (fil d'exécution à grande pile et limite de récursion relevée) — contournement de CPython, aucune bibliothèque ne le remplace : garder, noter que seule une évaluation sans récursion Python l'éliminerait (HYP-013)
- [x] `language/parser.py` — Lark déjà utilisé ; `ast.literal_eval` pour les chaînes : bibliothèque standard, garder
- [x] `language/typesystem/` (inférence HM, 893 lignes), `runtime/interpreter.py`, `epistemics/provenance.py` (semi-anneau miroir de Lean), `ir/core.py` : cœur du projet (ADR 0002, 0007), garder
- [x] Reporter le tableau « code maison restant → bibliothèque ou raison de garder » dans la fiche HYP-007 et dans `TECHNICAL.md` ; ouvrir un ticket seulement si une ligne passe de « garder » à « migrer » (aucune aujourd'hui)
- [ ] Clôture finale : `pyproject.toml` relu (une ligne de justification par dépendance), `./scripts/validate.sh complet` vert, mettre HYP-007 en `qa`

# Iteration 3 — audit de coordination du 2026-11-04

Les états et descriptions des itérations précédentes sont historiques. Les cases
d'inventaire cochées signifient « décision sourcée consignée », pas « nouveau code livré ».

- [x] Interroger Graphify avant les lectures de sources ; vérifier les sept migrations par leurs symboles et tests.
- [x] Réconcilier le tableau des lots dans une nouvelle entrée de la fiche ; HYP-014 reste `doing`, les six autres migrations sont `qa`.
- [x] Actualiser l'inventaire : HYP-137 utilise déjà `parser.lex`, qui appelle le lexeur Lark avec `dont_ignore=True` ; HYP-139 utilise déjà SciPy dans le banc **et** les figures ; l'automate HYP-061 est conservé pour ses règles propres.
- [x] Documenter une justification pour chaque dépendance directe de `pyproject.toml`, construction et développement compris, dans `TECHNICAL.md` ; aucune modification des extras nécessaire.
- [x] Reporter les quatorze décisions dans la fiche et `TECHNICAL.md`, sans ajouter de migration LLM ni toucher au métier, au noyau ou à Lean.
- [x] Vérifier les tests ciblés : 357 réussites (CLI, graphes, propriétés, Kanban, client simulé, traces, figures, certificats, architecture, descriptions et commandes).
- [x] Validation rapide et complète de l'arbre partagé : Ruff, Kanban (98 tâches), tests, pre-commit, Lean, audit des axiomes et certificat verts.
- [ ] Clôture coordonnée : HYP-014 validé et en `qa` ; comparaison réelle du banc avant/après par l'utilisateur.
- [ ] Confirmer la validation finale après intégration du parent ; les deux cases de clôture historiques restent ouvertes tant que HYP-014 n'est pas validé.
