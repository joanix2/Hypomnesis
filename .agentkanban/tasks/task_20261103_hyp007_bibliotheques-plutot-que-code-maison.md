---
title: "HYP-007 · Remplacer le code maison par des bibliothèques courantes"
lane: todo
created: 2026-11-03T21:29:19+01:00
updated: 2026-11-04T16:47:00+01:00
description: "P1 · S · Fondations et gouvernance · coordination des migrations vers des bibliothèques"
priority: P1
tags: [architecture, coordination, dette, outillage, python]
---

## Conversation

### user

**Ticket** HYP-007 · **Priorité** P1 · **Taille** S · **Epic** Fondations et gouvernance · **Dépend de** HYP-006, HYP-008, HYP-009, HYP-014, HYP-015, HYP-016, HYP-017 · **Labels** python, dette, coordination

#### Contexte

Préférence de l'utilisateur, notée dans `memory.md` : utiliser les bibliothèques courantes (NetworkX, NumPy, SciPy, scikit-learn, matplotlib, Typer, clients officiels, OpenTelemetry…) plutôt que du code maison, tant qu'elles restent raisonnables en poids. Seul ce qui est propre à Hypomnesis (langage, typage, IR, sémantique) est écrit à la main ; le noyau Lean reste sans dépendance.

Relevé des endroits concernés :

| Code maison | Remplacement | Fichiers |
|---|---|---|
| graphe de dépendances des faits (prémisses, invalidation en cascade, explication) | **NetworkX** `DiGraph` : `descendants` pour l'invalidation, parcours pour l'explication, export du graphe de provenance | `src/hypomnesis/epistemics/knowledge.py` |
| graphe des tâches du Kanban, détection de cycles, tâches prêtes | **NetworkX** : `simple_cycles`, `topological_generations`, chemin critique | `scripts/kanban.py` |
| client HTTP Ollama écrit avec `urllib` | client officiel **`ollama`** (Python) | `src/hypomnesis/llm/ollama.py` |
| traceur de spans maison | **OpenTelemetry SDK** (exportateur en mémoire pour les rapports, OTLP ensuite ; recoupe HYP-070) | `src/hypomnesis/observability/trace.py` |
| accesseurs de validation des certificats | **jsonschema**, avec le schéma déjà publié | `src/hypomnesis/certify/load.py` |
| CLI `argparse` | **Typer** (ticket dédié HYP-006) | `src/hypomnesis/cli.py` |
| tableaux du banc LLM en texte | **matplotlib** pour les graphiques (exactitude, latence, jetons par modèle) | `src/hypomnesis/llm/benchmark.py` |
| estimateurs par règles | **scikit-learn** quand un vrai modèle appris est voulu (ticket HYP-054) | langages M2 |

#### Découpage

Ce ticket coordonne les migrations ; chacune a son ticket, et celui-ci se termine quand elles le sont :

| Ticket | Migration |
|---|---|
| HYP-006 | CLI : argparse → Typer |
| HYP-008 | graphe de provenance des faits → NetworkX |
| HYP-009 | outil Kanban → NetworkX et PyYAML |
| HYP-014 | client LLM → paquet officiel `ollama` |
| HYP-015 | traceur maison → SDK OpenTelemetry (puis HYP-070) |
| HYP-016 | graphiques du banc LLM → matplotlib |
| HYP-017 | validation des certificats → `jsonschema` (déjà une dépendance) |
| HYP-054 | estimateurs appris → scikit-learn (ticket existant) |

#### Tâches proposées

- Après les migrations : relire `pyproject.toml` (une ligne de justification par dépendance ajoutée) et `TECHNICAL.md`.
- Vérifier qu'aucun autre code d'infrastructure maison ne subsiste ; ouvrir un ticket pour chaque cas trouvé.

#### Critères d'acceptation

- Tous les tests existants passent sans modification de leurs attentes.
- Les propriétés de la provenance (tests `tests/property/`, miroirs des théorèmes Lean) restent vraies.
- Le test d'architecture (aucun domaine dans le moteur) passe toujours.
- `./scripts/validate.sh complet` vert.

#### Fichiers concernés

- `src/hypomnesis/epistemics/knowledge.py`, `src/hypomnesis/llm/ollama.py`, `src/hypomnesis/observability/trace.py`, `src/hypomnesis/llm/benchmark.py`
- `scripts/kanban.py`, `pyproject.toml`, `TECHNICAL.md`

