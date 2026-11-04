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
| P3 | `Core.typeOf_sound` | le vérificateur exécutable n'accepte que des termes dérivables | §13.2, §14.3 (une sortie LLM typée est réellement bien typée) |
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

**Application aux programmes réels (HYP-026).** L'exécutable `hypomnesis-check` applique `typeOf`
(P3) aux certificats émis par le compilateur Python. Pour un programme accepté, P1 s'applique
donc au programme traduit : il ne peut pas se bloquer dans la sémantique de référence. Ce qui
reste de confiance : la fidélité de la traduction (décodeur) et celle de l'interpréteur Python à
la sémantique Lean, couverte par les tests différentiels (HYP-028).

**Fragment couvert** (`formal/Hypomnesis/Core/Syntax.lean`) :
- types `int`, `bool`, `unit`, fonctions, produits et **types de données** (variants, listes),
  monomorphisés dans une signature ;
- lambdas annotées, récursion (`fix` ↔ `LetRec`), `let`, `if` élaboré, paires ;
- constructeurs et **filtrage** (`case` en chaîne binaire, `fail`), motifs joker, variable,
  littéral, paire, constructeur ;
- primitives entières.

Ne sont **pas encore** couverts : records (F1b), motifs alternatifs et alias, exhaustivité
(F1c) et polymorphisme (F2).

**Frontière JSON (HYP-042, ADR 0010).** La primitive Python `core.to_json`, les conversions
`Json.t` et les codecs/contrats JSON ne font pas partie des primitives entières du fragment
prouvé. `Json.Int` est un constructeur de bibliothèque, pas une forme IR supplémentaire.
La migration des options étiquetées et des entiers exacts est couverte par les tests
Hypothesis et d'intégration, sans nouvelle garantie Lean revendiquée. Les preuves JSON
dédiées restent HYP-043.

---

## 2. Relecture du cahier des charges

### §4 — Langage

| Exigence | Propriété | Statut |
|---|---|---|
| fonctions pures, immutabilité | déterminisme ; l'évaluation ne dépend que de l'environnement | ✅ P8 |
| typage avant exécution | sûreté du typage | ✅ P1 (fragment) · 🎯 F1–F2 (variants, records, `match`, polymorphisme) |
| types algébriques, filtrage | sûreté étendue aux variants et au filtrage | ✅ P1, P14, P15 |
| | **exhaustivité** : un `match` exhaustif bien typé ne lève jamais `Match_failure` | 🎯 F1c |
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
| solveur externe | le **vérificateur de certificat** est correct : un modèle Z3 accepté satisfait réellement les contraintes | 🎯 F5 (on prouve le vérificateur, pas Z3) |
| validateur | un rejet est accompagné d'un contre-exemple vérifiable | 🎯 F5 |

### §7 — Modèle épistémique

| Exigence | Propriété | Statut |
|---|---|---|
| provenance (§7.2) | toute lecture se déduit de la provenance par homomorphisme | ✅ P9 |
| révision (§7.3) | localité, exactitude après retrait | ✅ P10, P11 |
| | **révision incrémentale = recalcul complet** : invalider puis recalculer les seuls dépendants donne le même état qu'un recalcul de zéro | 🎯 F4 |
| | conservation de l'historique : aucune révision ne détruit d'entrée du journal | 🎯 F4 (journal en ajout seul) |
| statuts (§7.1) | monotonie du support | ✅ P12, P13 |
| conflits | si le moteur signale `Conflict`, `⊥` est réellement dérivable (pas de faux conflit) | 🎯 F4 |

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
| simulation, dry-run, production (§10.3) | les trois modes exécutent **le même terme** ; le dry-run n'émet aucun `dispatch` | 🎯 F5 |
| contrats JSON (§9.4, §13.4) | **aller-retour** : `decode (encode v) = v` ; et `encode v` est conforme à `schemaOf t` dès que `v : t` | 🎯 F5 |
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
| H6 interopérabilité | 🎯 F5 (aller-retour JSON) et F7 (modèles de théories) |
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
