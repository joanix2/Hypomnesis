# Tableau Kanban — Hypomnesis

> Fichier généré par `python kanban/board.py` : ne pas éditer à la main.
> Conventions et protocole agent : [README.md](README.md).

**En cours** : 0 · **En revue** : 0 · **Prêt (dépendances satisfaites)** : 13 · **Bloqué (dépendances en attente)** : 54 · **Terminé** : 3

## En cours

_Aucun ticket._

## En revue

_Aucun ticket._

## Prêt (dépendances satisfaites)

| Ticket | Titre | Prio | Taille | Epic | Dépend de | Labels |
|---|---|---|---|---|---|---|
| [HYP-004](tickets/HYP-004-pousser-et-valider-ci.md) | Pousser la branche et valider la CI (Python et preuves) | P0 | S | FONDATIONS | HYP-003 | humain, ci |
| [HYP-020](tickets/HYP-020-lean-variants-et-match.md) | Lean F1a : variants et `match` général | P0 | L | FORMEL | HYP-003 | lean |
| [HYP-024](tickets/HYP-024-annoter-elaboration.md) | Pont F3a : annoter l'élaboration avec les types inférés | P0 | M | FORMEL | HYP-002 | python |
| [HYP-030](tickets/HYP-030-modele-connaissances.md) | Modèle de données des connaissances | P0 | M | P2-EPISTEMIQUE | HYP-002 | python |
| [HYP-040](tickets/HYP-040-interfaces-capacites.md) | Interfaces des capacités (Observer … Resolver) | P0 | M | P3-EXTENSIONS | HYP-002 | python |
| [HYP-051](tickets/HYP-051-problem-ir.md) | Problem IR : variables, domaines, contraintes, objectifs | P0 | M | P4-RAISONNEMENT | HYP-002 | python |
| [HYP-060](tickets/HYP-060-effect-ir-effets-algebriques.md) | Effect IR et effets algébriques | P0 | L | P5-EFFETS | HYP-002 | python |
| [HYP-005](tickets/HYP-005-amender-cahier-des-charges-v0-3.md) | Amender le cahier des charges en v0.3 | P1 | S | FONDATIONS | HYP-003 | humain, doc |
| [HYP-010](tickets/HYP-010-exhaustivite-filtrage.md) | Vérifier l'exhaustivité et la redondance du filtrage | P1 | M | LANG | HYP-002 | python |
| [HYP-012](tickets/HYP-012-signatures-de-modules.md) | Signatures de modules (`module type`, contrainte `M : S`) | P1 | L | LANG | HYP-002 | python |
| [HYP-011](tickets/HYP-011-import-entre-fichiers.md) | Import entre fichiers | P2 | M | LANG | HYP-002 | python |
| [HYP-056](tickets/HYP-056-types-dimensionnels.md) | Types dimensionnels (unification modulo groupe abélien) | P2 | L | P4-RAISONNEMENT | HYP-002 | python |
| [HYP-013](tickets/HYP-013-performance-interpreteur.md) | Benchmarks et performance de l'interpréteur | P3 | M | LANG | HYP-002 | python, perf |

## Bloqué (dépendances en attente)

