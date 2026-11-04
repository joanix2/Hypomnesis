# Hypomnesis — document technique

Référence d'implémentation pour les agents et les humains. Les décisions sont dans
`docs/adr/`, la vision dans `docs/specification/`, l'avancement dans `.agentkanban/tasks/`.

La [v0.3 du cahier des charges](docs/specification/cahier-des-charges-v0.3.md)
est la référence depuis l'arbitrage humain HYP-005 : OBJ-11, ses cinq critères
formels et les trois axes épistémiques sont adoptés comme cibles.
La v0.2 est conservée intacte ; l'ADR 0006 reste proposée pour expérimentation,
sans engagement sur toute son architecture. L'adoption n'ajoute aucune
garantie Lean au runtime existant.

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
| CLI | `src/hypomnesis/cli.py` | application Typer (Rich) : `run`, `check`, `repl`, `plugins list\|show`, `lancer`, `--version` ; `main(argv) -> int` convertit la sortie Click en entier (voir « CLI ») |

### Génération optionnelle, hors du noyau (HYP-146, ADR 0012)

`packages/codegen/` construit la distribution `hypomnesis-codegen` et le module
`hypomnesis_codegen`. Elle dépend du moteur (`hypomnesis>=0.1.0,<0.2`), jamais l'inverse.
Elle contient catalogue de prompt, prompting, RAG, client Ollama, traduction/réparation,
benchmarks et graphiques ; ses ressources Jinja2 sont incluses dans sa roue.
Dans la suite de ce document, `codegen/` abrège `packages/codegen/src/hypomnesis_codegen/`.

Installation des deux paquets depuis la racine :
`pip install -e '.[dev]' -e packages/codegen`. Le moteur et son extra `dev` ne déclarent
aucune dépendance LLM. Les commandes extraites sont
`hypomnesis-codegen decrire|benchmark-llm|graphiques-llm` et les imports
`hypomnesis_codegen.*`, sans alias dans l'ancienne CLI ou l'ancien module.
`pytest tests` teste le cœur ; `pytest packages/codegen/tests` teste Codegen sans modèle.
Les validateurs `rapide` et `complet` exécutent les deux suites, et Pyright couvre les deux
sources. Un job CI distinct installe seulement le moteur et teste son indépendance.
Les types, descriptions structurées, IR, solveurs, certificats et LSP restent dans le cœur.

## Moteur, langages, procédures (ADR 0008, HYP-060)

`src/hypomnesis/engine/` (M3) charge un langage M2 et exécute la procédure d'un programme M1 :

| Module | Rôle |
|---|---|
| `engine/language.py` | chargement d'une couche déclarée en `.hyp`, vérification statique ou évaluation explicite, contrats propres au langage |
| `engine/layers.py` | résolution du DAG d'imports locaux, vérification des fermetures, déduplication et export topologique |
| `engine/adapters.py` | décorateurs Python et registre I/O propre au langage, chargé seulement à l'exécution |
| `engine/procedure.py` | **interpréteur d'effets** : exécute une valeur `'a Effect.t` (observer, agir, résoudre, enregistrer, retirer, noter), borné en nombre d'étapes |
| `engine/bridge.py` | valeur Hypomnesis → JSON ; `Problem.problem` → Problem IR |
| `engine/registry.py` | registre statique de manifestes d'extensions et résolution SemVer, sans chargement de backend |

Bibliothèque standard (prélude, M3) : `Json.t`, `to_json` (primitive pure), `Problem`,
`Effect` (`'a Effect.t`, `return`, `bind`, `observe`, `act`, `solve`, `record`, `retract`,
`note`) et l'opérateur `>>=`. `m >>= fun x -> e` est accepté par la grammaire. Le support
`Effect.Given | Estimated c | Assumed c | Derived prémisses` qualifie ce qu'un programme
enregistre ; seul le moteur crée des faits observés, lors d'une lecture de capteur.

Briques M3 utilisées par l'interpréteur : `epistemics/` (provenance, connaissances),
`ir/problem.py`, `backends/z3_solver.py`, `effects/dispatcher.py`, `observability/trace.py`.

### Déclarations natives et couches (HYP-147, ADR 0013)

Le fichier d'entrée `.hyp`, par convention `langage.hyp`, commence par
`language nom = { version = "..."; imports = ["../base"]; … }`.
`LanguageItem` dans l'AST porte des données statiques, lues par les règles `config_*`
de Lark (pas par regex ni évaluation du langage). Le schéma interne
`language-declaration/1.0.0` vérifie les champs et la configuration de procédure ;
il ne décrit plus un manifeste utilisateur JSON. `langage.json` n'est plus accepté.
La propriété Python `Language.manifest` conserve l'objet de configuration normalisé
pour ses consommateurs existants, sans lire de fichier JSON.

`resolve_layers` renvoie un `LayerPlan` : entrées canoniques, sources avec AST et
positions d'origine, graphe NetworkX **dépendance → utilisateur**. Les imports de
dossiers visent `langage.hyp` ; les imports de fichiers `.hyp` sont explicites. Le corps
de l'entrée précède ses fichiers `sources`. Les diamants sont dédupliqués ; cycles,
identités dupliquées et collisions d'exports entre paquets sont refusés.
Les chemins de sources/contrats/exemples/adaptateurs sont confinés au paquet,
imports relatifs vers des paquets voisins autorisés. Ni registre distant, ni
contraintes de versions ou renommage d'import dans cette première version.

`check_layers` vérifie chaque couche dans la fermeture de ses propres imports
pour interdire les dépendances accidentelles entre branches. Les sessions statiques
ne chargent même pas les valeurs du prélude ; sa frontière de certificat est conservée.
`load_language(..., execute=False)` utilise cette session sans exécuter les définitions ;
`execute=True` (défaut pour l'API d'exécution) charge ensuite une seule fois les AST
résolus dans une session d'exécution fraîche. La Core IR et le runtime sont inchangés.
`SourceError` conserve source, chemin et étendue pour les erreurs des dépendances.
Les bibliothèques peuvent omettre `procedure`, mais ne peuvent alors pas être lancées.

