# Propriétés vérifiables du cahier des charges

- **Date :** 2026-11-03
- **Source :** [cahier des charges v0.2](../specification/cahier-des-charges-v0.2.md)
- **Preuves :** [`formal/`](../../formal/) (Lean 4.35, sans Mathlib)
- **Stratégie :** [strategie.md](strategie.md)

Ce document relit le cahier des charges section par section et classe chaque exigence selon
la manière dont on peut en établir la validité.

| Symbole | Signification |
|---|---|
| ✅ | **prouvé** en Lean, sans `sorry`, sur le fragment formalisé |
| 🎯 | **prouvable** : énoncé fixé, preuve planifiée (phase indiquée) |
| 🧪 | **testable seulement** : tests de propriétés, tests différentiels |
| ⛔ | **hors du champ formel** : dépend du monde physique, d'un modèle statistique ou d'un jugement humain |

---

## 1. Ce qui est déjà prouvé

| # | Théorème (Lean) | Énoncé | Exigences couvertes |
|---|---|---|---|
| P1 | `Core.eval_safe` | un terme bien typé, évalué dans un environnement bien typé, rend une valeur du type annoncé, épuise son budget ou échoue au filtrage (`Match_failure`) ; **il ne se bloque jamais** | §4.1, §16.4 « erreurs de types détectées avant exécution », H2 |
| P2 | `Core.closed_never_stuck` | corollaire pour les programmes clos | idem |
| P3 | `Core.typeOf_sound` | le vérificateur Lean n'accepte que des termes dérivables ; `check --certify` exige cette acceptation dans le fragment couvert | §13.2, §14.3 (garantie sur le terme traduit, pas raffinement Python complet) |
| P4 | `Core.typeOf_complete` | il accepte tous les termes dérivables | §13.2 |
| P5 | `Core.hasType_unique` | un terme élaboré a au plus un type | §13.4 (signatures canoniques) |
| P6 | instance `Decidable (HasType Γ e t)` | le typage du fragment est décidable | §13.4 « détecter les incompatibilités avant l'exécution » |
| P7 | `Core.eval_fuel_mono` | un budget ne fait que borner le calcul : tout budget suffisant donne **le même** résultat | §11 « budgets de calcul, limites d'itération » |
| P8 | `eval` est une fonction Lean | déterminisme de l'évaluation | §4.1 (pureté), §9.5 (reproductibilité) |
| P9 | `Epistemics.Prov.eval_subst` | réviser (substituer des observations) commute avec toute lecture de la provenance | §7.2, §7.3, H4 |
| P10 | `Epistemics.holds_after_retract` | après retrait d'une observation, une conclusion tient si et seulement si elle tient avec cette observation fausse | §7.3 étapes 1 à 3 |
| P11 | `Epistemics.retract_unrelated` | une conclusion qui ne dépend pas d'une observation n'est pas affectée par son retrait (**localité de la révision**) | §7.3 étape 1, H4 |
| P12 | `Epistemics.support_mono` | dégrader le support d'une observation ne peut pas améliorer celui d'une conclusion | §7.1, §14.4 (le LLM ne peut pas « blanchir » une valeur) |
| P13 | `Epistemics.conjunction_no_stronger` | dériver d'une estimation donne au mieux une estimation | §7.1 |
| P14 | `Core.matchPat_sound` | un motif bien typé qui filtre une valeur bien typée lie des valeurs des types annoncés | §4.1 (filtrage) |
| P15 | `Core.patTypeOf_sound`, `patTypeOf_complete` | le typage des motifs est décidé exactement par le vérificateur | §13.2 |
| P16 | `Examples.program_typed` | un programme réel (longueur de liste) est typé **par calcul**, au moyen du vérificateur prouvé | démonstration du mécanisme de certificat |
| P17 | `Effects.dispatch_ordered` | chaque occurrence de dispatch, relances comprises, possède une validation puis une autorisation antérieures dans le journal de la même commande | §9.8, §16.4 ; modèle de traces HYP-065 |
| P18 | `Effects.dispatch_permitted`, `no_dispatch_without_permission` | aucun dispatch dans le modèle sans permission hôte accordée à la commande | §16.4 ; modèle HYP-065 |
| P19 | `Effects.non_idempotent_at_most_once`, `attempts_bounded` | au plus un handoff local non idempotent ; toutes les tentatives sont bornées par la politique positive, pertes et doublons d'entrée compris | §9.7, §19 ; modèle HYP-066 à journal conservé |
| P20 | `Effects.terminal_absorbing` | les états terminaux n'ont pas de transition sortante | §9.7 ; automate HYP-066 |
| P21 | `Records.make_typed`, `get_typed`, `update_typed`, `update_checked` | construction, accès et mise à jour de records nominaux sont des formes dérivées typées, acceptées par le vérificateur prouvé | §4.1 ; HYP-021 |
| P22 | `Records.get_never_stuck`, `update_never_stuck` | appliqués à un record clos bien typé et à une nouvelle valeur du type du champ, accès et mise à jour ne se bloquent jamais, quel que soit le budget | §4.1 ; HYP-021 |
| P23 | `Records.Examples.program_typed`, `program_never_stuck`, `deposit_balance`, `deposit_owner` | deposit calcule 150 et conserve le propriétaire (encodé en points de code, pas en string natif) | exemple tour ; HYP-021 |
| P24 | `Core.evalOp_ty` | toute primitive binaire du catalogue fermé, appliquée à des valeurs de son domaine, produit une valeur du type annoncé ou une erreur explicite ; P1–P7 couvrent aussi les flottants, chaînes et erreurs | §4.1 ; HYP-150, pas de raffinement Python complet |
| P25 | `Effects.Handlers.dry_run_no_dispatch`, `simulation_no_dispatch`, `dry_action_unchanged` | pour tout arbre d'effets typé, état hôte et budget, dry-run et simulation ne passent aucune commande au callback de production ; une action autorisée en dry-run rend DryRun/None sans modifier l'état hôte | §10.3 ; modèle de handlers HYP-067, callbacks et raffinement Python non prouvés |
| P26 | `Effects.Handlers.handlers_interpret_same_term`, `ordinary_answers_shared`, `equal_answers_equal_results` | les trois modes s'effacent vers le même fold du terme original ; les opérations hors Act partagent les mêmes réponses ; à réponses/transitions hôte identiques, les résultats effacés sont égaux, même avec des continuations qui branchent sur la réponse | §10.3 ; HYP-067, pas d'égalité inconditionnelle entre résultats simulés et réels |
| P27 | `Problem.evalLinear_sound`, `evalLinear_complete` | l'évaluateur linéaire exact et la relation inductive de somme rationnelle décrivent les mêmes valeurs, booléens 0/1 compris | §6 ; projection normalisée de Problem IR, HYP-053 |
| P28 | `Problem.check_sound`, `check_complete` | une affectation est acceptée si et seulement si ses noms sont connus et si elle satisfait tous les domaines typés, bornes, choix et contraintes linéaires | §6 ; modèle HYP-053, correspondance Python testée ; ni optimalité ni unsat |
| P29 | `Revision.candidate_complete`, `invalidated_eq_full`, `revise_incr_eq_full` | l'index inverse augmenté des provenances contenant zéro couvre toute invalidation ; la révision incrémentale donne le même état que l'évaluation exhaustive | §7.3 ; HYP-036, valeurs/contexte génériques inchangés, correspondance Python testée |
| P30 | `Revision.journal_prefix` | toute révision acceptée prolonge exactement le journal précédent sans modifier aucune entrée | §7.3 ; modèle HYP-036, pas une preuve de durabilité SQLite |
| P31 | `Conflicts.no_false_conflict` | tout rapport produit rend incompatibles les assertions actives et les contraintes fonctionnelles/invariants déclarés | §7.1 ; HYP-037, valeurs à égalité décidable et prédicats purs génériques ; pont Python testé |
| P32 | `Contracts.decode_encode` | toute valeur ValTy du fragment structurel fermé est reconstruite exactement après encodage, nom du record et distinction None/Some unit compris | §9.4, §13.4 ; HYP-043, int/bool/string/unit, listes, paires, options et records imbriqués |
| P33 | `Contracts.encode_conforms` | l'encodage d'une valeur ValTy satisfait le schéma produit : types, propriétés requises, aucun champ supplémentaire | §9.4, §13.4 ; HYP-043, objets à champs distincts, ordre des propriétés indifférent |
| P34 | `Coverage.check_sound`, `exhaustive_sound`, `guarded_exhaustive_selects` | un résultat `some true` du calcul par matrices couvre toute valeur bien typée ; la sélection réussit quelles que soient les réponses booléennes des gardes si les bras non gardés couvrent | §4 ; HYP-022, fragment monomorphe, budget épuisé = indéterminé, pas de complétude revendiquée |
| P35 | `Coverage.Certified.typed`, `eval_protected`, `certified_program_no_matchFail` | tout programme clos certifié ne rend ni `matchFail` ni `stuck` dans le véritable `Core.eval`, pour tout budget ; corps et fermetures récursives compris | §4 ; HYP-022, jugement renforcé explicite, timeout/erreur permis, pas encore attaché au pont CLI |
| P36 | `Poly.Ty.subst_var`, `subst_comp`, `subst_congr`, `subst_scoped`, `rename_comp`, `rename_scoped` | identité/composition des substitutions et renommages des monotypes paramétriques ; la substitution conserve les portées si ses images sont bien scopées | §4 ; fondations HYP-023, aucune nouvelle garantie des programmes ou du CLI |
| P37 | `Poly.lift_comp`, `lift_scoped`, `Scheme.subst_comp`, `subst_scoped`, `instantiate_scoped`, `instantiate_subst` | la substitution sous les quantificateurs protège les variables liées ; la bonne portée est préservée et l'instanciation commute avec la substitution extérieure | §4 ; schémas de rang 1, pas encore le jugement de généralisation des termes |
| P38 | `Poly.Signature.constructorType_scoped` | dans une signature paramétrique bien formée, instancier un constructeur avec des arguments bien scopés produit un type bien scopé | §4 ; pas encore une preuve de sûreté des valeurs de données paramétriques |
| P39 | `Poly.Ty.ofCore_subst`, `closed_subst` | la substitution ne change ni les types du fragment historique inclus ni les types paramétriques clos bien scopés | §4 ; inclusion des types seulement, pas un pont des programmes |
| P40 | `Poly.TyEnv.subst_scoped`, `instantiate_scoped`, `instantiate_subst` | les environnements de schémas conservent leurs portées sous substitution ; l'instanciation d'une liaison conserve la portée et commute avec la substitution des types extérieurs | §4 ; brique d'environnement HYP-023, sans jugement de typage des termes ni nouvelle garantie CLI |
| P41 | `Poly.Ty.beq_iff_eq`, `typeOf_sound`, `typeOf_complete`, `hasType_iff_typeOf` | l'égalité booléenne des types reflète l'égalité structurelle ; sous une signature bien formée et un environnement bien scopé, le checker décide exactement le jugement déclaratif polymorphe | §4 ; termes annotés explicitement et let-polymorphe, sans préservation opérationnelle ni branchement CLI |
| P42 | `Poly.PatTy.subst`, `Poly.HasType.subst` | une dérivation polymorphe reste valable après substitution des variables de type dans les types, termes et environnements, si la signature est bien formée et les images de substitution sont bien scopées ; cas, constructeurs et let-polymorphe compris | §4 ; préservation statique HYP-023, sans sûreté de l'évaluateur ni branchement CLI |
| P43 | `Poly.Expr.erase_subst`, `eval_erase_subst`, `eval_erase_subst_ne_stuck` | l'effacement vers le Core est invariant par substitution de types ; par conséquent, une propriété de sûreté déjà établie sur l'exécution Core est conservée après toute substitution | §4 ; invariant opérationnel utile au pont HYP-023, ne prouve pas à lui seul la sûreté d'un terme polymorphe |
| P44 | `Poly.HasType.erase_runtimeFragment`, `eval_safe_runtimeFragment`, `eval_safe_monoLetRuntimeFragment`, `eval_safe_capturedIntLambdaApp`, `eval_safe_recursiveCountdownApplication`, `eval_safe_pairPatternCase` | les constantes, variables mono-instanciées, conditions, produits, projections, opérations binaires, `let` monomorphes, fermetures monomorphes/récursives et motifs scalaires/de paires s'effacent en termes Core typés, dont l'évaluation est sûre à tout fuel | §4 ; relation d'environnement limitée aux schémas d'arité zéro ; pour les fermetures, l'effacement du corps doit coïncider ; motifs de constructeurs, données paramétriques et `let` polymorphes multi-instanciés restent hors preuve |
| P45 | `Poly.TypingExamples.identity_polymorphic_let_is_safe_at_fuel_20` | l'exemple concret du `let` identité utilisé aux types `int` et `bool` donne à fuel 20 une paire Core dont les deux composantes satisfont leur relation de valeurs | §4 ; régression d'exécution à fuel fixé, pas une preuve générale de sûreté des schémas polymorphes |
| P46 | `Poly.TypingExamples.generic_map_has_type`, `generic_map_runs_with_two_instances` | un encodage récursif polymorphe de `List.map` reçoit son type exact et s'exécute dans le même programme aux instanciations `int → bool` et `bool → int` | §4 ; exemple Lean autonome sur la signature paramétrique de liste, pas encore le décodeur du certificat ni le corps exact du prélude Python |