| Ticket | Titre | Prio | Taille | Epic | Dépend de | Labels |
|---|---|---|---|---|---|---|
| [HYP-025](tickets/HYP-025-certificat-json.md) | Pont F3b : schéma et export JSON du certificat | P0 | M | FORMEL | **HYP-024** | python, contrats |
| [HYP-026](tickets/HYP-026-verificateur-lean-executable.md) | Pont F3c : exécutable Lean `hypomnesis-check` | P0 | M | FORMEL | **HYP-025**, **HYP-020** | lean |
| [HYP-027](tickets/HYP-027-certify-cli-et-ci.md) | Pont F3d : `hypomnesis check --certify` et certification en CI | P0 | S | FORMEL | **HYP-026**, **HYP-004** | python, ci |
| [HYP-031](tickets/HYP-031-provenance-semi-anneau.md) | Provenance en semi-anneau (implémentation Python) | P0 | M | P2-EPISTEMIQUE | **HYP-030** | python |
| [HYP-033](tickets/HYP-033-revision-et-journal.md) | Révision des connaissances et journal d'événements | P0 | M | P2-EPISTEMIQUE | **HYP-031** | python |
| [HYP-041](tickets/HYP-041-registre-capacites.md) | Registre de capacités et manifestes | P0 | M | P3-EXTENSIONS | **HYP-040** | python, contrats |
| [HYP-042](tickets/HYP-042-types-vers-json-schema.md) | Correspondance types Hypomnesis ↔ JSON Schema | P0 | L | P3-EXTENSIONS | **HYP-041** | python, contrats |
| [HYP-044](tickets/HYP-044-backend-python.md) | Adaptateur de backend Python générique | P0 | M | P3-EXTENSIONS | **HYP-041**, **HYP-042** | python |
| [HYP-050](tickets/HYP-050-moteur-de-regles.md) | Moteur de règles avec provenance | P0 | L | P4-RAISONNEMENT | **HYP-031**, **HYP-038** | python |
| [HYP-052](tickets/HYP-052-backend-z3.md) | Backend Z3 depuis la Problem IR | P0 | M | P4-RAISONNEMENT | **HYP-051**, **HYP-044** | python |
| [HYP-054](tickets/HYP-054-estimateur-sklearn.md) | Estimateur scikit-learn (épaisseur de plaque) | P0 | M | P4-RAISONNEMENT | **HYP-044**, **HYP-032** | python |
| [HYP-061](tickets/HYP-061-automate-commandes.md) | Automate d'états des commandes, délais, relances | P0 | M | P5-EFFETS | **HYP-060** | python |
| [HYP-062](tickets/HYP-062-pipeline-validation-effets.md) | Permissions et pipeline de validation des effets | P0 | M | P5-EFFETS | **HYP-061**, **HYP-042** | python |
| [HYP-063](tickets/HYP-063-transport-et-peripheriques-simules.md) | Transport JSON par fichiers et périphériques simulés | P0 | M | P5-EFFETS | **HYP-062** | python |
| [HYP-064](tickets/HYP-064-trois-modes-execution.md) | Modes simulation, dry-run et production comme handlers | P0 | M | P5-EFFETS | **HYP-060**, **HYP-063** | python |
| [HYP-065](tickets/HYP-065-lean-validation-avant-dispatch.md) | Lean F5a : validation et autorisation avant tout dispatch | P0 | L | FORMEL | **HYP-062** | lean |
| [HYP-066](tickets/HYP-066-lean-au-plus-une-execution.md) | Lean F5b : au plus une exécution des commandes non idempotentes | P0 | L | FORMEL | **HYP-061** | lean |
| [HYP-068](tickets/HYP-068-scenario-capteur-actionneur.md) | Scénario MVP secondaire : température → ventilateur | P0 | M | P5-EFFETS | **HYP-063**, **HYP-050** | python, exemple |
| [HYP-090](tickets/HYP-090-scenario-mvp-mecanique.md) | Scénario MVP principal : plaque de bout en bout | P0 | L | P8-STABILISATION | **HYP-054**, **HYP-052**, **HYP-055**, **HYP-063**, **HYP-082** | python, exemple |
| [HYP-021](tickets/HYP-021-lean-records.md) | Lean F1b : records et mise à jour fonctionnelle | P1 | M | FORMEL | **HYP-020** | lean |
| [HYP-022](tickets/HYP-022-lean-exhaustivite.md) | Lean F1c : un `match` exhaustif ne lève jamais `Match_failure` | P1 | M | FORMEL | **HYP-020**, **HYP-010** | lean |
| [HYP-023](tickets/HYP-023-lean-polymorphisme.md) | Lean F2 : polymorphisme dans les termes élaborés | P1 | L | FORMEL | **HYP-020** | lean |
| [HYP-028](tickets/HYP-028-tests-differentiels.md) | Tests différentiels interpréteur Python ↔ sémantique Lean | P1 | M | FORMEL | **HYP-026** | python, lean, tests |
| [HYP-032](tickets/HYP-032-metavariables.md) | Métavariables : inconnues explicites et contraintes | P1 | M | P2-EPISTEMIQUE | **HYP-030** | python |
| [HYP-034](tickets/HYP-034-persistance-sqlite.md) | Persistance SQLite et import/export JSON | P1 | M | P2-EPISTEMIQUE | **HYP-033** | python |
| [HYP-035](tickets/HYP-035-detection-conflits.md) | Détection et signalement des conflits | P1 | M | P2-EPISTEMIQUE | **HYP-033** | python |
| [HYP-036](tickets/HYP-036-lean-revision-incrementale.md) | Lean F4a : révision incrémentale = recalcul complet | P1 | L | FORMEL | **HYP-033**, HYP-003 | lean |
| [HYP-038](tickets/HYP-038-connaissances-dans-le-langage.md) | Exposer les connaissances dans le langage | P1 | M | P2-EPISTEMIQUE | **HYP-030**, **HYP-033** | python |
| [HYP-043](tickets/HYP-043-lean-aller-retour-json.md) | Lean F5d : aller-retour JSON et conformité au schéma | P1 | L | FORMEL | **HYP-042**, **HYP-021** | lean |
| [HYP-045](tickets/HYP-045-demo-substitution-plugins.md) | Démonstration : deux plugins derrière la même interface | P1 | S | P3-EXTENSIONS | **HYP-044** | python, exemple |
| [HYP-046](tickets/HYP-046-theories-style-gat.md) | Théories : signatures avec lois, modèles et tests de lois | P1 | L | M3 | **HYP-012** | python |
| [HYP-053](tickets/HYP-053-verificateur-certificats-solveur.md) | Vérificateur de certificats de solveur (+ preuve Lean) | P1 | M | P4-RAISONNEMENT | **HYP-052** | python, lean |
| [HYP-055](tickets/HYP-055-validateurs-contre-exemples.md) | Validateurs et contre-exemples | P1 | M | P4-RAISONNEMENT | **HYP-052** | python |
| [HYP-067](tickets/HYP-067-lean-modes-execution.md) | Lean F5c : dry-run sans dispatch, même terme dans les trois modes | P1 | M | FORMEL | **HYP-064**, **HYP-065** | lean |
| [HYP-070](tickets/HYP-070-instrumentation-otel.md) | Instrumentation OpenTelemetry (traces) | P1 | M | P6-OBSERVABILITE | **HYP-044** | python, observabilité |
| [HYP-071](tickets/HYP-071-metriques.md) | Métriques du §12.4 | P1 | M | P6-OBSERVABILITE | **HYP-070** | python, observabilité |
| [HYP-072](tickets/HYP-072-logs-structures.md) | Logs structurés corrélés et expurgation | P1 | S | P6-OBSERVABILITE | **HYP-070** | python, observabilité |
| [HYP-073](tickets/HYP-073-stack-observabilite.md) | Stack Collector, Prometheus, Grafana, Tempo | P1 | M | P6-OBSERVABILITE | **HYP-071** | infra, observabilité |
| [HYP-080](tickets/HYP-080-description-dsl-pour-llm.md) | Publication des DSL pour les LLM | P1 | M | P7-LLM | **HYP-041** | python, llm |
| [HYP-081](tickets/HYP-081-transcription-llm.md) | Transcription langage naturel → programme Hypomnesis | P1 | L | P7-LLM | **HYP-080** | python, llm |
| [HYP-082](tickets/HYP-082-grade-hypothese-et-manques.md) | Sorties LLM au grade `Hypothesis` et détection des manques | P1 | M | P7-LLM | **HYP-081**, **HYP-032** | python, llm |
| [HYP-093](tickets/HYP-093-revue-criteres-acceptation.md) | Revue des critères d'acceptation du MVP | P1 | S | P8-STABILISATION | **HYP-090**, **HYP-027**, **HYP-065** | humain, doc |
| [HYP-037](tickets/HYP-037-lean-pas-de-faux-conflit.md) | Lean F4b : pas de faux conflit | P2 | M | FORMEL | **HYP-035**, **HYP-036** | lean |
| [HYP-057](tickets/HYP-057-lean-dimensions.md) | Lean F6 : cohérence dimensionnelle et invariance d'échelle | P2 | L | FORMEL | **HYP-056**, **HYP-023** | lean |
| [HYP-074](tickets/HYP-074-dashboards.md) | Tableaux de bord Runtime, Plugins, Epistemic, Actuators | P2 | M | P6-OBSERVABILITE | **HYP-073**, **HYP-033**, **HYP-063** | infra, observabilité |
| [HYP-083](tickets/HYP-083-evaluation-demandes-ambigues.md) | Jeu d'évaluation de demandes ambiguës | P2 | M | P7-LLM | **HYP-081** | llm, tests |
| [HYP-084](tickets/HYP-084-explicabilite.md) | Explicabilité : reformuler ce qui a été compris et fait | P2 | M | P7-LLM | **HYP-081**, **HYP-031** | python, llm |
| [HYP-091](tickets/HYP-091-benchmarks.md) | Benchmarks de bout en bout | P2 | M | P8-STABILISATION | **HYP-090** | perf |
| [HYP-092](tickets/HYP-092-doc-creation-domaine-sdk.md) | Documentation de création de domaine et SDK expérimental | P2 | M | P8-STABILISATION | **HYP-090**, **HYP-046** | doc |
| [HYP-100](tickets/HYP-100-modalite-graduee.md) | Modalité graduée `[g]` dans le typeur | P2 | L | M3 | **HYP-031** | python |
| [HYP-075](tickets/HYP-075-lean-non-interference-telemetrie.md) | Lean : la télémétrie n'influe pas sur les résultats | P3 | M | FORMEL | **HYP-070**, **HYP-036** | lean |
| [HYP-101](tickets/HYP-101-staging-type-frontiere-llm.md) | Code typé `⇑A` pour la frontière LLM | P3 | L | M3 | **HYP-081**, **HYP-012** | python |
| [HYP-102](tickets/HYP-102-prototype-niveau-meta.md) | Prototype du niveau méta (λΠ-modulo, `Desc`) en Lean | P3 | L | M3 | **HYP-023**, **HYP-005** | lean, recherche |
| [HYP-103](tickets/HYP-103-lean-modeles-de-theories.md) | Lean F7 : modèles de théories et substituabilité | P3 | L | FORMEL | **HYP-046**, **HYP-102** | lean, recherche |