Les modules I/O sont listés dans `adapters`, sans nom de fonction ni scan implicite.
Ils portent `@sensor("id")`, `@actuator("id")`, `@environment` et `@transcriber` :
lecteur `(env, id) -> enveloppe`, fabrique `env -> Actuator`, constructeur
`(options, out_dir) -> env`, transcription `demande -> programme M1`.
Les signatures incompatibles, duplications et fonctions asynchrones sont refusées.
Sans environnement, une fabrique d'actionneur reçoit `out_dir`.
Ni la résolution, ni `check`, ni le LSP n'importent ces modules. Les configurations
I/O, contrats et permissions des dépendances ne sont pas héritées implicitement.
Le dispatcher reste responsable de valider, autoriser et exécuter les effets.

`hypomnesis layers LANGAGE` publie `LayerPlan.to_json()` (version 1.0.0), ses nœuds,
arêtes orientées et générations topologiques, sans évaluation. `check langage.hyp`
reconnaît la déclaration ; `check programme.hyp --langage LANGAGE` vérifie dans
le même contexte sans exécution. Le catalogue et les prompts Codegen parcourent
`Language.plan.source_files()` et incluent les définitions transitives une seule fois.
Les exemples `booleen`, `arithmetique`, `contraintes`, `composition_a` et
`composition_b` illustrent ce partage. Tests : `test_language_layers.py`,
`test_adapter_decorators.py`, protocole LSP et catalogue Codegen.

### Épistémique : graphe de provenance (NetworkX, HYP-008)

HYP-030 complète les instantanés existants : `Fact` capture récursivement les
valeurs dans un arbre immuable et renvoie des conteneurs détachés ; `Source`
et `Unknown` valident leurs métadonnées. `Observation` lie explicitement un
fait observé et sa source. Les signatures de la base restent inchangées.
`epistemics/serialization.py` échange ces trois formes selon
`contracts/schemas/knowledge-1.0.0.json`, en réutilisant `TypeCodec` et le
type fermé attendu par l'hôte pour la valeur. Ni grade déclaré ni valeur
sentinelle pour une inconnue. Ce n'est pas l'export/rejeu complet d'une base.
Guide et limites : [connaissances.md](docs/architecture/connaissances.md).

La **source de vérité** reste le terme de provenance en semi-anneau de chaque fait
(`epistemics/provenance.py`, miroir du modèle Lean) : support, confiance et « tient-il encore ? »
en sont des évaluations. `KnowledgeBase.graph()` en dérive, à la demande, un `nx.DiGraph` :

- nœuds `fact:<clé>` et `source:<id>` (préfixes : une clé de fait peut ressembler à un id de
  source) ; `source:axiome` est déclarée dès qu'un fait est dérivé sans prémisse (voir plus bas) ;
- arêtes `source → fait` (la provenance du fait la mentionne, `kind="provenance"`) et
  `prémisse → conclusion` (`kind="premise"`) ; `graph(detailed=True)` ajoute valeur, méthode,
  support et confiance (nœuds faits), origine et confiance (nœuds sources).

Usages : depuis HYP-033, `retract_source` prend pour **ensemble candidat** l'index
inverse observation → faits (`epistemics/revision.py`), puis **décide par l'évaluation booléenne** de chaque
candidat (substitution `x ↦ 0`, P10/P11) — un fait à deux dérivations (`plus`) survit si l'une tient
encore ; `explain` parcourt les prédécesseurs `premise` (même rendu texte qu'avant) ;
`provenance_graph()` exporte le graphe en JSON node-link (`nx.node_link_data(…, edges="edges")`,
rechargeable par `nx.node_link_graph`), inclus par `ProcedureReport.to_json` sous la clé
`provenance_graph`. Tests : `tests/unit/test_knowledge_graph.py`,
`tests/property/test_knowledge_graph.py` (Hypothesis), `tests/integration/test_provenance_graph.py`
(caractérisation).

HYP-031 ajoute `COST`, la lecture tropicale non négative (`min`, `+`, `inf`, `0`),
et les propriétés générées correspondant aux quatre théorèmes Lean.
HYP-033 protège le journal : tuple d'événements gelés avec instantanés des
faits remplacés/invalidés. `replace_observation` retire explicitement l'ancienne
source et laisse les conclusions invalidées inconnues jusqu'à nouvelle
dérivation ; aucun libellé de méthode n'est exécuté comme du code. Les
alternatives survivantes recalculent support et confiance sans sources retirées.

Limites connues : re-dériver une clé à partir d'une conclusion qui dépend d'elle crée un cycle de
prémisses au niveau des clés ; `explain` le refuse (`ValueError`) au lieu de récurser sans fin, la
révision reste correcte (elle se fonde sur les provenances). Deux prémisses identiques dans une
même dérivation n'apparaissent qu'une fois dans l'explication.

Fait sans prémisse (HYP-143, option A) : `derive(k, v, m, [])` est une *constante du programme*. Sa
provenance est `obs("axiome")`, et la source `axiome` (`AXIOM`) est **déclarée** à la première
utilisation : type `default`, support « par défaut » (`Defaulted`), confiance 1,0, origine
« constante du programme ». `support`, `confidence`, `explain`, `to_json` et le graphe fonctionnent
donc sur ce fait (avant : `KeyError: 'axiome'`). `retract_source("axiome", …)` est refusé
(`ValueError`) : la source n'est jamais rétractée, et `_holds` ne dit plus « faux » pour une source
inconnue (avant : tout fait sans prémisse était invalidé par la première rétractation, même sans
lien). Cohérent avec P10/P11 : un fait dont la provenance ne mentionne pas la source retirée est
inchangé. Un fait mêlant `axiome` et une observation suit l'observation (produit : le plus faible
l'emporte ; le retrait de l'observation l'invalide).

CLI : `hypomnesis lancer LANGAGE [PROGRAMME] [--demande …] [--mode …] [--env cle=valeur]
[--sortie DIR] [--sans-permission]`.

### CLI (Typer, HYP-006)

`cli.py` déclare une fonction annotée par commande sur `app = typer.Typer(...)` (typer 0.27 : Click
embarqué, aide rendue par Rich). Les options gardent leurs noms et défauts d'avant la migration ;
`--mode` est l'énumération `Mode` (`simulate`, `dry-run`, `production`), `--format` l'énumération
`CheckFormat` (`text`, `json`), `--env` une liste répétable. Les imports lourds (`certify`, `engine`)
restent dans les fonctions pour que `check` démarre vite. La CLI séparée Codegen possède
son propre `Format` (`md`, `json`).

Codes de sortie : 0 succès ; 1 refus applicatif (erreur positionnée, `refusé : …` pour
`lancer`, ou `decrire` dans Codegen) ; 64 `lancer` sans programme ni demande ; 2 erreur d'usage détectée par Click
(option inconnue, `--mode` invalide, fichier `.hyp` de `run`/`check`/`lancer` ou dossier de
`benchmark-llm` absent — refusés avant tout chargement). Le dossier `LANGAGE` de `lancer`/`decrire`
n'est volontairement **pas** vérifié par Click : son absence est refusée par le code (`LanguageError`,
code 1). `main(argv) -> int` appelle `app` en mode autonome et convertit le `SystemExit` en entier
retourné : les tests l'appellent directement, le point d'entrée `hypomnesis` fait
`sys.exit(main())`.

