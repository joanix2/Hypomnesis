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

HYP-023 est en cours : `formal/Hypomnesis/Core/PolyTypes.lean` formalise
les types paramétriques et schémas de rang 1 (ADR 0020), avec substitutions
sans capture, lois d'identité/composition, bonne portée et instanciation des
constructeurs/environnements. `PolySyntax.lean` ajoute l'instanciation de
types explicite et le let-polymorphe ; `PolyTyping.lean` définit son checker
et son jugement déclaratif. P41 prouve leur équivalence sous les préconditions
de signature et d'environnement bien formés. P42 prouve la préservation du
jugement par substitution des types, y compris les substitutions relevées au
let polymorphe, les constructeurs paramétriques et les contextes de motifs.
Les régressions vérifient le let identité à int/bool, la spécialisation de
variables de type ouvertes et des refus négatifs.

Le pont vers l'évaluateur, le décodeur/CLI et le vrai corps de `List.map`
ne sont pas encore prouvés ou branchés. La certification existante continue
à monomorphiser ; aucune garantie de sûreté opérationnelle polymorphe n'est
revendiquée.

La sûreté polymorphe ne se déduit pas d'un simple effacement vers le noyau
actuel : `Core.Ctx` attribue un seul type à chaque valeur d'environnement et
`Core.Sig` fixe un payload monomorphe par déclaration, tandis qu'un même
schéma `let` et une donnée paramétrique peuvent être instanciés à plusieurs
types dans le même programme. Le pont doit donc interpréter les schémas et
signatures polymorphes dans la relation de valeurs/environnements (ou fournir
une spécialisation avec une preuve de préservation de l'évaluation), puis
prouver la sûreté du véritable `Core.eval`. `Core.eval_safe` et ses preuves
de motifs/fuel restent la référence à préserver ; leur réutilisation par
une conversion monomorphe non démontrée ne suffit pas.
Une régression vérifie conjointement le type polymorphe et l'exécution par
`Core.eval` du même `let` identité à `int` et `bool` ; ce cas concret n'est
pas un théorème général de sûreté.
P43 prouve l'invariance de l'effacement et du résultat de `Core.eval` par
substitution de types, ainsi que le transport de l'absence de `stuck` quand
cette propriété est déjà établie. Il reste à établir ce cas de base pour
toutes les dérivations polymorphes. P44 établit désormais un cas de base
vérifié : les constantes, conditions, paires, projections, opérations
binaires, `let` monomorphes et certaines lambdas/applications monomorphes
s'effacent en termes Core typés ; les `fix` monomorphes et leurs fermetures
récursives sont aussi couverts. `Core.eval_safe` garantit leur sûreté à tout
budget. Pour les fermetures, le fragment impose l'égalité entre les
effacements spécialisé et polymorphe du corps, afin que l'évaluateur réel
stocke exactement le corps justifié par le typage. Une relation
`RuntimeEnvRel` relie aussi les environnements de schémas monomorphes aux
valeurs Core pour ce fragment ; les variables à arguments de types vides sont
donc prises en charge lorsque leur schéma est monomorphe, y compris dans le
corps d'un `let` et les fermetures monomorphes peuvent capturer ces valeurs.
La récursion et les motifs scalaires/de paires sont couverts dans ce fragment ;
les motifs de constructeurs, les données paramétriques et les liaisons
polymorphes multi-instanciées restent hors preuve. P44 ne constitue pas encore
la sûreté générale du polymorphisme de rang 1.
Indépendamment de cette preuve de fragment, P45 établit pour l'exemple concret
du `let` identité partagé entre `int` et `bool` que l'exécution à fuel 20 rend
une paire dans la relation Core `ValTy`. Cette régression n'est pas une
garantie générale pour le fragment polymorphe.
P46 ajoute un terme récursif polymorphe `List.map`-équivalent, vérifié par le
checker et évalué à deux instanciations dans un même programme (`int → bool`
et `bool → int`). C'est un exemple Lean autonome : il ne décode pas le corps
exact de `List.map` depuis le certificat Python et ne ferme donc pas le pont
CLI.

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

### Déclarations natives et couches (HYP-147/151, ADR 0013/0016)

HYP-011 / ADR 0017 ajoute les imports locaux `import`, `from`, `as` (sans
étoile). `Session` résout les chemins relativement au fichier source et
partage les espaces de noms par chemin canonique. Le typeur élabore les
dépendances dans des frames isolées avec le seul prélude ; alias, types et
constructeurs gardent leur identité. Les imports restent des opérations
de compilation vers les définitions Core existantes, pas une nouvelle IR.
Les imports de sources M2 sont confinés au paquet et les overlays LSP se
propagent transitivement ; le catalogue projette la documentation sous
les noms publics. Les avertissements conservent le fichier importé.

Les caches d'import sont transactionnels pour les erreurs d'analyse.
Une session statique peut ensuite exécuter les définitions importées non
encore évaluées, sans les dupliquer dans les certificats. Après un échec
d'exécution impliquant ces définitions, la réutilisation exige une nouvelle
session afin de ne pas rejouer automatiquement des effets partiels.
`execute_prelude=False` prépare aussi le prélude sans l'évaluer.

HYP-012 / ADR 0018 ajoute `module type S = sig ... end` et `module M : S`.
`Namespace.signatures` contient les spécifications lexicalement résolues ;
les types/alias sont résolus avant les valeurs, indépendamment de leur ordre.
Le scellement construit un espace de noms public distinct : types abstraits
génératifs (`TypeInfo.kind = abstract`), alias manifestes et valeurs promises
seulement. Une instanciation rigide vérifie la subsomption polymorphe.
Des `DefValue` Core adaptent explicitement les arguments de type des valeurs
exportées ; leurs définitions privées restent dans l'ordre d'évaluation.

Les représentations privées des types abstraits sont conservées dans `alias`
pour l'export, mais jamais développées par `_to_type` ni par les contrats JSON.
L'export des certificats les abaisse dans les annotations et les templates
de types ; aucune extension de la Core IR, du format 1.1.0 ou de Lean.
Le vrai checker vérifie ces programmes élaborés ; l'opacité du frontend
reste testée en Python, pas nouvellement prouvée en Lean. Les déclarations
documentaires sont filtrées par les namespaces publics pour le catalogue
et la vérification des descriptions M2.

Le fichier d'entrée `.hyp`, par convention `langage.hyp`, commence par
`language nom = struct let version = "1" let imports = ["../base"] end`.
HYP-151 remplace la forme extérieure à accolades : le parseur la refuse
en attendant `struct`. Chaque champ est une liaison `let cle = valeur`,
sans `;` entre liaisons ; les listes/records imbriqués restent inchangés.
Ces liaisons ne sont pas exécutables et n'exportent aucune variable.
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

HYP-034 : `epistemics/storage.py` persiste le journal typé, sous contrat
`knowledge-journal/1.0.0` et schéma SQLite version 2. Transactions et protections
UPDATE/DELETE préservent le préfixe ; upgrade 1 → 2 non destructif.
`Event.unknown` conserve l'inconnue exacte issue d'une invalidation, le
compteur explicite des sources survit au redémarrage. Rejeu sans exécution
de méthode ou prédicat, avec TypeCodec fermé par propriété. Les descripteurs
d'invariants exigent des liaisons hôte, pas du code importé. JSON strict et
erreurs localisées ; les modifications non journalisées de la projection
sont refusées. Tests : `tests/unit/test_knowledge_storage.py`.

HYP-035 : `epistemics/conflicts.py` vérifie les attributs fonctionnels et
invariants purs déclarés. `KnowledgeBase.conflicts` est une lecture vivante
du journal et des faits encore étayés, pas une notification poussée : une
ancienne assertion ne disparaît pas par simple écrasement de la projection
`facts`. Les rapports immuables citent faits, provenances, sources et retraits.
`best-support` réutilise la sélection des métavariables ; une sélection ne
masque jamais le conflit, une égalité incompatible ne choisit personne.
Un invariant violé n'est pas réparé automatiquement. Les contrôles absents
ou incomplets restent `unchecked`. Aucun nouveau statut concret ou schéma
JSON ; preuve de correction réservée HYP-037. Tests de construction générés :
`tests/unit/test_conflicts.py`. Détails : guide des connaissances.

HYP-036 prouve dans `formal/Hypomnesis/Epistemics/Revision.lean`
l'équivalence index/référence exhaustive et le préfixe du journal (P29–P30).
Les valeurs et le contexte sont génériques et inchangés. Correction associée :
les provenances contenant zéro, sans forcément dépendre d'une observation,
sont candidates à l'invalidation ; décision booléenne exacte, pas de faux
retrait pour `ZERO + ONE`. Les termes non concernés sans zéro restent non
évalués. Le rejeu suit cette règle, avec message d'invalidation non trompeur.
160 cas réels Python/Lean comparent l'état et chaque champ du journal ;
test obligatoire en CI des preuves et validation Lean/complète.

HYP-037 : `formal/Hypomnesis/Epistemics/Conflicts.lean` prouve P31 :
aucun rapport fonctionnel ou d'invariant sans incompatibilité avec les
contraintes déclarées sur les assertions actives. Valeurs et prédicats
génériques ; aucune confusion entre grade de support et cohérence.
48 bases réelles × deux politiques comparent les rapports effacés au
détecteur Lean ; égalité de snapshots explicitement projetée et vérifiée.
La pureté/fidélité des prédicats hôte et de l'égalité Python reste une
frontière, pas un théorème de théorie métier ou de raisonnement universel.

HYP-032 : `epistemics/metavariables.py` ajoute `MetaVar` (TypeCodec fermé,
contraintes nommées), `Proposal`, `propose`, `best`, `resolve` et `conflict`.
Opérations persistantes ; toute nouvelle proposition rouvre la résolution.
Pas de lecture concrète avant résolution ; les conflits exigent un choix
explicite et restent visibles après ce choix. Le support d'une proposition
est un jugement hôte conservé avec sa provenance, pas une promotion automatique
d'un fait de la base. Guide : [connaissances.md](docs/architecture/connaissances.md).

HYP-038 : le prélude fournit `Knowledge` (base persistante, lookup/value
optionnels, provenance/support, derive). Les fonctions sont écrites en
Hypomnesis, sans ajout de natifs ni de Core IR. Le pont hôte
`epistemics.language.snapshot_value` produit une vue `Json.t Knowledge.t`
immuable ; un encodeur explicite est requis pour des valeurs nominales.
La vue ne certifie pas des observations et ne modifie pas la base réelle.
Produits, alternatives et retraits sont comparés aux lectures Python ;
exemple : `demo/examples/knowledge/plaque.hyp`.

HYP-050 : `engine/rules.py` fournit le chaînage positif sous budget exact,
`Conclusion`/`Rule`/`RuleReport`, alternatives de provenance par règle et
conflits explicites. Les défauts ont une source Defaulted révocable retirée
au prochain passage lorsqu'une observation remplace directement leur cible ;
HYP-033 invalide puis le moteur recalcule les dépendants. Les contributions
persistantes évitent les réécritures au point fixe. Publication individuelle
validée, pas de transaction sur tout le passage. La récursion de provenance
peut épuiser le budget. `language_rule` adapte une fonction pure
`Json.t list -> Json.t option` : logique M2 dans le langage, pas dans Python.
Exemple : `examples/knowledge/rules.py` ; détails dans le guide connaissances.

HYP-054 : `backends/sklearn` charge scikit-learn à la construction seulement
(extra `sklearn`). Régression linéaire déterministe, validation distincte,
refus des entrées hors boîte d'entraînement, diagnostics `Result` et
`Prediction` avec modèle/version/RMSE empirique. L'hôte enregistre Estimated
avec ces métadonnées dans la source ; aucune résolution de MetaVar implicite.
Le jeu synthétique versionné reste en M2 et ne certifie pas une pièce.
Suite optionnelle `tests/optional`, exécutée par la validation complète,
exclue du job core-only. Guide : [estimateurs.md](docs/architecture/estimateurs.md).

HYP-055 : `engine/validators.py` implémente Validator par une fonction pure
Hypomnesis `type_nominal -> string list`, avec TypeCodec fermé. Acceptation :
certificat rejouable ; rejet logique : proposition complète et violations,
rejouées par une fonction choisie par l'hôte. Erreur de type ou panne du
vérificateur n'est jamais présentée comme une réfutation. La géométrie reste
en M2 (`Plaque.verifier_proposition`), avec dimensions positives et épaisseur
zéro refusée sans division. Aucun fait/promouvoir Observed, aucune preuve
Lean revendiquée. Guide : [validateurs.md](docs/architecture/validateurs.md).

HYP-068 : le scénario ventilation utilise deux capteurs simulés distincts,
avec API M2 `reguler_avec_confirmation` et wrapper `reguler` compatible.
Seul Completed mène à la confirmation : simulation/rejet/échec/issue inconnue
ne réfutent pas l'hypothèse physique. Le budget borne les actions et vérifie
le seuil atteint lors de la dernière action. La trace distingue
`procedure.resume` (continuation pure), `observer.read`, `command.dispatch`
et `actuator.execute`. Guide : [retroaction.md](docs/architecture/retroaction.md).

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
la première erreur fatale ; le tableau peut aussi conserver plusieurs avertissements
de filtrage précédents (HYP-010, gravité `warning`).

HYP-010 : `typesystem/exhaustiveness.py` analyse l'utilité des matrices de
motifs Core IR après unification, par spécialisation et matrice par défaut.
Constructeurs, produits/records, littéraux, alternatives et alias sont couverts ;
les gardes ne contribuent jamais à la couverture. Les sites incluent matches,
fonctions, paramètres et liaisons. Un témoin `_` décrit une sous-valeur quelconque.
L'inhabitabilité des types récursifs sans base et la vérité des gardes ne sont
pas décidées ; l'analyse est conservatrice.

HYP-022 : `Core/Coverage.lean` modélise les mêmes spécialisations/matrices
par défaut avec budget explicite et `Option Bool` (seul `some true` accepte).
P34 prouve la couverture des valeurs bien typées et la sélection malgré les
gardes si les bras non gardés couvrent. `Core/Covered.lean` définit `Certified`,
qui certifie aussi tous les corps et sous-expressions ; les environnements
protégés incluent les fermetures récursives. P35 exclut `matchFail`/`stuck`
du véritable `eval`, pour tout budget d'un programme clos certifié.
Timeout et erreurs explicites restent permis. La CLI ne construit pas encore
ces dérivations ; ni `--strict` ni `--certify` ne suffisent à invoquer P35.
271 matrices réelles/générées sont comparées à Lean, plus quatre budgets ;
ce pont normalise alias/alternatives mais ne prouve pas leur élaboration.

`CheckResult.warnings` et `LoadResult.warnings` portent les nouveaux diagnostics ;
`Session.warnings` en conserve l'historique du typage, avec fichiers des couches M2.
CLI texte/JSON, REPL et LSP remontent ces avertissements sans changer le runtime
ni la Core IR. `check --strict` les promeut en erreurs et refuse avant export/
certification, y compris dans les dépendances M2 ; le LSP reste non strict.
Prélude et six exemples sans avertissement ; domaines booléens produits contrôlés
aussi par comparaison exhaustive des valeurs d'exécution dans des tests générés.

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
format `certificate/1.1.0` validé par `contracts/schemas/certificate-1.1.0.json`
(lecture 1.0 conservée) :

- les variables locales sont des indices de de Bruijn (0 = lieur le plus proche) ;
- les variables de motif sont des emplacements numérotés (`{"bind": k}`) ;
- les variables de type sont nommées par définition et liées par des listes `forall` ;
- les littéraux portent leur sorte ; les floats finis portent aussi leurs bits binary64.

`load.py` fait l'opération inverse : il valide d'abord le certificat entier, une seule fois, par
`SchemaRegistry` et le schéma de leur version (le JSON Schema est l'unique description de la
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

HYP-028 : `tests/differential/` génère 500 termes fermés bien typés par
exécution Hypothesis, puis compare exactement la dernière définition du
certificat avec le même IR exécuté en Python. Valeurs structurées et erreurs
sont comparées, jamais les timeouts (pas de notion de pas commune aux deux
runtimes). Une mutation volontaire du runtime doit être détectée.
Le job CI des preuves et `validate.sh lean|complet` construisent le binaire
puis imposent `HYPOMNESIS_REQUIRE_LEAN=1` ; les jobs Python sans Lean
peuvent ignorer le différentiel. Voir
[la stratégie](docs/verification/strategie.md) pour le fragment généré.

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

HYP-045 : l'hôte `examples/mechanics/substitution.py` sélectionne un manifeste
M2 de règle ou régression et lie le même symbole `thickness.estimate`, via
PythonBackend, sans changer `demo/programs/mecanique/plaque_plugins.hyp`.
Les contrats sont dérivés des types M2 ; règle et caractéristiques restent
en Hypomnesis, scikit-learn optionnel. Préparation statique sans import du
fournisseur, erreurs explicites, provenance Estimated avec fournisseur/version.
Voir [les commandes et limites](docs/architecture/estimateurs.md#substitution-contractuelle-sans-modifier-le-m1-hyp-045).

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
Les contrats embarqués sont lus et vérifiés une fois par classe/processus,
puis copiés dans chaque nouveau registre. Le registre de ressources
`referencing` est persistant ; ajouter un contrat local ne modifie ni les
autres instances ni le modèle en cache. Les ajouts personnalisés restent
vérifiés, les schémas exposés restent des copies. Redémarrer le processus
après modification des contrats embarqués.

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
incompatibles refusés sans importer un backend piégé.

HYP-043 : `formal/Hypomnesis/Contracts/Json.lean` modélise une frontière
structurelle distincte de la Core IR. Sous `ValTy`, `decode_encode` (P32)
reconstruit la valeur exactement et `encode_conforms` (P33) établit sa
conformité au schéma indépendant. Fragment : int arbitraire, bool, string,
unit, listes, paires, options étiquetées et records nominaux imbriqués.
Les nombres JSON sont rationnels exacts ; integer signifie dénominateur 1.
Les objets exigent toutes les propriétés déclarées, aucune autre et aucun
doublon, indépendamment de leur ordre. Le décodeur retire chaque propriété
consommée et rejette les propriétés restantes ; le nom du record vient du type.

`tests/integration/test_json_contract_model.py` confronte 96 compositions
réelles au modèle : encodage après texte JSON, aller-retour, schémas Draft
2020-12 identiques après résolution non récursive des `$ref`, décodages
valides/invalides, permutations, champs absents/supplémentaires et longueurs
de tableaux. Alias et paramètres concrets testés. Gate Lean obligatoire
en CI et dans `validate.sh lean|complet`.

Limites : pas de preuve du parseur texte ni de raffinement du codec Python.
Le modèle option est une abréviation des deux objets fermés oneOf disjoints.
Binary64, variants généraux, tuples autres que paires et références récursives
restent couverts par les tests HYP-042, pas par P32–P33 ; aucune régression de
leur prise en charge Python n'est introduite.

### CLI structurée pour les agents (HYP-133)

Guide court : [cli-agents.md](docs/outillage/cli-agents.md). Le catalogue HYP-080
reste dans Codegen, sans duplication ni import inverse dans le moteur :
`Catalogue.to_json()` ajoute la version et valide language-catalogue/1.0.0 ;
la CLI `hypomnesis-codegen decrire --format json` l'utilise. Markdown et
instantanés de prompts inchangés. `check --format json` garde diagnostics/1.0.0.

`hypomnesis lancer --format json` émet cli-execution/1.0.0 : version, mode,
status ok/stopped/error, rapport (dont étapes, connaissances, commandes,
journal, trace) et diagnostics. Sérialisation JSON stricte sans `default=str`,
validation du véritable document JSON avant émission. Les impressions Python
de l'exécution vont sur stderr ; données seules sur stdout. Un arrêt budget
donne status stopped/code 1 avec rapport partiel ; un refus donne error/rapport
nul. Le code 0 n'implique pas que chaque commande a réussi. Le mode texte
reste inchangé et conserve ses codes ; --env mal formé est désormais refusé
explicitement plutôt qu'ignoré. Aucune permission implicite ni invite ajoutée.

Tests réels : `tests/integration/test_agent_cli.py` utilise uniquement le
catalogue JSON pour produire un M1, provoquer/corriger une erreur, vérifier
puis simulate/dry-run ; stdin fermé et tous les documents validés. Tests de
refus structurés, logs d'adaptateur sur stderr et seuil réel 1000/1001 étapes.
Erreurs d'usage Typer : code 2, stderr, stdout vide. Aucun appel LLM.

### Coloration des métadonnées (volet local HYP-151)

Extension VS Code 0.1.1 : scopes dédiés au nom `language` et aux clés de
configuration, contexte équilibré pour records imbriqués, chaînes/commentaires
protégés et absence de débordement sur les records ordinaires. Un tokenizer
TextMate commun sert aux tests Node et à l'Extension Host ; ce dernier lit
la grammaire de la contribution réellement chargée, vérifie association
`.hyp`, activation, scopes du bloc utilisateur et diagnostics LSP.
Guide de rechargement et inspection des scopes dans `editors/vscode/README.md`.
Le parseur et les programmes sont inchangés ; l'arbitrage syntaxique de
HYP-151 demeure humain, distinct de cette correction d'outillage.

## Observabilité (HYP-015/070)

`src/hypomnesis/observability/trace.py` : la classe `Tracer` est une façade au-dessus du SDK
OpenTelemetry (`opentelemetry-sdk`). Chaque instance possède son propre `TracerProvider` (jamais
de `set_tracer_provider` global) avec un `SimpleSpanProcessor(InMemorySpanExporter)` ; `tree()`
et `export()` (clé `trace` de `rapport.json`) sont reconstruits depuis les spans terminés, triés
par début. API : `span(nom, **attributs)` (gestionnaire de contexte ; le parent est la pile
propre au `Tracer`, pas le contexte ambiant), `trace_id`, `spans`, `tree()`, `export()`,
`current_context()`. Le contexte actif et la pile sont des `ContextVar` :
threads et tâches asynchrones ne partagent pas une pile mutable.
Les identifiants sont exportés en hexadécimal (trace 32 caractères, span 16) ;
le `trace_id` est fixé à la création du `Tracer` (générateur d'identifiants dédié). Les valeurs
d'attributs non scalaires simples sont rendues par `repr`, après expurgation
des champs sensibles ; les objets arbitraires ne sont jamais formatés.
Une exception ouvre le statut `error` (`StatusCode.ERROR`) puis est relancée,
sans enregistrer son message ni sa pile bruts (HYP-072).

`trace_context(tracer)` renvoie `{"traceparent": "00-<trace>-<span>-<flags>"}` pour l'enveloppe de
message (§9.6, schéma `envelope-1.0.0.json`) ; hors d'un span, l'identifiant de span est nul et
le drapeau d'échantillonnage éteint. `Tracer(enabled=False)` utilise `NoOpTracerProvider` : aucun
span, aucun effet sur les connaissances (ADR 0005, test `tests/unit/test_trace.py`).
HYP-070 ajoute `TraceConfig`, `Tracer.close()` et le protocole de contexte
pour fermer les providers, y compris après échec. La CLI place le chargement
M2, le parsing/typage M1 et la procédure sous une seule racine `hypomnesis.run`.
`run_procedure(..., tracer=...)` accepte un traceur hôte : celui-ci garde la
responsabilité de le fermer. Si une racine hôte est encore ouverte, appeler
`report.write(out_dir)` après sa fermeture pour inclure cette racine terminée.
Sans racine hôte, le rapport final est écrit automatiquement.

La configuration se fait par API ou par environnement, également en CLI :

```bash
HYPOMNESIS_TELEMETRY=0 hypomnesis lancer demo/languages/mecanique demo/programs/mecanique/plaque_120x80.hyp
HYPOMNESIS_OTLP_TRACES_ENDPOINT=http://127.0.0.1:4318/v1/traces \
  HYPOMNESIS_TELEMETRY_TIMEOUT=3 \
  hypomnesis lancer demo/languages/mecanique demo/programs/mecanique/plaque_120x80.hyp
```

Seuls `0`/`1` sont admis pour l'activation ; délai positif fini en secondes.
Sans endpoint, aucun export réseau. Installer `.[telemetry]` pour OTLP HTTP
(inclus dans dev pour ses tests). L'exporteur officiel utilise une session
sans proxy d'environnement ni redirection, avec endpoint limité à localhost/
127.0.0.1/::1. Une panne/refus du collecteur est journalisé par OTel et
n'altère pas les résultats symboliques. Le format mémoire du rapport reste
inchangé. Le délai borne chaque requête, pas la durée totale du pipeline.

`trace_context()` sans argument renvoie le contexte actif. Les transports
mémoire/fichier et les lectures de capteurs ajoutent le contexte à une copie
de l'enveloppe sortante si absent, jamais au payload ni à l'objet d'origine.
Le rejeu conserve un contexte déjà enregistré. `Tracer(parent_context=...)`
extrait strictement un parent W3C et propage aussi tracestate. Un capteur
répondant avec son propre contexte distant est lié au span de lecture ;
un contexte distant sémantiquement invalide est signalé puis ignoré, sans
réinterpréter son payload. Le contexte est de l'observabilité, pas une preuve.

Les appels purs M2 sont déclarés dans `language.tracing` (fonction/opération) :
instrumentation par identité de valeur dans `Interpreter.apply`, conservant
partiels, aliases, champs de records et appels terminaux. Aucun nom métier
n'est codé dans le moteur. Seules les fonctions explicitement configurées
produisent ces spans, sans arguments/résultats. Les appels inexistants ne
produisent aucun span fictif ; le lot sans LLM n'émet pas `llm.transcribe`.
L'autorisation est distincte de l'exécution réelle dans Dispatcher ; le
dry-run ne produit donc pas `actuator.execute`, et une commande dédupliquée
ne rejoue ni exécution ni observation. Les vérifications de schéma/solveur,
enregistrement/révision de connaissances et observation post-action sont
instrumentés aux frontières réelles.

Tests `test_trace_pipeline.py` : vrai protobuf OTLP reçu sur HTTP local,
refus/redirection du collecteur, arbre du MVP sauvegardé, concurrence,
propagation/rejeu et résultat identique avec ou sans export. Aucun service
tiers n'est contacté par ces tests.

### Métriques (HYP-071)

`observability/metrics.py` utilise un `MeterProvider` privé par `Tracer`,
sans fournisseur global. `tracer.metrics.snapshot()` expose les données du
lecteur mémoire SDK ; elles restent consultables après `close()`. Le format
historique de `rapport.json` est inchangé. Les ressources OTLP portent
`service.name=hypomnesis` et une identité standard `service.instance.id`
UUID indépendante par fournisseur SDK, stable pendant sa vie. Ce n'est
pas un identifiant de run/trace/message ; elle distingue les producteurs
de compteurs simultanés (ADR 0019). Les lecteurs mémoire et OTLP sont
cumulatifs. Les labels applicatifs restent fermés, mais cette dimension
technique augmente explicitement la cardinalité ; avec une CLI courte,
elle peut créer de nouvelles séries à chaque lancement.

```bash
HYPOMNESIS_OTLP_TRACES_ENDPOINT=http://127.0.0.1:4318/v1/traces \
  HYPOMNESIS_OTLP_METRICS_ENDPOINT=http://127.0.0.1:4318/v1/metrics \
  hypomnesis lancer demo/languages/mecanique demo/programs/mecanique/plaque_120x80.hyp
```

Le second endpoint est indépendant du premier, également validé en API
(`TraceConfig.otlp_metrics_endpoint`). Même extra `telemetry`, même
restriction locale et même session sans proxy/redirection. Exporteur
officiel périodique (5 s), export final et arrêt du lecteur à la fermeture.
Un échec de construction du traceur ferme les fournisseurs déjà créés.
`HYPOMNESIS_TELEMETRY=0` désactive aussi les métriques et leurs exports.

Les dix métriques non conditionnelles du §12.4 sont produites par les
opérations auxquelles elles s'appliquent, sans incrément factice :

- Fin de `hypomnesis.run` : compteur des exécutions et durée.
- Appels réels de capteur/actionneur/estimateur/solveur/validateur/transcripteur :
  compteur et histogramme par catégorie, pas par identifiant de plugin.
- Validation JSON : compteur `accepted`, `rejected` ou `error`.
- Solveur : histogramme ; estimateur : compteur.
- Refus effectif d'un `LanguageValidator` ou du checker d'assignation :
  rejet de validateur. Une erreur logicielle du checker n'est pas une
  réfutation ; elle reste une erreur d'appel.
- Commande : compteur à l'état final, dédupliqué par le Dispatcher.
  `Failed`, `TimedOut` et `UnknownOutcome` comptent aussi comme échecs ;
  refus d'autorisation, dry-run et simulation ne sont pas des échecs d'envoi.

Durées en secondes avec buckets adaptés de 1 ms à 60 s. Les seuls labels
admis sont `status`, `kind`, `mode`, `state`, `direction`, chacun avec une
énumération fermée. Toute autre clé ou valeur est refusée, même un
identifiant passé comme `status`. Aucun message, trace, connaissance,
schéma, résultat, exception ni nom libre de plugin dans les labels.

`hypomnesis_llm_tokens_total` n'est enregistré que si une mesure existe :
`tracer.metrics.record("hypomnesis_llm_tokens_total", n, direction="input")`
(ou `output`), avec entier non négatif. Aucun appel LLM ni consommation
inventée : la fixture enregistrée du MVP n'émet pas ce compteur.
Les tests MVP vérifient succès, refus de permission et vraie exception
d'écriture ; les tests de validateur couvrent séparément les réfutations.
Une exécution réussie n'émet pas artificiellement un rejet ou un échec.
`test_metrics.py` vérifie également SDK, protobuf OTLP reçu localement,
isolement, désactivation, fermeture et erreurs/refus/redirections d'export.

### Stack locale (HYP-073)

`monitoring/docker-compose.yml` déploie les images officielles ARM64 fixées
par version et digest : Collector contrib 0.164.0, Prometheus 3.15.1,
Grafana OSS 13.3.0 et Tempo 2.10.10 (branche 2.x single-binary locale).
Ports loopback, limites CPU/mémoire et volumes persistants. Sources Grafana
provisionnées, sans cloud, LLM, Loki ni tableaux de bord P2.

Prometheus conserve le label technique `instance` du producteur
(`honor_labels: true`), plutôt que de le remplacer par l'adresse du
Collector. Pas de conversion DELTA : elle ne corrige pas à elle seule
la concurrence de producteurs indistinguables. Les histogrammes SDK sont
transmis sans reconstruction ni modification des horodatages.

`.venv/bin/python -m monitoring.verify --timeout 120` lance deux vrais MVP
séquentiels puis deux simultanés. Via les proxies des sources Grafana, il
exige tous les spans attendus et l'égalité des compteurs, comptes/sommes
et buckets des histogrammes avec l'instantané SDK persisté par chaque MVP
(`sdk_metrics`). Les producteurs sont vérifiés séparément ; l'expiration
d'anciennes séries ne fausse donc pas le contrôle. Seul un succès écrit
le nouveau bilan de vérification.

L'identité par producteur a un coût de cardinalité accepté. Expiration du
cache Collector à cinq minutes, historique Prometheus à un jour/256 Mo,
traces Tempo à une heure. La somme des compteurs visibles n'est pas un
registre durable d'exécutions depuis l'installation. Cette stack locale
avec Grafana anonyme ne constitue pas un déploiement de production.
Commandes, URLs et limites : `monitoring/README.md`.

### Logs JSON et expurgation (HYP-072)

`observability/logging.py` utilise la bibliothèque standard `logging` :
un logger privé et un handler JSON sur stderr par traceur, sans provider
global ni modification des handlers de l'application. Les fins d'opérations,
leurs erreurs, les contextes invalides et les états finaux des commandes
produisent des événements structurés. `operation.completed`,
`operation.failed` et `actuator.command.finished` ne contiennent ni
arguments, ni résultats métier, ni payload de commande.

Chaque événement actif porte `run_id`, `trace_id` et `span_id`. Le `run_id`
est distinct du trace id : deux exécutions sous le même parent W3C gardent
des identités d'exécution différentes. ContextVar isole aussi la corrélation
des logs entre threads et tâches asynchrones. Le stdout JSON de la CLI
reste exclusivement le résultat sémantique ; `Effect.note` et les diagnostics
du programme ne sont pas altérés par le filtre de télémétrie.

```bash
# Désactiver les logs seulement, en gardant traces/métriques.
HYPOMNESIS_LOGS=0 hypomnesis lancer demo/languages/mecanique demo/programs/mecanique/plaque_120x80.hyp
```

Activation par défaut ; seuls `0`/`1` sont admis. API :
`TraceConfig(logs_enabled=False)`. `HYPOMNESIS_TELEMETRY=0` coupe les trois
signaux. Pour un hôte : `Tracer(log_stream=flux, log_policy=RedactionPolicy(
additional_sensitive_keys=frozenset({"plugin"})))`. Le flux reste propriété
de l'hôte et n'est pas fermé. Les événements personnalisés passent par
`log_event("mon.evenement", **champs)` dans un span actif.

Les logs n'acceptent qu'une liste positive de métadonnées et des scalaires
bornés ; les champs inconnus sont omis et signalés par `redacted=true`.
Les prompts/messages, payloads, entrées/sorties, données personnelles et
secrets connus deviennent `[REDACTED]`, y compris dans les structures
imbriquées. La récursion est bornée, les cycles et valeurs non finies
restent sérialisables. Aucun `repr` d'objet ni `str` d'exception pour le log.
La politique hôte permet de **renforcer**, pas d'enlever, ces protections.
Les noms/versions de plugins et autres métadonnées déclarées par l'hôte
restent des métadonnées de confiance : ce filtre n'est pas une analyse DLP
d'un texte arbitraire placé délibérément dans un nom de plugin.

Les traces conservent leur format de rapport, avec expurgation des champs
sensibles lors de l'ouverture du span. Les événements d'exception ne
gardent que le type et des marqueurs expurgés ; le statut ne contient plus
le message. L'exception originale est relancée sans modification.
L'API SDK brute `span.set_attribute` reste sous la responsabilité de l'hôte :
ne pas y ajouter explicitement des prompts ou données personnelles.

Les exporteurs restent ceux du SDK officiel ; une portée de diagnostic
expurge leurs messages/arguments, corps HTTP et traceback pour les exports
de cet hôte seulement, sans reconfigurer les autres usages d'OTel.
Les erreurs conservent signal, run/trace et code HTTP (également les 3xx
refusés). Un export périodique hors span garde run/trace sans span fictif.
Des handlers/prints installés directement par un adaptateur ou par l'hôte
ne sont pas des événements de cette façade et ne passent pas par son filtre.

`test_structured_logging.py` vérifie absence de prompt/données brutes,
exceptions dont `__str__` est interdit, corps de refus HTTP réel pour traces
et métriques, concurrence, désactivation, renforcement, cycles, stdout CLI
et invariance des résultats/connaissances/commandes.

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
HYP-067 : `formal/Hypomnesis/Effects/Handlers.lean` modélise les opérations
à continuations typées et état hôte, avec budget. Dry-run/simulation sans
handoff production, effacement des trois handlers vers un même fold et
congruence sous réponses/transitions égales sont audités. Les tests comparent
24 décisions avec le vrai dispatcher et exigent une IR identique dans les
trois modes, y compris les branches dépendant des réponses. Le job des
preuves et `validate.sh lean|complet` imposent les modèles exécutables ;
les jobs Python sans Lean peuvent les ignorer explicitement.
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

HYP-066 : `Effects/Commands.lean` raffine ce modèle par la garde de relance,
les pertes de réponse et les doublons d'entrée conservant le cache.
`non_idempotent_at_most_once`, `attempts_bounded`, `terminal_absorbing` et
`Execution.toRun` sont audités. Le test compare aussi 384 gardes et les états
terminaux. La garantie est locale au dispatcher séquentiel et à son journal
conservé, pas une exécution physique unique après duplication aval ou
redémarrage. Détails : [commandes.md](docs/verification/commandes.md).

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

## Scénario mécanique (HYP-090)

HYP-090 : `python -m examples.mechanics.mvp` assemble le pipeline mécanique
à dix étapes avec fixture Codegen, ingestion Hypothesis/MetaVar, sklearn
versionné, modèle Z3 typé revérifié, LanguageValidator et export réel via
dispatcher/FileTransport. Session M2 de confiance séparée du candidat ;
normalisation et règles dans M2. Rapport JSON, journal, graphe et spans
persistés, y compris les refus. Guide :
[scenario-mecanique.md](docs/architecture/scenario-mecanique.md).

## Publication DSL (HYP-080)

HYP-080 : le catalogue Codegen publie également les contrats et modules
adaptateurs déclarés du langage sélectionné. `decrire --plugin` ajoute les
métadonnées d'extensions fournies par l'hôte, signatures et permissions
requises, sans importer leurs backends. Tests d'exhaustivité des valeurs
publiques de Mechanics et budget mesuré <= 16 Kio UTF-8.

HYP-081 : `translation.check` utilise `load_language(execute=False)` et
`Session.check`, sans évaluer M2/M1 ; simulation uniquement sur callback
explicite. `max_repairs` entier naturel strict (pas bool), diagnostics
conservés pour toutes les tentatives. Fixture MVP et refus de Python
testés sans réseau.

HYP-082 : `Codegen.hypotheses.capture_input` valide d'abord la donnée fermée,
puis produit des faits Hypothesis et des MetaVar pour les options absentes,
avec un rapport des chemins/types. `run_procedure(generated=True)` dégrade
conservativement tous les Record, sans modifier Observe. CLI --demande,
--generated et banc Codegen propagent cette origine ; aucun import inverse.

## Certification CLI (HYP-027)

HYP-027 : `check --certify` appelle le checker Lean avec découverte explicite
et délai fini. `_load_files` renvoie la session réellement chargée pour ne
pas certifier un prélude vide après une entrée de langage. Le JSON final
attend la fin du contrôle. Tests d'élaboration falsifiée et couverture
explicite des six exemples : tous acceptés, chacun via checker et CLI.
Le validateur rebâtit le checker avant de lancer ces tests. Les alternatives
racines deviennent des chaînes de case, sans modifier le noyau ; signatures
de variables par slot compatibles, garde fausse vers le cas suivant (pas
vers l'autre alternative). Alternatives imbriquées et alias restent refusés.
Guide : [certification.md](docs/verification/certification.md).

HYP-021 : les records sont des données nominales à constructeur unique,
portant un produit terminé par unit (`Core/Records.lean`). Construction,
projection et mise à jour héritent des preuves du noyau ; les théorèmes
de sûreté portent sur les opérations appliquées, pas seulement leurs lambdas.
Le décodeur préserve l'ordre d'évaluation source (base évaluée une fois),
les champs non modifiés et les emplacements des variables des motifs partiels,
même permutés ou sous une garde. Champs inconnus, doublons, manques, mauvais
types et confusion nominale sont refusés ; chaque définition émise est comparée
à son annotation, même si elle n'est jamais utilisée. L'exemple deposit prouve
150 et le propriétaire inchangé, encodé en points de code : les strings
natives étaient encore hors fragment à cette étape. Aucune preuve complète
de raffinement du décodeur/Python revendiquée.

HYP-150 : Float Lean 4.35 possède un modèle logique binary64 pour les quatre
opérations arithmétiques couvertes. String reste Unicode. BinOp fixe domaines
et résultats ; le certificat ne peut inventer une signature. Les comparaisons
d'ordre suivent le compare total Python, égalité IEEE distincte pour NaN.
Division/modulo entiers : tdiv/tmod (vers zéro), zéro donne Res.error ; failwith
est également une erreur explicite. P1–P7 sont étendus, evalOp_ty audité (P24).
L'audit ajoute Classical.choice du modèle Float standard aux dépendances
propext/Quot.sound, conformément à la politique existante, sans axiome maison.
Le format 1.1 porte les bits des littéraux, y compris -0.0 ; concordance/finis/
bornes contrôlés dans les deux lecteurs. Le schéma 1.0 reste immuable.

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

Le format `problem/1.1.0` est un JSON fermé et versionné : chaque nombre est une
paire d'entiers numérateur/dénominateur positif. Schéma puis constructeurs assurent
respectivement validation structurelle et sémantique. Z3 continue de résoudre
uniquement la partie numérique ; les transitions ne sont pas un certificat
d'exécutabilité. Voir [le guide](docs/architecture/problem-ir.md).

HYP-052 : domaines real/int/bool explicites ; lecture JSON 1.0 conservée
(réels historiques), écriture 1.1. Les booléens ne valent 0/1 que dans les
contraintes linéaires. Z3 rend Fraction/int/bool, durée et raison d'unknown,
avec délai configurable positif. Le noyau revérifie le modèle indépendamment
du champ violations du plugin. `Problem.typed_problem` et `Effect.solve_typed`
retournent `Problem.solution` nominal, statuts distincts et rationnels exacts.
`Effect.solve` reste compatible (projection float, unsat/unknown réunis).
Ni optimalité ni unsat ne disposent d'un certificat Lean. Pas de nouveau
natif/Core IR ; exemple M1 `demo/programs/solveur/domaines.hyp`.

HYP-053 : `formal/Hypomnesis/Problem/Check.lean` formalise les domaines
real/int/bool, bornes, choix discrets et sommes linéaires en rationnels
exacts. Relation inductive et évaluateur sont corrects/complets l'un par
rapport à l'autre ; le vérificateur est correct/complet pour la satisfaction
des domaines et contraintes (P27–P28, quatre théorèmes audités).
Les tests comparent 413 cas Python/Lean, dont 24 vrais modèles Z3 et leurs
altérations, avec gate obligatoire en CI des preuves et validate.sh lean/complet.
Les deux opérations Solve refusent un modèle faux avant reprise d'une
continuation qui enregistrerait un fait Derived. Aucune promotion automatique.
Le runtime conserve check_assignment ; traduction des tests et fidélité
Python sont testées, pas prouvées. Objectif et planification ne participent
pas à ce vérificateur de faisabilité.

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