## Terminé

| Ticket | Titre | Prio | Taille | Epic | Dépend de | Labels |
|---|---|---|---|---|---|---|
| [HYP-001](tickets/HYP-001-phase-0-fondations.md) | Phase 0 : fondations du dépôt | P0 | M | FONDATIONS | — | python, doc |
| [HYP-002](tickets/HYP-002-phase-1-langage-minimal.md) | Phase 1 : langage minimal (parser, HM, interpréteur) | P0 | L | LANG | HYP-001 | python |
| [HYP-003](tickets/HYP-003-lean-fragment-et-premieres-preuves.md) | Sémantique de référence Lean et premières preuves | P0 | L | FORMEL | HYP-002 | lean |

## Par epic

| Epic | Terminés | Total |
|---|---|---|
| Fondations et gouvernance | 1 | 3 |
| Langage | 1 | 5 |
| Vérification formelle (Lean) | 1 | 19 |
| Phase 2 — Moteur épistémique | 0 | 7 |
| Phase 3 — Extensions et contrats | 0 | 5 |
| Phase 4 — Raisonnement hybride | 0 | 7 |
| Phase 5 — Effets et actionneurs | 0 | 6 |
| Phase 6 — Observabilité | 0 | 5 |
| Phase 7 — Intégration LLM | 0 | 5 |
| Phase 8 — Stabilisation | 0 | 4 |
| Niveau M3 (méta-métamodèle) | 0 | 4 |