**Application aux programmes réels (HYP-026).** L'exécutable `hypomnesis-check` applique `typeOf`
(P3) aux certificats émis par le compilateur Python. Pour un programme accepté, P1 s'applique
donc au programme traduit : il ne peut pas se bloquer dans la sémantique de référence. Ce qui
reste de confiance : la fidélité de la traduction (décodeur) et celle de l'interpréteur Python à
la sémantique Lean, couverte par les tests différentiels (HYP-028).

**Pont CLI (HYP-027).** `hypomnesis check --certify` émet et vérifie le certificat,
sans exécuter le programme, avec refus explicite hors fragment et délai fini.
La CI teste ce chemin et refuse une élaboration falsifiée. L'export seul ne
certifie rien. Les six exemples actuels sont acceptés par le checker et le pont
CLI en CI, sans exemption ; une élaboration falsifiée est refusée.
Les alternatives racines sont traduites en case, avec gardes sans réessai.
Voir [certification.md](certification.md) pour les limites du fragment.

**Fragment couvert** (`formal/Hypomnesis/Core/Syntax.lean`) :
- types `int`, `bool`, `unit`, `float` binary64, `string` Unicode, fonctions, produits et **types de données** (variants, listes),
  monomorphisés dans une signature ;
- lambdas annotées, récursion (`fix` ↔ `LetRec`), `let`, `if` élaboré, paires ;
- constructeurs et **filtrage** (`case` en chaîne binaire, `fail`), motifs joker, variable,
  littéral, paire, constructeur ;