### Diagnostics structurés (HYP-130)

`hypomnesis check FICHIERS --format json [--langage DOSSIER]` imprime sur la sortie standard un
document `diagnostics/1.0.0` (`contracts/schemas/diagnostics-1.0.0.json`, constantes
`DIAGNOSTICS_SCHEMA_ID`/`DIAGNOSTICS_VERSION` dans `language/errors.py`) et rien d'autre ; la sortie
texte (défaut `--format text`) et les codes de sortie (0/1) sont inchangés. Le compilateur s'arrête à
la première erreur : le tableau `diagnostics` contient donc 0 ou 1 entrée (le schéma admet plus, pour
les avertissements de HYP-010, gravité `warning`).

`HypomnesisError.to_diagnostic(filename)` produit une entrée : `stage` (identifiant stable
`stage_id` : `syntax`, `name`, `type`, `runtime`, ou `error` pour toute sous-classe qui ne le
redéfinit pas — le libellé affiché reste `stage`), `severity`, `message`, `file`, et `line`,
`column`, `end_line`, `end_column` (1-based, fin exclusive, `null` si l'erreur n'a pas d'étendue).
`--langage DOSSIER` charge le langage M2 (`load_language`) et vérifie les fichiers dans sa session ;
un dossier sans `langage.hyp` est refusé (`refusé : …`, code 1).

Précision des étendues (fin approximée ou large) : une erreur de **syntaxe** n'a que son début
(`parser._convert_error` : fin = début + 1 colonne) ; un **champ inconnu** (`infer._check_fields`)
est positionné sur l'expression enregistrement entière, faute d'étendue du nom de champ dans l'AST.
Les erreurs de nommage et de typage portent l'étendue de l'expression fautive.
Consommateurs : linter VS Code (HYP-132) et CLI pour agents (HYP-133).

### Banc LLM : graphiques (HYP-016)

`packages/codegen/src/hypomnesis_codegen/plots.py` (matplotlib, paquet Codegen) lit un `resultats-*.json` de `benchmark-llm` et
trace trois figures, chacune en PNG et SVG (`<stem>-justesse`, `<stem>-justesse-par-jeu`, `<stem>-cout`) :
justesse au premier essai et après réparations par modèle/stratégie, puis par jeu (dev/test/hard), avec
intervalles de Wilson à 95 % ; temps et jetons générés par cas (moyenne ± erreur standard). Trois
couches testables séparément : `load_results`/`normalize` (tolère les anciens lots : sans `strategy`,
`split` ni `correct_first`, on suppose stratégie par défaut, jeu `dev`, et « juste au premier essai » =
juste avec au plus une tentative), fonctions de séries pures (`accuracy_by_label`, `accuracy_by_split`,
`cost_by_label`, `wilson_interval`), figures (`Figure` + `FigureCanvasAgg`, jamais `pyplot` : aucun
affichage, aucun état global). Le texte SVG reste du texte (`svg.fonttype = none`).

CLI : `hypomnesis-codegen benchmark-llm … [--graphiques/--sans-graphiques]` (actif par défaut ;
matplotlib est une dépendance du paquet) écrit les figures à côté du résumé ; `hypomnesis-codegen graphiques-llm
FICHIER.json [--sortie DIR]` les régénère sans relancer le banc ni appeler Ollama.

### Banc LLM : intervalles, temps hors chargement, répétitions (HYP-139)

- **Intervalles de Wilson** : `benchmark.wilson(k, n)` et `plots.wilson_interval` s'appuient sur
  `scipy.stats.binomtest(k, n).proportion_ci(method="wilson")` (paquet Codegen). `summary()` les
  affiche à 95 % pour « Correct (1er essai) » et « Correct ». Le tableau distingue aussi parsé, typé
  (1er essai / après réparations), exécuté, **cas réparés** (plus d'une tentative), et deux temps :
  « Temps moy. » (total) et « Temps moy. hors chargement » (total − `Reply.load_seconds`).
- **JSON de résultats** : `seconds`, `load_seconds`, `seconds_without_load`, `repetition`, `temperature`
  s'ajoutent à chaque ligne ; `plots.normalize` tolère les anciens lots (aucun chargement soustrait). La
  figure de coût trace les deux temps côte à côte.
- **Répétitions** (bibliothèque seulement) : `run_benchmark(..., repetitions=N, temperature=T)` et
  `run_case(..., temperature=, repetition=)`, `translate(..., temperature=)`,
  `OllamaClient.chat(..., temperature=)`. À température 0 les essais sont identiques : avec `N > 1` la
  température par défaut est `REPEAT_TEMPERATURE` (0,7). Chaque essai est une ligne de résultat ; les
  intervalles supposent des essais indépendants, d'où un second tableau (`repetition_table`) : correct au
  1er essai moyen par cas et nombre de cas « stables » (même issue à chaque essai).
- Option CLI `--repetitions`/`--temperature` : pas encore branchée dans `codegen/cli.py`.
## Certificats

`src/hypomnesis/certify/` exporte la Core IR élaborée et annotée (prélude compris) en JSON,
format `certificate/1.0.0` validé par `contracts/schemas/certificate-1.0.0.json` :

- les variables locales sont des indices de de Bruijn (0 = lieur le plus proche) ;
- les variables de motif sont des emplacements numérotés (`{"bind": k}`) ;
- les variables de type sont nommées par définition et liées par des listes `forall` ;
- les littéraux portent leur sorte.

`load.py` fait l'opération inverse : il valide d'abord le certificat entier, une seule fois, par
`SchemaRegistry` et `CERTIFICATE_SCHEMA_ID` (le JSON Schema est l'unique description de la
structure ; les problèmes deviennent une `CertificateError` qui garde le chemin JSON), puis ne
fait plus que déconstruire. Il garde en code les contrôles qu'un schéma n'exprime pas : indice de
de Bruijn hors portée, variable de type non liée, emplacement cible non lié, numérotation des
emplacements de motif, liaison récursive qui n'est pas une fonction. Les tests vérifient
`export(load(c)) = c` et que le programme réimporté calcule les mêmes valeurs. CLI : `hypomnesis check FICHIERS --emit-certificate cert.json`.
Le vérificateur Lean `hypomnesis-check` (`formal/Main.lean`, `formal/Hypomnesis/Certificate.lean`)
les relit : `cd formal && lake build hypomnesis-check`, puis
`lake exe hypomnesis-check check cert.json` (codes : 0 accepté, 1 rejeté par `typeOf`, 2 hors du
fragment, 3 illisible) ou `eval cert.json` (sémantique de référence). Exemple entièrement dans
le fragment : `demo/examples/basics/certifiable.hyp`.

## Capacités (HYP-040)

`src/hypomnesis/capabilities/` (M3, strict Pyright par `# pyright: strict`) définit les neuf
interfaces génériques du §6 — `Observer`, `Generator`, `Estimator`, `Transpiler`, `Solver`,
`Validator`, `KnowledgeBase`, `Actuator`, `Resolver` — comme des `typing.Protocol`
`runtime_checkable` (conformité structurelle, sans héritage ni import de backend). Le rôle
type-théorique de chacune (§4.4 de `docs/architecture/m3-metalangage.md`) est dans sa docstring.

- `result.py` : `Result[T]` immuable (`value`, `certificate`, `diagnostics`, `ok` = aucun
  diagnostic de gravité `error`), `Diagnostic` (`code`, `message`, `severity`, `data`), `Certificate`
  (`kind`, `body`), constructeurs `success` / `failure`. Un refus du `Validator` est un diagnostic
  d'erreur dont `data` porte le contre-exemple ; un succès porte le certificat.
- `protocols.py` : un protocole par interface (méthodes à paramètres positionnels, une méthode
  par verbe : `observe`, `generate(spec, *, limit)`, `estimate`, `transpile`, `solve`, `validate`,
  `query`/`store`, `actuate`, `resolve(goal, capabilities)`), `ROLES` (clés = énumération `role`
  du manifeste d'extension, vérifié par test) et `roles_of(plugin)`.
- `safe.py` : `guarded` convertit toute `Exception` d'un plugin en `Result` en échec
  (`capability.raised`) ; règle : **jamais d'exception brute vers le noyau**.

Un plugin ne décide rien : il rend valeur et certificat, le noyau gradue et vérifie.

### Registre statique des extensions (HYP-041)

`engine/registry.py` expose `ExtensionRegistry(manifests=(), *, schemas=None)` ; par défaut,
`SchemaRegistry.with_builtin_schemas()` valide chaque manifeste contre `MANIFEST_ID`.
Le registre ne charge **jamais** le backend, ne vérifie pas ses protocoles et ne modifie pas
le registre natif fermé du noyau (ADR 0003). Le chargement effectif relève de HYP-044.

- `add(manifest)` et `add_many(manifests)` : copies profondes, validation du lot entier avant
  mutation ; doublon id/version identique accepté, contradictoire refusé.
- `load(path)` / `load_paths(paths)` : fichiers JSON ou dossiers (`*.json` immédiats, triés,
  sans récursion), enregistrement atomique de l'ensemble des chemins.
- `ids(role=None)`, `versions(id)`, `list(role=None)`, `show(id, version=None)` : index id/rôle/version ;
  toutes les versions sont inspectables sans résoudre les dépendances. `show` sans version
  choisit la plus récente ; les données retournées sont des copies profondes.
- `resolve({id: contrainte, ...})` : fermeture transitive, une version par id, backtracking
  via `resolvelib` ; versions les plus récentes d'abord, puis ordre topologique NetworkX
  (dépendances avant dépendants, ordre lexical pour les ex æquo). Aucun état n'est modifié.

Versions : SemVer 2.0.0 (`semantic-version`, pas PEP 440), préversions arbitraires et métadonnées
de build acceptées par le schéma du manifeste. Contraintes : syntaxe `SimpleSpec`, par exemple
`>=1.0.0,<2`, `*`, `=1.2.3-preview.custom`. Une préversion peut satisfaire une plage selon les
règles de `SimpleSpec` ; pour la fixer, utiliser l'égalité explicite. À précédence SemVer égale
(build différent), le texte de la version départage de façon déterministe.

Erreurs publiques (toutes dérivent de `RegistryError`, lui-même `ValueError`) :
`InvalidManifestError`, `DuplicateManifestError`, `MissingDependencyError`,
`VersionConflictError`, `DependencyCycleError`. La résolution indique les contraintes et leurs
origines en cas d'échec. Les cycles du graphe sélectionné sont refusés après résolution
(pas de recherche d'une autre solution acyclique) ; garde-fou de 10 000 tours du résolveur.
Les URI de schémas et les points d'entrée restent des métadonnées : aucune lecture distante,
aucun import ni contrôle d'existence de backend.

CLI : `hypomnesis plugins list --manifest CHEMIN [--manifest CHEMIN …] [--role ROLE]` ;
`hypomnesis plugins show ID --manifest CHEMIN [--version VERSION]`. `--manifest` est placé sur
la sous-commande `list` ou `show`. Sortie JSON indentée uniquement sur stdout (tableau des
manifestes complets pour `list`, objet pour `show`) ; pas de chemin = registre vide. Pas de
résolution à l'inspection, même si une dépendance est absente. Codes 0 succès, 1 refus applicatif
(`refusé : …` sur stderr, stdout vide), 2 erreur d'usage (dont chemin inexistant).

## Contrats

`src/hypomnesis/contracts/` : schémas JSON Schema 2020-12 (enveloppe, manifeste d'extension) et
`SchemaRegistry` (validation des schémas à l'enregistrement, enveloppe puis payload).

### Correspondance des types et JSON (HYP-042, ADR 0010)

`contracts/codec.py` : `TypeCodec(checker, type_ou_signature)` photographie les déclarations
du compilateur. `schema` rend une copie Draft 2020-12, `encode(value)` valide la valeur
runtime puis son JSON, `decode(payload)` valide le JSON puis reconstruit la valeur typée.
Primitives, tuples, listes, records, variants, options, alias, instanciations et récursion
régulière sont couverts ; erreurs `CodecError` avec chemin JSON et `UnsupportedTypeError`.
Les signatures passent par `parser.parse_type` et `Checker.resolve_type` sans mutation du
contexte d'inférence. Les références récursives sont locales dans `$defs`.

`contracts/compatibility.py::require_inclusion(source, target, schemas)` démontre une
inclusion structurelle suffisante, avec refus explicite des mots-clés hors sous-ensemble.
`ExtensionRegistry.prepare(id, checker, version=None)` exige type d'entrée ⊆ contrat et
contrat de sortie ⊆ type ; rend `PreparedExtension` (`manifest`, `input`, `output`,
`encode_input`, `decode_output`). Ces deux dernières méthodes valident aussi le contrat
concret. L'inspection reste indépendante ; HYP-044 devra utiliser cette préparation avant
chargement et invocation. Les contrats sont cherchés par identifiant enregistré exact,
jamais téléchargés. `SchemaRegistry.schema(id)` rend une copie ; l'enregistrement possède
aussi sa copie, pour éviter une mutation ultérieure par l'appelant.

Le sous-ensemble comprend scalaires, bornes numériques, longueurs, constantes/enum, objets
fermés, tableaux homogènes/tuples, `anyOf`, `oneOf` étiquetés disjoints et références locales
ou absolues déjà enregistrées. `CompatibilityError` indique une inclusion non établie ;
`UnsupportedSchemaError` un schéma hors sous-ensemble. `pattern`, `format`, `allOf`,
conditions, objets ouverts, ressources imbriquées et références relatives sont refusés.
Les sorties `float` demandent des bornes finies ; JSON Schema `integer` accepte un token
intégral comme `1.0`, reconstruit exactement comme `int`.

`runtime/json.py` partage l'encodage structurel et les conversions `Json.t` entre
`engine/bridge.py`, la primitive `core.to_json` et `engine/procedure.py`. Les options sont
étiquetées, les entiers utilisent `Json.Int` (ajouté après les constructeurs existants),
les flottants restent flottants ; NaN/infinis, listes mal formées et clés JSON non textuelles
ou dupliquées sont refusés. `Json.num` reste une conversion explicite vers float,
`Json.int` est exact. Les anciens formats d'options ne sont pas acceptés silencieusement.
Les attentes JSON du banc mécanique et les explications numériques sont migrées ; les
contrats capteurs/actionneurs existants n'exposaient pas d'option.

Tests : `tests/unit/test_json_codec.py`, `tests/unit/test_contract_compatibility.py`,
`tests/unit/test_effects.py`, `tests/integration/test_languages.py`. Propriétés Hypothesis
sur types composés et récursifs, sérialisation JSON réelle et accord des ponts ; manifestes
incompatibles refusés sans importer un backend piégé. Ces tests ne remplacent pas HYP-043.

## Observabilité (HYP-015)

`src/hypomnesis/observability/trace.py` : la classe `Tracer` est une façade au-dessus du SDK
OpenTelemetry (`opentelemetry-sdk`). Chaque instance possède son propre `TracerProvider` (jamais
de `set_tracer_provider` global) avec un `SimpleSpanProcessor(InMemorySpanExporter)` ; `tree()`
et `export()` (clé `trace` de `rapport.json`) sont reconstruits depuis les spans terminés, triés
par début. API : `span(nom, **attributs)` (gestionnaire de contexte ; le parent est la pile
propre au `Tracer`, pas le contexte ambiant), `trace_id`, `spans`, `tree()`, `export()`,
`current_context()`. Les identifiants sont exportés en hexadécimal (trace 32 caractères, span 16) ;
le `trace_id` est fixé à la création du `Tracer` (générateur d'identifiants dédié). Les valeurs
d'attributs non scalaires sont rendues par `repr`. Une exception ouvre le statut `error`
(`StatusCode.ERROR`) puis est relancée.

`trace_context(tracer)` renvoie `{"traceparent": "00-<trace>-<span>-<flags>"}` pour l'enveloppe de
message (§9.6, schéma `envelope-1.0.0.json`) ; hors d'un span, l'identifiant de span est nul et
le drapeau d'échantillonnage éteint. `Tracer(enabled=False)` utilise `NoOpTracerProvider` : aucun
span, aucun effet sur les connaissances (ADR 0005, test `tests/unit/test_trace.py`).
Export OTLP vers un collecteur : HYP-070 (non fait ici, aucun accès réseau).

## Vérification formelle

`formal/` (Lean 4.35, sans dépendance) : fragment de la Core IR, typage, évaluateur à budget,
preuves de sûreté, vérificateur correct et complet, monotonie du budget, provenance en
semi-anneau. Propriétés : `docs/verification/proprietes.md`. Stratégie : `docs/verification/strategie.md`.

## Exemples

- `demo/examples/basics/`, `demo/examples/mechanics/` : tour du langage, plaque du §4.2.

## Éditeur VS Code et serveur LSP (HYP-131/132)

`editors/vscode/` déclare le langage `.hyp`, une grammaire TextMate (commentaires
imbriqués/documentaires, mots-clés Lark, types, nombres et chaînes) et un client
`vscode-languageclient`. Tests Oniguruma : `npm ci && npm test` dans ce dossier ;
construction du paquet : `npm run package` (Node.js ≥ 22). Un job CI distinct vérifie
la compilation TypeScript, la grammaire et le VSIX.

Installer l'extra Python `lsp` (`pygls` 2) pour `hypomnesis-lsp`, ou
`python -m hypomnesis.lsp.server` sur stdio. Le client choisit le `.venv` du dossier,
sinon Python système, avec surcharge `hypomnesis.pythonPath`. Un serveur par dossier ;
pas de lancement Python dans un espace non approuvé. Les réglages sont documentés dans
`editors/vscode/README.md`.

`lsp/analysis.py` utilise le plan de `engine/layers.py` et ses sessions statiques,
sur les dépendances transitives puis le document. Une session neuve évite les noms obsolètes ;
aucun programme édité, contrat d'effet ou adaptateur Python n'est exécuté. Le contexte
M2 vient du `langage.hyp` le plus proche, de `demo/programs/<nom>` vers `demo/languages/<nom>`,
ou de `hypomnesis.languageRoot`. Les documents ouverts non enregistrés remplacent les
sources disque, déclarations d'imports comprises. Une erreur de dépendance est signalée au début du document avec son
chemin ; une erreur du document reprend exactement message, étape et étendue du compilateur.
Les positions sont converties de coordonnées 1-based en positions LSP négociées
(UTF-16 par défaut, UTF-8/32 possibles).

`lsp/server.py` diffère l'analyse de 300 ms par défaut et annule les tâches obsolètes.
`lsp/worker.py` isole chaque compilation dans un sous-processus tué à l'annulation ou
au dépassement de 30 secondes. Les erreurs d'infrastructure sont journalisées et publiées
comme diagnostics, jamais assimilées à un succès. Correction et fermeture effacent les
diagnostics. Les tests Python parlent directement JSON-RPC/stdio au serveur ; le test
`npm run test:host` vérifie également l'association du langage, l'apparition de l'erreur
et sa disparition après correction non enregistrée dans un véritable hôte VS Code isolé.
Pas de complétion, survol ou navigation dans ce lot.

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

## Validation des effets (HYP-062)

Validation des effets HYP-062 : le dispatcher journalise séparément les
contrôles dans `Outcome.checks` et `commands[].checks` des rapports.
`PermissionPolicy` permet les autorisations exactes et refus prioritaires ;
`Actuator.safety`, `requires_human` et `observe_effects` complètent le pipeline.
L'hôte fournit `policy` et `approve` au dispatcher ou à `run_procedure`.
HYP-064 : les handlers `_dry_run`, `_simulate`, `_production` partagent la
même signature et les contrôles en amont. Le mode, dry-run par défaut, ne
peut être choisi que par CLI/hôte. Le span `command.dispatch` inclut les
contrôles ; `actuator.execute` ne trace que l'appel effectif et ses relances,
jamais un dry-run ou une simulation.
Guide de l'ordre des étapes, modes et limites :
[validation-effets.md](docs/architecture/validation-effets.md).

## Kanban

`scripts/kanban.py` (PyYAML pour le front-matter, NetworkX pour le graphe des dépendances ; à
lancer avec `.venv/bin/python`) lit `.agentkanban/tasks/` :

| Commande | Rôle |
|---|---|
| `check` | format des tâches, couloirs, dépendances inconnues, cycles (`nx.simple_cycles`), tâche démarrée avant ses dépendances |
| `status [--json]` | hypothèses (`hypothese`), tâches en cours, prêtes (avec ce qu'elles débloquent), bloquées (avec ce qu'elles attendent), en `qa` (à vérifier par l'utilisateur), et chemin critique vers les tâches P0 restantes (`critical_path`, `nx.dag_longest_path`) |
| `graph [--wait]` | injecte tâches et relations (`depends_on`, `touches`, `references`, `defined_in`, `contains`) dans `graphify-out/graph.json`, sous le verrou de reconstruction de Graphify ; idempotent |

Les éléments injectés portent `_origin: "kanban"` et `source_file: .agentkanban/board.yaml`.
Le front-matter est lu par `yaml.safe_load` à une nuance près : les dates restent des chaînes
(le résolveur de timestamps est retiré), car l'extension Agent Kanban les écrit sans guillemets.
Le graphe des tâches est un `nx.DiGraph` tâche → dépendance (`dependency_graph`).
Le couloir `hypothese`, placé avant `todo`, conserve les propositions non adoptées.
Il n'est ni prêt à l'exécution ni terminé ; l'ordonnanceur parallèle l'exclut
via la règle commune `is_ready`, sans promotion implicite en tâche de travail.
Une reconstruction incrémentale de Graphify conserve les nœuds mais perd les relations vers les
fichiers qu'elle réextrait : réinjecter après chaque `graphify update .`, ce que fait
`./scripts/validate.sh graphe`. Ce mode réinjecte aussi avant la reconstruction si un graphe
existe, pour migrer les anciennes représentations synthétiques. Un chemin sans nœud-fichier
réel est un document nommé `Chemin Kanban : …`, avec son chemin dans `referenced_path` :
il ne doit pas être confondu avec un fichier AST par la déduplication de Graphify, sous peine
de déclencher le garde-fou contre la perte de nœuds sémantiques. Les vrais nœuds-fichiers
restent utilisés dès qu'ils sont disponibles. L'injection prend le verrou de reconstruction de Graphify ;
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

## Automate des commandes (HYP-061)

`src/hypomnesis/effects/commands.py` (pur, sans horloge ni `sleep`) : `State` (§9.7 + `DryRun`,
`Simulated`), table explicite `TRANSITIONS`, `can_move`, `CommandRecord` (journal, tentatives,
échéance ; `move` lève `IllegalTransition`), `RetryPolicy` (tentatives max, délai, backoff) et
`may_retry`. Les états terminaux (`Completed`, `Rejected`, `Failed`, `TimedOut`, `UnknownOutcome`,
`DryRun`, `Simulated`) sont absorbants. La seule façon d'exécuter deux fois est l'auto-transition
`Dispatched → Dispatched` (relance), accordée **aux seules commandes idempotentes** (`Actuator.idempotent`,
`False` par défaut) dans la limite de `max_attempts`.

`Dispatcher` (`effects/dispatcher.py`) : déduplication par `command_id` (la même commande rend l'issue
existante sans rappeler l'actionneur ; même id avec un autre contenu → `DuplicateCommand`) ; horloge et
`sleep` injectables ; `Actuator.timeout` fixe l'échéance. Une exception ordinaire de l'actionneur donne
`Failed` (pas de relance) ; `TransportError` (aucune réponse fiable : l'action a pu avoir lieu) donne une
relance si idempotent, sinon `UnknownOutcome`. Une réponse tardive donne `TimedOut`. `Accepted` est dans
la table mais n'est pas émis par les transports synchrones HYP-063. Miroir de la propriété Lean HYP-066
(`docs/verification/proprietes.md`) ; tests : `tests/unit/test_commands.py`.

## Transports (HYP-063)

`effects/transports/` définit `Transport`, `MemoryTransport`, `FileTransport`
(JSONL append-only, curseur de lecture local) et `replay`. Chaque message est
un instantané JSON strict validé par l'enveloppe et son contrat nommé, à
l'envoi et à la réception. Le rejeu restitue les messages exacts, pas les
effets physiques ; pas de garantie multi-processus ni de curseur durable.
Les I/O du langage M2 ventilation utilisent ces transports pour requêtes,
relevés, commandes et réponses. L'hôte choisit mémoire ou fichiers ; les
manifestes restent descriptifs et les décorateurs restent le branchement I/O.
Guide et exemple exécutable : [transports.md](docs/architecture/transports.md),
`examples/robotics/transport.py`.

## Preuves de dispatch (HYP-065)

`formal/Hypomnesis/Effects/Dispatch.lean` modélise les états, la table de
transitions et le journal par commande. `dispatch_ordered` prouve l'ordre
validation puis autorisation avant chaque envoi, y compris les relances ;
`dispatch_permitted` et `no_dispatch_without_permission` prouvent la permission
nécessaire. Audit des axiomes : `propext` seulement pour ces trois théorèmes.
Le test d'intégration `test_effects_model.py` calcule la table Lean et compare
les 144 paires à Python. Il requiert Lean/Lake sans skip. Correspondance
ligne à ligne et frontières : [dispatch.md](docs/verification/dispatch.md).
Ce n'est pas une preuve de raffinement du Python ni de sécurité physique.

## Descriptions obligatoires (HYP-137)

`language/docs.py` extrait les `(** … *)` en lexant la source (`parser.lex`, pas de regex) et les
rattache par position ; `declarations` rend aussi la position de chaque élément (nom du membre pour un
champ ou un constructeur). `missing_descriptions` liste les éléments publics (aucun `_` dans le nom
qualifié) sans description ; `load_language(root, strict=True)` lève `MissingDescriptionError`
(`engine/language.py`) pour le premier. `@interne` : décrit mais hors catalogue ; `@discret` : membre
listé sans sa description (`codegen/describe.py`). Règles complètes : ADR 0009 (décisions 6 et 7). Tests :
`tests/unit/test_language_docs.py` (règle, propriétés « Core IR et certificat identiques avec ou sans
descriptions ») et `packages/codegen/tests/` avec ses instantanés `snapshots/`
(catalogue rendu, octet pour octet).

## Commandes

```bash
./scripts/validate.sh                   # rapide : Ruff, Kanban, tests
./scripts/validate.sh complet           # tous les validateurs
./scripts/validate.sh graphe            # reconstruire le graphe Graphify + Kanban
python3 scripts/kanban.py status        # tâches prêtes et bloquées
.venv/bin/hypomnesis run demo/examples/basics/tour.hyp
```

## Bibliothèques et infrastructure conservée (audit HYP-007, 2026-11-04)

Les sept remplacements sont présents dans le code : Typer (`cli.py`), NetworkX
(`epistemics/knowledge.py`, `scripts/kanban.py`), PyYAML (Kanban), client officiel Ollama
(`codegen/ollama.py`), SDK OpenTelemetry (`observability/trace.py`), matplotlib (`codegen/plots.py`)
et jsonschema via `SchemaRegistry` (`certify/load.py`). Cela ne vaut pas clôture des tickets :
HYP-014 reste en `doing`, avec comparaison réelle du banc avant/après à vérifier par l'utilisateur.
La façade locale, les conversions de valeurs et les règles de sûreté ne sont pas des
réimplémentations des bibliothèques. Le noyau pur et Lean restent inchangés (ADR 0003, 0007).

### Justification des dépendances déclarées

Depuis HYP-146, les dépendances LLM sont déclarées dans `packages/codegen/pyproject.toml`,
pas dans les extras du moteur ; Codegen reste un paquet optionnel. Ses tests fonctionnent
sans serveur ni GPU. Le tableau reflète ce nouvel emplacement.
Les dépendances transitives (Click, Rich, httpx, NumPy…) ne sont pas ajoutées sans besoin direct.

| Dépendance directe | Groupe | Justification |
|---|---|---|
| `hatchling` | construction | Construction du paquet Python et inclusion des ressources. |
| `lark` | exécution | Grammaire LALR, analyse syntaxique et lexage des descriptions (`language/parser.py`). |
| `jsonschema[format-nongpl]` | exécution | Validation Draft 2020-12, formats compris, des contrats et certificats (`contracts/registry.py`). |
| `referencing` | exécution | Résolution contrôlée des références de schémas enregistrés (`contracts/registry.py`). |
| `z3-solver` | exécution | Résolution et vérification des contraintes du Problem IR (`backends/z3_solver.py`). |
| `typer` | exécution | Commandes, paramètres annotés et aide de la CLI (`cli.py`, HYP-006). |
| `networkx` | exécution | Graphes de provenance et de dépendances, parcours et cycles ; ordre des extensions (HYP-008/009/041). |
| `semantic-version` | exécution | SemVer et contraintes `SimpleSpec`, sans parseur de versions maison (`engine/registry.py`, HYP-041). |
| `resolvelib` | exécution | Résolution transitive par retour arrière des extensions (`engine/registry.py`, HYP-041). |
| `opentelemetry-api` | exécution | Contextes, statuts et fournisseur sans effet pour les traces désactivées (`observability/trace.py`). |
| `opentelemetry-sdk` | exécution | Création et collecte des spans, export en mémoire (`observability/trace.py`, HYP-015). |
| `jinja2` | Codegen | Gabarits du catalogue et du prompt (`codegen/describe.py`). |
| `scikit-learn` | Codegen | TF-IDF et similarité cosinus du mini-RAG (`codegen/retrieval.py`) ; HYP-054 reste distinct. |
| `ollama` | Codegen | Client officiel, réponses typées et erreurs HTTP (`codegen/ollama.py`, HYP-014). |
| `matplotlib` | Codegen | Figures PNG/SVG hors affichage, régénérables depuis le JSON (`codegen/plots.py`, HYP-016). |
| `scipy` | Codegen | Intervalles de Wilson par `binomtest().proportion_ci`, dans le banc et les figures (HYP-139). |
| `pyyaml` | `dev` | Lecture sûre du front-matter des tickets (`scripts/kanban.py`, HYP-009). |
| `pytest` | `dev` | Tests unitaires, d'intégration et de contrats. |
| `hypothesis` | `dev` | Propriétés de provenance, certificats, codecs et tests différentiels. |
| `ruff` | `dev` | Analyse statique et formatage Python. |
| `pyright` | `dev` | Vérification statique des types Python. |
| `pre-commit` | `dev` | Orchestration explicite des validateurs du dépôt, sans hook git obligatoire. |

### Inventaire du code maison restant

Chemins relatifs à `src/hypomnesis/`, sauf `codegen/` (voir HYP-146) et indication contraire. Les décisions concernent
le besoin actuel, pas une interdiction de réexaminer une bibliothèque si ce besoin grandit.

| Emplacement et source | Décision et bibliothèque examinée |
|---|---|
| `language/docs.py::_doc_index`, `parser.py::lex` | **Déjà migré** par HYP-137 : jetons Lark (`dont_ignore=True`), plus de regex globale `_DOC`. Garder `parse_doc` et `_TAG`, format de balises du projet. |
| `codegen/benchmark.py::wilson`, `plots.py::wilson_interval` | **Déjà migré** par HYP-139 vers SciPy, désormais déclaré dans Codegen. Garder `summary`, tableau Markdown spécifique au banc. |
| `effects/commands.py::TRANSITIONS`, `may_retry`, `RetryPolicy` ; `dispatcher.py::_execute` | **Garder** : automate explicite et règle de non-relance des commandes non idempotentes, miroir de HYP-066. `transitions`/`python-statemachine`/`tenacity` n'enlèveraient pas ces règles ; délai exponentiel actuellement élémentaire. HYP-061 porte ce besoin. |
| `scripts/kanban.py::graph_lock`, `_lock_busy`, `_section_paths`, `_meta` | **Garder** : protocole `flock` de Graphify et extraction du format Markdown borné ; `filelock` ou un analyseur Markdown complet ne sont pas un remplacement transparent. Aucun changement de verrou dans cet audit. |
| `observability/trace.py::Tracer.tree`, `export` | **Garder** : rendu des rapports M0 au-dessus des spans SDK ; réexaminer avec l'export OTLP de HYP-070, sans nouveau traceur. |
| `cli.py::_repl` ; `engine/procedure.py::ProcedureReport.render` | **Garder** : tampon `;;` et rendus spécifiques. `prompt_toolkit` serait disproportionné sans besoin d'édition enrichie ; Rich est déjà fourni par Typer, mise en forme non requise. |
| `codegen/translation.py::extract_code`, `translate` | **Garder** : extraction des blocs et réparation guidée par les diagnostics, protocole propre au projet. |
| `demo/languages/mecanique/adaptateurs/transcription.py::transcrire` | **Garder** : adaptateur M2 déterministe, non infrastructure M3 ; HYP-081 porte la transcription LLM. Aucune migration métier ici. |
| `codegen/retrieval.py::Retriever`, `_normalise` ; `codegen/describe.py::_environment` | **Déjà délégué** à scikit-learn et Jinja2 ; garder la normalisation numérique et le catalogue propres au banc. |
| `contracts/registry.py::SchemaRegistry` | **Garder** : adaptateur de jsonschema et referencing, non validateur structurel maison. |
| `engine/bridge.py::to_json`, `runtime/natives.py::to_json_value`, `certify/export.py::export_certificate` | **Garder** : codecs des valeurs Hypomnesis et certificat lu par Lean. Les ponts JSON passent désormais par `runtime/json.py` (HYP-042), pas par des conversions dupliquées. |
| `session.py::run_deep` | **Garder** : pile CPython dédiée à la récursion non terminale ; une bibliothèque générique ne la supprime pas. Réexamen avec les évolutions d'évaluation de HYP-013. |
| `language/parser.py::_parser`, `_ToAst` | **Déjà délégué** à Lark et `ast.literal_eval` ; garder la construction de l'AST Hypomnesis. |
| `language/typesystem/`, `runtime/interpreter.py`, `epistemics/provenance.py`, `ir/core.py` | **Garder** : inférence, sémantique et semi-anneau propres au projet (ADR 0002/0007) ; NetworkX ne remplace pas l'évaluation de la provenance. |

Aucune nouvelle migration d'infrastructure retenue dans ce périmètre : aucun nouveau ticket
nécessaire. HYP-054 (estimateur appris) et HYP-070 (instrumentation/OTLP) restent des travaux
distincts, pas des conditions supplémentaires de clôture des sept remplacements.

## Backend Python contractuel (HYP-044)

`backends/python/PythonBackend` reçoit une `PreparedExtension` et les permissions
accordées par l'hôte. Il réutilise les codecs et contrats de HYP-042, refuse les
préconditions non interprétées et n'importe jamais le plugin dans le processus hôte.
`register(natives, symbol)` autorise une primitive sur un registre explicite, à
utiliser par une déclaration `external` correspondant à la signature préparée.

Chaque appel valide l'entrée avant import, communique en JSON avec un sous-processus,
puis valide/décode la sortie. Le délai couvre le démarrage du worker et l'import ;
expiration et crash sont des `BackendError` typées, également visibles depuis le
langage et journalisées par `Tracer`. Le groupe enfant est arrêté et le processus
direct récolté. Aucune relance implicite ; pas de bac à sable de sécurité.
Voir [le guide](docs/architecture/backend-python.md).

## Problem IR déclarative (HYP-051)

`ir/problem.py` conserve les variables bornées/discrètes, contraintes linéaires et
l'objectif de proximité. Ses structures de problème valident immutabilité,
identités, références, domaines et nombres finis, normalisés en rationnels.
`check_assignment` interprète les flottants selon leur écriture décimale, comme
la construction du problème.

`State`, `Action`, `Transition` ajoutent la description d'un plan sans exécution.
Le prélude garde `Problem.problem` et ajoute `Problem.planning_problem`, avec
`base_problem`, états, actions et transitions. Le pont `engine.bridge.to_problem`
accepte les deux formes. Les nouveaux champs d'identité du prélude sont distincts
pour préserver la résolution nominale des champs historiques.

Le format `problem/1.0.0` est un JSON fermé et versionné : chaque nombre est une
paire d'entiers numérateur/dénominateur positif. Schéma puis constructeurs assurent
respectivement validation structurelle et sémantique. Z3 continue de résoudre
uniquement la partie numérique ; les transitions ne sont pas un certificat
d'exécutabilité. Voir [le guide](docs/architecture/problem-ir.md).

## Ordonnanceur local de worktrees (HYP-148)

`scripts/parallel.py` réutilise `scripts/kanban.py` et fournit `plan`, `prepare`,
`status`, `record`, `integrate`. La CLI prépare et suit les travaux ; la conversation
principale lance les agents, sans SDK ajouté. Trois travaux actifs par défaut.
Les chemins/globs et interfaces réservées sont comparés conservativement, et les
modifications réelles sont vérifiées avant attestation.

L'état et les logs résident sous le répertoire Git commun `parallel/`, hors index,
avec verrou exclusif et écritures atomiques. Les validations sont réellement
exécutées et liées au SHA ; elles deviennent périmées après un nouveau commit.
L'intégration prépare un merge sans commit, valide l'arbre combiné et refuse
les mutations du validateur. Conflit ou échec conserve l'état pour intervention,
sans reset, suppression automatique, push ou changement de couloir.
Voir [la CLI et ses limites](docs/outillage/ordonnanceur-parallele.md).