#### Références

- `.agentkanban/memory.md` (préférence « bibliothèques plutôt que code maison »)
- Tickets liés : HYP-006 (Typer), HYP-054 (scikit-learn), HYP-070 (OpenTelemetry)

### agent

**Point d'étape (2026-11-04 14:40).** Lot 0 fait (commit eaa6e55) : dépendances déclarées dans `pyproject.toml`.

| Ticket | Migration | État |
|---|---|---|
| HYP-006 | CLI : argparse → Typer | qa |
| HYP-008 | graphe de provenance → NetworkX | qa |
| HYP-009 | outil Kanban → NetworkX et PyYAML | qa |
| HYP-015 | traceur → SDK OpenTelemetry (façade `Tracer`) | qa |
| HYP-017 | certificats → `jsonschema` | qa |
| HYP-014 | client LLM → paquet `ollama` | doing (reste la validation finale) |
| HYP-016 | graphiques du banc → matplotlib | todo, en cours chez un implémenteur |
| HYP-054 | estimateurs appris → scikit-learn | bloqué (attend HYP-044, HYP-032), hors du périmètre de clôture |

Bug découvert pendant HYP-008 : HYP-143 (fait sans source déclarée `axiome`).

Pour la clôture, l'inventaire du code maison encore présent (avec bibliothèque candidate ou raison de le garder) est dans la checklist `todo_20261103_hyp007_…`, itération 2. Résumé : aucune autre migration ne s'impose ; trois examens restent ouverts (intervalles de confiance du banc avec `scipy.stats`, collecte des commentaires de doc par les callbacks du lexeur Lark, bibliothèque d'automate ou de relance pour HYP-061) et sont rattachés à leurs tickets plutôt qu'à un nouveau ticket.

### user

### agent

**Audit sourcé de coordination (2026-11-04).** Exploration commencée par
`graphify query "HYP-007 migrations Typer NetworkX Ollama OpenTelemetry matplotlib jsonschema infrastructure dependencies pyproject"`,
puis lectures des symboles indiqués par le graphe. Ce rapport complète les états historiques
ci-dessus ; présence du remplacement dans le code ne signifie pas validation humaine du ticket.

#### Sept migrations : fait / reste

Chemins relatifs à `src/hypomnesis/`, sauf indication contraire.

| Ticket | Remplacement vérifié dans la source | État observé / reste |
|---|---|---|
| HYP-006 | `cli.py::app`, commandes annotées, `main` : Typer ; tests `tests/unit/test_cli_contract.py` | `qa` ; pas de nouvelle migration CLI. |
| HYP-008 | `epistemics/knowledge.py::graph`, `retract_source`, `provenance_graph` : `nx.DiGraph`, `nx.descendants`, `nx.node_link_data` ; tests unitaires, propriétés et intégration du graphe | `qa` ; le semi-anneau reste la source de vérité et décide l'invalidation, conformément à ADR 0005/0007. |
| HYP-009 | `scripts/kanban.py::_FrontMatterLoader`, `dependency_graph`, `cycles`, `critical_path` : PyYAML, `nx.simple_cycles`, `nx.dag_longest_path` ; tests `tests/tools/test_kanban.py` | `qa` ; fichier et outillage associés laissés au parent, lecture seule. Pas de parcours de dépendances maison à migrer ici. |
| HYP-014 | `llm/ollama.py::OllamaClient` : import paresseux du client officiel, `chat`, `list`, erreurs ; tests `tests/unit/test_ollama_client.py` et `test_llm.py` | **`doing`, blocage de clôture** : comparaison même modèle/même jeu avant/après non réalisée ; validation finale du sous-ticket à confirmer. Aucun changement de son couloir. |
| HYP-015 | `observability/trace.py::Tracer` : fournisseur privé, `SimpleSpanProcessor`, `InMemorySpanExporter`, fournisseur sans effet ; tests `tests/unit/test_trace.py` | `qa` ; OTLP relève de HYP-070, pas de cette clôture. |
| HYP-016 | `llm/plots.py::render_all`, figures `FigureCanvasAgg` ; `cli.py::graphiques_command` ; tests `tests/unit/test_plots.py` | `qa` ; écarts déjà déclarés dans son rapport : régénération par `graphiques-llm` et non `benchmark-llm --graphiques FICHIER` ; figures de justesse, pas tous les niveaux parsé/typé/exécuté. Audit ≠ acceptation de ces écarts. |
| HYP-017 | `certify/load.py::load_definitions` appelle `SchemaRegistry.issues` une fois avant déconstruction ; `contracts/registry.py` utilise jsonschema/referencing ; tests `tests/unit/test_certificate.py` | `qa` ; seuls les contrôles de portée et de liaison propres au certificat restent en code. |

#### Dépendances

`pyproject.toml` relu intégralement : justification par dépendance directe dans la nouvelle
section « Bibliothèques et infrastructure conservée » de `TECHNICAL.md`, y compris construction,
extras et outillage. **Aucune modification de `pyproject.toml` nécessaire.**
SciPy est déjà explicite dans `llm` et `dev` ; scikit-learn sert déjà au TF-IDF de
`llm/retrieval.py`, indépendamment de l'estimateur appris HYP-054 (hors périmètre).

Versions observées : Typer 0.27.3, NetworkX 3.7, PyYAML 6.0.3, Ollama 0.6.3,
OpenTelemetry API/SDK 1.45.2, matplotlib 3.11.2, jsonschema 4.26.0, SciPy 1.18.1,
scikit-learn 1.9.1, semantic-version 2.10.0, resolvelib 1.2.1.
Ce relevé n'est pas un verrouillage de versions ni un test des versions minimales.

#### Inventaire : bibliothèque ou raison de garder

| Source examinée | Décision |
|---|---|
| `language/docs.py::_doc_index`, `language/parser.py::lex` | **Déjà traité, HYP-137** : lexage Lark, plus de `_DOC` global ; garder `parse_doc`/`_TAG` pour les balises propres au langage. |
| `llm/benchmark.py::wilson`, `llm/plots.py::wilson_interval` | **Déjà traité, HYP-139** : SciPy `binomtest().proportion_ci(method="wilson")` ; garder le tableau Markdown spécifique `summary`. |
| `effects/commands.py::TRANSITIONS`, `may_retry`, `RetryPolicy` ; `effects/dispatcher.py::_execute` | **Garder** : automate pur explicite, délais injectés et interdiction de relance non idempotente (HYP-061/066). `transitions`, `python-statemachine`, `tenacity` ne suppriment pas ces règles ; pas de besoin nouveau justifiant leur poids. |
| `scripts/kanban.py::graph_lock`, `_lock_busy`, `_section_paths`, `_meta` | **Garder** : compatibilité du protocole Graphify `flock`/suppression du fichier et format Markdown borné ; `filelock`/analyseur Markdown complet non justifiés ici. La maintenance HYP-144 reste au parent. |
| `observability/trace.py::Tracer.tree`, `export` | **Garder** : rendus M0 au-dessus du SDK, pas un deuxième traceur ; réexaminer avec HYP-070/OTLP. |
| `cli.py::_repl`, `engine/procedure.py::ProcedureReport.render` | **Garder** : tampon `;;`, rendus spécifiques ; `prompt_toolkit` sans besoin d'édition enrichie serait disproportionné. Rich déjà transitif via Typer. |
| `llm/translation.py::extract_code`, `translate` | **Garder** : extraction des réponses et réparation guidée par les diagnostics, propres au protocole du projet. |
| `languages/mecanique/adaptateurs/transcription.py::transcrire` | **Garder** : adaptateur M2 déterministe ; transcription LLM dans HYP-081, aucune migration métier ici. |
| `llm/retrieval.py::Retriever`, `_normalise` ; `llm/describe.py::_environment` | **Déjà bibliothèques** : scikit-learn/Jinja2 ; normalisation numérique et catalogue spécifiques conservés. |
| `contracts/registry.py::SchemaRegistry` | **Garder** : mince adaptateur jsonschema/referencing, sans validateur structurel concurrent. |
| `engine/bridge.py::to_json`, `runtime/natives.py::to_json_value`, `certify/export.py::export_certificate` | **Garder** : conversions propres aux valeurs et certificat Lean ; les deux ponts JSON délèguent désormais au codec commun `runtime/json.py` (HYP-042). |
| `session.py::run_deep` | **Garder** : pile CPython pour récursion non terminale ; aucune bibliothèque générique ne la remplace ; réexamen possible avec HYP-013. |
| `language/parser.py::_parser`, `_ToAst` | **Déjà bibliothèques** : Lark et `ast.literal_eval` ; transformation AST propre au langage conservée. |
| `language/typesystem/`, `runtime/interpreter.py`, `epistemics/provenance.py`, `ir/core.py` | **Garder** : noyau du projet et miroirs Lean (ADR 0002/0003/0007), pas infrastructure générique. |

Les trois examens autrefois ouverts sont donc résolus pour le besoin actuel : lexage déjà
migré, intervalles déjà migrés, automate conservé avec justification. **Aucun nouveau ticket
de migration retenu**, ni nouvelle bibliothèque, ni nouveau code LLM.
La décision sur l'automate est consignée ici et dans `TECHNICAL.md`, sans modifier HYP-061.

#### Vérifications et critères

Commande ciblée exécutée, sans GPU ni serveur Ollama :

```bash
.venv/bin/python -m pytest tests/unit/test_cli_contract.py tests/unit/test_knowledge_graph.py tests/property tests/integration/test_provenance_graph.py tests/tools/test_kanban.py tests/unit/test_ollama_client.py tests/unit/test_llm.py tests/unit/test_trace.py tests/unit/test_plots.py tests/unit/test_benchmark.py tests/unit/test_certificate.py tests/integration/test_languages.py tests/unit/test_language_docs.py tests/unit/test_commands.py
```

**357 tests réussis en 17,68 s.** Satisfaits sur ce lot : tests des sept migrations,
propriétés de provenance (`tests/property/`), non-interférence des traces, test d'architecture
`test_engine_contains_no_domain`, inventaire et justifications des dépendances.
Aucune attente de test modifiée par cet audit ; aucun changement de Core IR, de sémantique
ou de formalisation nécessaire.

**Restants :** toutes les dépendances en `qa` (HYP-014 ne l'est pas), comparaison réelle
du banc HYP-014, validation complète verte de l'arbre intégré ; les cases de clôture restent
ouvertes. Les états `qa` des autres tickets ne sont pas transformés en validation humaine.
Les modifications préexistantes de tags/priorités et les fichiers réservés au parent sont conservés.
La nouvelle documentation est ajoutée en fin de `TECHNICAL.md`, hors sections Graphe/Kanban.

### user

### agent

**Bilan de l'audit borné.** La tâche n'est **pas clôturée** : HYP-014 reste `doing`,
comparaison réelle du banc avant/après encore à confirmer. Les cases de clôture restent ouvertes.
Le passage initial de HYP-007 en `doing` a provoqué le refus Kanban ; le parent a rétabli
`todo`. Aucun couloir de sous-ticket n'a été changé.

Vérifications supplémentaires effectivement exécutées : `./scripts/validate.sh rapide`
puis `./scripts/validate.sh complet`, toutes étapes vertes sur l'arbre partagé, dont
Kanban (98 tâches), suite Python entière, Lean, audit des axiomes et vérificateur de certificats.
Cela ne remplace ni la comparaison GPU HYP-014 ni la validation du parent après intégration.
Écart opérationnel : ces deux validations ont été relancées au-delà des seuls tests ciblés demandés.

Fichiers de cet audit uniquement : cette fiche, son `todo_` et la section ajoutée en fin de
`TECHNICAL.md`. `pyproject.toml` relu mais inchangé ; mémoire, métier, sources Python, Lean,
graphe et fichiers réservés au parent non modifiés par cet audit.
Commit documentaire : « HYP-007 : documenter l'audit des bibliothèques et ses blocages »
(sans push) ; les modifications préexistantes de métadonnées et les sections du parent
ne font pas partie de ce commit. Aucun travail supplémentaire hors périmètre retenu.

### user

### agent

Bilan intégré des trois tickets demandés : HYP-144 corrigé, avec migration des chemins
synthétiques et rafraîchissements Graphify répétés réussis ; HYP-004 vérifié avec CI
distante verte sur le commit publié et tests locaux du garde-fou exact contre `sorry`
et `admit`. Validation complète finale : 655 tests, linters, Pyright, schémas, Kanban,
Lean et audit des axiomes verts.

HYP-007 dispose maintenant de son audit et des justifications des dépendances, mais
reste bloqué pour clôture par la comparaison réelle avant/après de HYP-014. Cette mesure
LLM n'a pas été lancée sur le Mac, conformément au périmètre de gestion du projet.
Le commit documentaire local `76c19a3` est conservé ; le reste des modifications reste
dans l'arbre de travail, sans push. Tags et priorités antérieurs préservés.

### user