- catalogue fermé de primitives entières, flottantes et chaînes ;
- erreurs de primitives (`Res.error`), distinctes de stuck et Match_failure ;
- records nominaux comme données à constructeur unique : construction, accès,
  mise à jour et motifs partiels ; mêmes P1–P7, sans changer le noyau.

Ne sont **pas encore** couverts : réels mathématiques et primitives hors catalogue,
élaboration des motifs alternatifs imbriqués et alias, certification automatique
d'exhaustivité par la CLI et polymorphisme (F2).

**Fondations HYP-023 (en cours).** P36–P40 portent sur l'algèbre des types
et les environnements de schémas dans `Core/PolyTypes.lean`. P41 prouve la
correction et la complétude du vérificateur de termes de `Core/PolyTyping.lean`
par rapport à son jugement déclaratif, sous les préconditions de portée explicites.
P42 prouve la préservation statique par substitution de types, y compris les
liaisons `let` polymorphes, les constructeurs et les contextes de motifs. Les
régressions couvrent un `let` identité instancié à int et bool, un couple de
variables de type ouvertes spécialisées en int/bool, ainsi que des refus d'arité
et de valeur incompatibles. Le pont vers l'évaluateur, le décodeur/CLI et le vrai
corps de `List.map` restent à prouver ou à brancher. Le CLI historique continue
à monomorphiser.

**Exhaustivité (HYP-022, F1c).** P34 prouve le calcul positif par matrices ;
P35 ajoute un jugement `Certified` qui exige la couverture et certifie tous
les corps, y compris les fermetures récursives. La sélection sous gardes est
prouvée séparément de leur évaluation. Le corollaire programme entier
suppose la dérivation renforcée : `typeOf`, `--strict` et `--certify` ne la
produisent pas encore. Le corpus Python/Lean compare 271 matrices réelles
et quatre cas de budget, sans preuve universelle du pont ni de complétude.
Voir [les frontières détaillées](certification.md#exhaustivité-prouvée-et-frontière-cli-hyp-022).

**Frontière JSON (HYP-042, ADR 0010).** La primitive Python `core.to_json`, les conversions
`Json.t` et les codecs/contrats JSON ne font pas partie du catalogue de primitives du fragment
prouvé. `Json.Int` est un constructeur de bibliothèque, pas une forme IR supplémentaire.
HYP-043 ajoute un modèle de frontière **séparé**, `Contracts/Json.lean` :
P32–P33 pour int/bool/string/unit, listes, paires, options étiquetées et
records nominaux imbriqués. Les nombres JSON sont rationnels exacts ;
un nombre intégral tel que `1.0` est admissible pour int, jamais un booléen.
Les schémas représentent tableaux et objets fermés ; l'option abrège les
deux branches oneOf disjointes à tags None/Some. Aucun ordre d'objet n'est exigé
par la conformité et le décodeur restitue les champs dans l'ordre déclaré.

96 compositions concrètes comparent le vrai TypeCodec au modèle : encodage,
résultat du décodage, schéma après résolution des références non récursives
et sondes valides/invalides, avec traversée du véritable texte JSON.
La résolution des alias et paramètres concrets est testée, pas prouvée.
Flottants binary64 (dont les zéros signés et bornes finies), variants généraux,
tuples d'arité autre que deux et `$ref` récursifs restent testés par HYP-042,
**hors P32–P33**. Ni parseur texte, ni raffinement Python complet, ni inclusion
de contrats JSON Schema arbitraires ne sont prouvés.

---

## 2. Relecture du cahier des charges

### §4 — Langage

| Exigence | Propriété | Statut |
|---|---|---|
| fonctions pures, immutabilité | déterminisme ; l'évaluation ne dépend que de l'environnement | ✅ P8 |
| typage avant exécution | sûreté du typage | ✅ P1, P21–P23 (variants, records, `match`) · 🎯 F2 (polymorphisme explicite) |
| types algébriques, filtrage | sûreté étendue aux variants et au filtrage | ✅ P1, P14, P15 |
| | **exhaustivité** : un `match` exhaustif bien typé ne lève jamais `Match_failure` | ✅ P34–P35 pour `Certified` ; rattachement CLI encore absent |
| inférence Hindley-Milner | *correction* de l'inférence : obtenue **sans prouver l'inférence Python**, par vérification de son résultat (certificat) | 🎯 F3 |
| | *principalité* (le type inféré est le plus général) | 🧪 tests différentiels ; preuve en Lean possible mais non prioritaire |
| modules | la résolution de noms préserve le sens : renommer un module ne change pas le résultat | 🎯 F2 |
| macros hygiéniques (§4.4) | pas de capture de variables | 🎯 avec le niveau méta (ADR 0006) : le code typé en HOAS rend l'hygiène structurelle |

### §5 — Métamodèle

| Exigence | Propriété | Statut |
|---|---|---|
| cohérence dimensionnelle (§5.3) | un programme bien typé n'additionne jamais deux grandeurs de dimensions différentes | 🎯 F6 |
| | **invariance par changement d'unités** : une fonction polymorphe en dimension commute avec le changement d'échelle (théorème de paramétricité, Kennedy, POPL 1997) | 🎯 F6 |
| règles, invariants | un invariant déclaré est préservé par chaque transition autorisée | 🎯 F7 (obligation de preuve par domaine) |
| unités hors du noyau | le noyau ne contient aucune constante d'unité | ✅ par construction (vérifiable syntaxiquement) |

### §6 — Extensions

| Exigence | Propriété | Statut |
|---|---|---|
| deux plugins substituables (§16.4, H6) | deux **modèles** d'une même théorie satisfont les mêmes lois ; un programme écrit contre la théorie a le même résultat observable modulo ces lois | 🎯 F7 · 🧪 lois testées par Hypothesis sur chaque modèle |
| solveur externe | le **vérificateur de certificat** est correct : un modèle accepté satisfait les domaines et contraintes | ✅ P27–P28 pour le modèle rationnel ; 🧪 correspondance Python, pas une preuve de Z3, d'optimalité ou d'unsat |
| validateur | un rejet est accompagné d'un contre-exemple vérifiable | 🎯 F5 |

### §7 — Modèle épistémique

| Exigence | Propriété | Statut |
|---|---|---|
| provenance (§7.2) | toute lecture se déduit de la provenance par homomorphisme | ✅ P9 |
| révision (§7.3) | localité, exactitude après retrait | ✅ P10, P11 |
| | **révision incrémentale = recalcul complet** : invalider les candidats donne le même état qu'une évaluation exhaustive ; aucune règle n'est exécutée implicitement | ✅ P29 ; correspondance Python testée, pas de raffinement Python complet |
| | conservation de l'historique : aucune révision ne détruit d'entrée du journal | ✅ P30 ; durabilité du stockage testée séparément |
| statuts (§7.1) | monotonie du support | ✅ P12, P13 |
| conflits | si le moteur signale `Conflict`, les assertions actives ne satisfont pas les contraintes déclarées (pas de faux conflit) | ✅ P31 pour le modèle ; pas de théorie logique universelle ni de raffinement Python complet |

### §8 — Procédural, déclaratif, transitions

| Exigence | Propriété | Statut |
|---|---|---|
| planification sans exécution (§8.3) | un plan validé, exécuté depuis un état qui satisfait ses préconditions, atteint ses postconditions (dans le modèle de transitions) | 🎯 F7 |
| | planifier n'émet aucun effet | 🎯 F5 (propriété de trace) |

### §9–10 — Effets, capteurs, actionneurs

C'est la partie où la preuve a le plus de valeur, car les erreurs y sont physiques.

| Exigence | Propriété | Statut |
|---|---|---|
| noyau pur (§9.1, H5) | **aucun terme du niveau objet n'exécute d'effet** ; il ne peut que le décrire | ✅ par construction pour le fragment (aucun constructeur d'effet) · 🎯 F5 avec la modalité `U` |
| validation avant appel (§9.8, §16.4) | chaque `dispatch(c)` est précédé de `validated(c)` puis `authorized(c)` pour le même `command_id` | ✅ P17 dans le modèle de traces ; correspondance Python documentée/testée, pas de raffinement prouvé |
| action non autorisée (§16.4) | aucune trace ne contient `dispatch(c)` sans permission accordée pour `c` | ✅ P18 dans le modèle de traces ; correspondance Python documentée/testée |
| états des commandes (§9.7) | l'automate n'autorise que les transitions spécifiées ; les états terminaux sont absorbants | ✅ P20 ; transitions Lean/Python comparées exhaustivement |
| doubles commandes (§9.7, §19) | **au plus un handoff local** non idempotent, relances, pertes de réponse et doublons d'entrée compris, avec journal conservé | ✅ P19 dans le modèle HYP-066 ; tests des gardes et Hypothesis côté Python ; pas de garantie physique après duplication aval ou redémarrage |
| simulation, dry-run, production (§10.3) | les trois modes exécutent **le même terme** ; le dry-run n'émet aucun `dispatch` | ✅ P25–P26 dans le modèle à continuations typées ; correspondance Python testée |
| contrats JSON (§9.4, §13.4) | **aller-retour** : `decode (encode v) = some v` ; et `encode v` est conforme à `schemaOf t` dès que `v : t` | ✅ P32–P33 pour le fragment structurel fermé ; reste du codec 🧪 |
| sécurité physique d'une commande | — | ⛔ explicitement hors du champ du JSON Schema (§9.4) ; relève de contraintes métier et de capteurs |

**HYP-065** : portée exacte, hypothèses de confiance et correspondance Python
ligne à ligne dans [dispatch.md](dispatch.md). L'automate Lean et Python est
comparé de manière exécutable sur les 144 paires d'états. Le modèle fixe un
journal par commande et la permission accordée lors de son contrôle ;
il ne certifie ni les callbacks Python, ni le matériel, ni la concurrence.

**HYP-066** : [commandes.md](commandes.md) précise les événements modélisés,
la déduplication d'entrée et la distinction entre handoff local et effet
physique. Prouver « une seule action physique malgré un réseau qui duplique
les requêtes après l'adaptateur » exigerait un contrat récepteur supplémentaire ;
P19 ne revendique pas cette garantie.

### §11 — Boucle épistémologique

| Exigence | Propriété | Statut |
|---|---|---|
| budgets, critères d'arrêt | le budget n'altère pas les résultats | ✅ P7 |
| | la boucle Observer → … → Agir termine sous une limite d'itérations | 🎯 F4 (trivial dès que la boucle est un `fold` borné) |

### §12 — Observabilité

| Exigence | Propriété | Statut |
|---|---|---|
| provenance distincte de la télémétrie (§12.8, ADR 0005) | **non-interférence** : le résultat d'un programme ne dépend pas du traceur | 🎯 F5 |
| métriques, tableaux de bord | — | 🧪 tests d'intégration |

### §13–14 — Compilateur et LLM

| Exigence | Propriété | Statut |
|---|---|---|
| pas de Python arbitraire (§13.5) | la Core IR ne contient aucune construction d'appel hors du registre natif | ✅ par construction (Lean) · ✅ côté Python, vérifié statiquement (ADR 0003, tests) |
| sortie LLM validée avant effet (§14.3) | une sortie LLM n'atteint le runtime qu'au travers de `typeOf` | 🎯 F3 (chaîne de certificats) |
| incertitudes explicites (§14.4) | une valeur issue du LLM a le grade `Hypothesis` et ne peut satisfaire une exigence `[Observed]` | 🎯 F4 (types gradués) · ✅ P12 pour la partie provenance |
| qualité de la transcription | — | ⛔ évaluation empirique |

### §20 — Hypothèses de recherche

| Hypothèse | Apport de la preuve |
|---|---|
| H1 extensibilité | 🎯 F7 : un domaine = une théorie ; ajouter une théorie ne change pas le noyau |
| H2 fiabilité | ✅ en partie : P1–P6 montrent que la chaîne typée exclut toute une classe d'erreurs, ce que la génération directe de code ne garantit pas |
| H3 composition hybride | 🎯 F7 |
| H4 révision | ✅ P9–P11 |
| H5 séparation des effets | 🎯 F5 |
| H6 interopérabilité | ✅ P32–P33 (fragment JSON), 🎯 F7 (modèles de théories) |
| H7 traçabilité | ⛔ pour l'explicabilité ; 🎯 pour la non-interférence |

---

## 3. Feuille de route formelle

| Lot | Contenu | Phase projet |
|---|---|---|
| F1 | variants, records, `match` général, exhaustivité | avec la phase 2 |
| F2 | polymorphisme (termes élaborés à abstraction de type explicite), modules | phase 2–3 |
| F3 | **pont de certificats** Python → Lean, tests différentiels (voir [strategie.md](strategie.md)) | dès que F1 est prêt |
| F4 | moteur épistémique : révision incrémentale, conflits, grades dans le typage | phase 2 |
| F5 | effets : automate de commandes, propriétés de trace, au plus une exécution, aller-retour JSON | phases 3 et 5 |
| F6 | types dimensionnels et invariance par changement d'unités | phase 4 |
| F7 | niveau méta (ADR 0006) : théories, modèles, morphismes | après le MVP |

---

## 4. Amendement adopté du cahier des charges (v0.3)

La [v0.3](../specification/cahier-des-charges-v0.3.md) adopte OBJ-11 et ses
cinq critères suivant l'arbitrage humain HYP-005 du 4 novembre 2026, avec les
axes épistémiques et un suivi des critères. Ces exigences cibles n'étendent
pas la couverture des preuves actuelles.

La v0.2 ne mentionnait pas la vérification formelle. Objectif adopté en v0.3 :

> **OBJ-11 — Vérification formelle.** Le noyau du langage, le vérificateur de types, le moteur
> de révision et le runtime d'effets doivent disposer d'une sémantique de référence en Lean 4. Les
> propriétés de sûreté (typage, budgets, révision, séquencement des effets, au plus une
> exécution) doivent y être prouvées. Le compilateur de production n'est pas prouvé directement : il
> émet des certificats vérifiés par un noyau Lean prouvé correct.

Critères d'acceptation adoptés au §16.4 :

- la sûreté du typage est prouvée pour la Core IR complète du MVP ;
- chaque programme d'exemple produit un certificat accepté par le vérificateur Lean ;
- l'interpréteur Python et la sémantique Lean donnent les mêmes résultats sur un corpus généré ;
- la propriété « validation et autorisation avant tout `dispatch` » est prouvée pour le
  modèle du runtime d'effets ;
- aucune preuve ne contient `sorry`, et les axiomes utilisés sont audités en CI.
