# Le niveau M3 d'Hypomnesis — fondations type-théoriques

- **Statut :** note de conception, ouverte à discussion
- **Date :** 2026-11-03
- **Objet :** définir ce qu'est le méta-métamodèle (M3) d'Hypomnesis, c'est-à-dire le langage
  dans lequel les DSL métiers (M2) sont définis, en l'ancrant dans le λ-calcul, la théorie des
  types, la théorie des modes et une méta-algèbre réflexive.
- **Décision associée :** [ADR 0006](../adr/0006-m3-theorie-des-types-a-deux-niveaux.md) (proposée).

---

## 1. Le problème

Dans l'architecture MDA de l'OMG, les niveaux sont :

| Niveau | Contenu | Exemple Hypomnesis |
|---|---|---|
| M0 | données, objets réels | la plaque n° 42, une lecture de capteur |
| M1 | modèle | « une plaque de 120 × 80 mm, épaisseur inconnue » |
| M2 | métamodèle = définition d'un DSL | `Mechanics` : `Plate`, `has_thickness`, règles, unités |
| M3 | méta-métamodèle | ce dont tout DSL est fait |

Le M3 classique (MOF, Ecore) décrit un métamodèle avec des *classes*, *attributs*,
*associations* et *contraintes OCL*, et se décrit lui-même (« MOF est conforme à MOF »). Pour
Hypomnesis, ce M3 est insuffisant sur cinq points :

1. **Pas de calcul.** Un métamodèle MOF décrit des structures, pas des opérations exécutables,
   des règles d'inférence ni leur sémantique.
2. **Pas d'équations.** On ne peut pas dire que `a * b = b * a` pour les dimensions, ni qu'un
   `Transpiler` préserve le sens.
3. **Une réflexivité informelle.** « MOF décrit MOF » n'est pas un théorème ; poussée naïvement,
   l'autodescription est le paradoxe de Girard (`Type : Type`).
4. **Ni connaissance ni effets.** Statut épistémique, provenance, capteurs et actionneurs
   n'ont pas de place dans le M3 : ils devraient être réinventés par chaque DSL, au mépris de
   l'objectif OBJ-10.
5. **Pas de sémantique pour la substitution.** « Deux plugins derrière la même interface »
   (critère du §16.4) n'a pas de sens précis sans notion de *modèle* d'une théorie.

**Thèse.** Le M3 d'Hypomnesis doit être une **théorie des types**. Les niveaux MDA y
deviennent des niveaux de jugement, la conformité devient le typage, la réflexivité devient
un univers de codes stratifié, et connaissance comme effets deviennent des **modalités**.

---

## 2. Les niveaux MDA comme niveaux de jugement

| MDA | Théorie des types | Jugement | Hypomnesis |
|---|---|---|---|
| M0 | valeurs closes | `⊢ v : A` | valeurs runtime, observations |
| M1 | termes dans un contexte | `Γ ⊢ t : A` | modèles, programmes, connaissances |
| M2 | **signatures** (théories) | `⊢ Σ sig` | DSL : sortes, opérations, règles, lois |
| M3 | **cadre logique** | règles qui définissent `Σ sig` | le noyau |

« Conformité » au sens MOF signifie ici :

- un modèle M1 est *conforme* à un DSL M2 si et seulement si `Σ; Γ ⊢ t : A` est dérivable ;
- un DSL M2 est *bien formé* si et seulement si `⊢ Σ sig` est dérivable dans le M3.

Le M3 n'est donc pas un « métamodèle de plus » : c'est **l'ensemble des règles de formation
des signatures**. C'est l'idée des cadres logiques (LF, Harper–Honsell–Plotkin 1993), où l'on
définit une logique en écrivant une signature, selon le principe *judgments as types*.

---

## 3. Le λ-calcul comme substrat : deux niveaux

### 3.1 Pourquoi deux niveaux

Il y a deux besoins contradictoires :

- **Côté méta** (définir des théories, des règles, des preuves, des transformations), il faut
  des types dépendants (une sorte `Hom a b`, une quantité indexée par une dimension), la
  totalité et la cohérence logique.
- **Côté objet** (programmes métiers, orchestration, appels de plugins), il faut la récursion
  générale, des effets et une inférence simple, adaptée aux LLM : c'est le noyau ML
  implémenté en phase 1.

La théorie des types à deux niveaux (2LTT : Annenkov–Capriotti–Kraus–Sattler ; Kovács,
ICFP 2022 pour son usage en compilation étagée) répond exactement à ce besoin :

```text
┌──────────────────────────────────────────────────────────────┐
│ NIVEAU MÉTA (M3/M2)  λΠ dépendant, total, cohérent           │
│   théories, sortes, lois, règles, preuves = provenance,       │
│   morphismes de théories, codes de programmes objet          │
├───────────────────────── ⇑ Code / staging ───────────────────┤
│ NIVEAU OBJET (M1)    λ-calcul ML (HM), pur, récursion        │
│   = Core IR actuelle (ADR 0002), inchangée                   │
└──────────────────────────────────────────────────────────────┘
```

Le niveau méta manipule les programmes objet comme des valeurs typées (`⇑A`, le code d'un
programme objet de type `A`) et les produit par étagement (*staging*). Le niveau méta
disparaît à la compilation : le runtime n'exécute que la Core IR.

**Conséquence importante :** le travail de la phase 1 n'est pas remis en cause. Il devient
le *niveau objet*.

### 3.2 Choix du calcul méta

| Option | Forces | Faiblesses |
|---|---|---|
| **A. Théories algébriques généralisées** (GAT, Cartmell 1986) | sortes dépendantes, opérations, équations ; sémantique catégorique claire ; la théorie des GAT est elle-même une GAT ; outillage existant (GATlab/Catlab) | pas de lieurs : on ne peut pas écrire une règle qui introduit une variable |
| **B. λΠ-calcul modulo réécriture** (LF étendu ; Cousineau–Dowek 2007, Dedukti) | lieurs (HOAS), jugements, règles et preuves dans un même cadre ; équations calculatoires par réécriture ; conçu pour faire **interopérer** des logiques hétérogènes | confluence et terminaison des règles de réécriture à vérifier |
| **C. MLTT complète** (univers, familles inductives) | expressivité maximale | noyau lourd, contraire au principe de noyau minimal (§1.2) |

**Recommandation : B comme noyau, A comme sous-langage de surface.** Une GAT est une
signature λΠ sans lieurs. La plupart des DSL métiers s'écriront donc en style « GAT », plus
lisible, et seuls les domaines qui en ont besoin (règles avec quantificateurs, transitions,
définition de logiques) utiliseront les lieurs. L'objectif d'interopérabilité de Dedukti
recoupe directement H6.

---

## 4. Théorie des types : connaissances, inconnues et capacités

### 4.1 Un DSL est une signature

Esquisse de syntaxe, illustrative et non implémentée, qui reste proche des signatures de
modules OCaml :

```ocaml
theory Mechanics (Q : Quantity) = sig
  sort plate
  sort material

  op width     : plate -> Q.q Q.length
  op height    : plate -> Q.q Q.length
  op thickness : plate -> Q.q Q.length          (* peut rester inconnue *)
  rel has_material : plate -> material -> prop

  op area : plate -> Q.q (Q.length * Q.length)
  law area_def : area p = Q.mul (width p) (height p)

  rule rigid : thickness p >= Q.mm 3.0 -> has_material p steel -> rigid p
end
```

- `sort` déclare une sorte : un concept (§5.1).
- `op` et `rel` déclarent des opérations et des relations (§5.2) ; une relation est une
  famille de types à valeur dans `prop`.
- `law` est une équation, orientée en règle de réécriture.
- `rule` est une règle d'inférence : un constructeur de preuves.

La continuité avec ML est voulue : **une signature de module est déjà une théorie sans
équations**, une structure en est un modèle, et un foncteur est un modèle paramétré. Le style
*tagless-final* (Carette–Kiselyov–Shan, JFP 2009) montre que cette lecture est praticable en
OCaml dès aujourd'hui. Il n'y a donc pas de nouveaux mots-clés *par domaine* : seuls `sort`,
`op`, `law`, `rule` et `theory` appartiennent au M3.

### 4.2 Curry–Howard pour la connaissance

| Notion épistémique (§7) | Notion type-théorique |
|---|---|
| un fait | un type habité (jugement dérivable) |
| sa justification, sa provenance | **le terme de preuve** qui l'habite |
| une hypothèse | une **variable du contexte** `Γ` |
| une observation | un axiome introduit par un capteur, gradué `Observed` |
| une valeur inconnue | une **métavariable** `?x` (un trou, comme en Agda ou Lean) |
| une règle de déduction | une constante de type `A₁ → … → Aₙ → B` |
| un conflit | un habitant de `⊥`, ou deux termes incompatibles pour une même métavariable |
| la base de connaissances | le contexte `Γ` (persistant) |

Cette lecture règle d'un coup la **révision** (§7.3). Les dépendances d'une conclusion sont
exactement les variables libres et les axiomes de son terme de preuve. Si une observation
change, on invalide les termes qui la mentionnent et on reconstruit les autres. C'est le
*truth maintenance system* de Doyle (1979), obtenu ici comme une propriété structurelle et non
comme un mécanisme ajouté.

### 4.3 Les sept statuts du §7.1 se décomposent en trois axes

Les statuts de la spécification mélangent des notions orthogonales. Les séparer rend le
système compositionnel :

| Axe | Valeurs | Nature |
|---|---|---|
| **Existence** | connu / `Unknown` | une métavariable est-elle résolue ? |
| **Support** (grade) | `Observed` ⊑ `Estimated` ⊑ `Defaulted` ⊑ `Hypothesis` | élément d'un treillis de confiance, porté par une modalité graduée (§5.3) |
| **Cohérence** | cohérent / `Conflict` | `⊥` est-il dérivable dans `Γ` ? |

`Derived` n'est **pas un grade** mais une **forme de preuve** : une application de règle. Une
conclusion dérivée d'observations reste fondée sur l'observation ; dérivée d'une estimation,
elle est estimée. Le grade d'une conclusion se *calcule* donc à partir de ses prémisses, au
lieu d'être déclaré (§6.4).

### 4.4 Les capacités sont des opérations d'élaboration

La lecture « inconnues = métavariables » donne un rôle précis à chacune des neuf interfaces du
§6. Hypomnesis devient un **élaborateur** dont les plugins sont des tactiques :

| Interface (§6) | Rôle type-théorique |
|---|---|
| `Observer` | introduit des axiomes de grade `Observed` (depuis le mode Monde, §5) |
| `Generator` | énumère des habitants d'un type (synthèse de termes) |
| `Estimator` | propose une solution pour une métavariable, de grade `Estimated` |
| `Solver` | résout un ensemble de métavariables sous contraintes (unification modulo théorie, SMT) |
| `Validator` | procédure de décision : rend un terme de preuve ou un contre-exemple |
| `Transpiler` | **morphisme de théories** (traduction de signatures, §6.1) |
| `KnowledgeBase` | contexte `Γ` persistant et interrogeable |
| `Actuator` | opération d'un effet algébrique (§6.3) |
| `Resolver` | **tactique** : stratégie qui compose les précédentes pour résoudre un but |

### 4.5 Un noyau de confiance

Le principe LCF et le critère de de Bruijn s'appliquent : seul le noyau peut construire un
fait de forme `Derived`. Un plugin ne *décide* rien ; il rend un **certificat** que le noyau
vérifie. Pour Z3, c'est le modèle (vérification bon marché) ou la preuve d'insatisfiabilité ;
pour un estimateur, une valeur que le noyau gradue `Estimated`. L'hypothèse H2 devient
mesurable : la base de confiance se réduit au noyau, aux plugins près.

---

## 5. Modes

### 5.1 Une théorie des modes

La théorie des types multimodale (MTT, Gratzer–Kavvos–Nuyts–Birkedal, LICS 2020) est
*paramétrée* par une **théorie des modes** : une 2-catégorie dont

- les objets sont des **modes**, c'est-à-dire des mondes de discours ayant chacun leurs propres
  règles ;
- les 1-morphismes sont des **modalités** `μ : n → m`, qui transportent un type du mode `n`
  vers le mode `m` ;
- les 2-cellules sont des **coercions** entre modalités.

Proposition de théorie des modes canonique pour Hypomnesis :

```text
                    ⇑ (Code)
        Objet ─────────────────────▶ Méta
   (ML pur, valeurs)                (λΠ, théories, preuves)
       │   ▲
     F │   │ U          F ⊣ U        T = U ∘ F  : la monade d'effets
       ▼   │
        Monde
   (calculs à effets : capteurs, actionneurs ; interprété par le runtime seul)

   + sur Objet : une famille de modalités graduées [g] indexée par le treillis
     de support, avec des 2-cellules  g ⊑ g'  ⇒  [g]A → [g']A
```

### 5.2 Effets : la monade naît d'une adjonction entre modes

Suivant Benton (logique LNL, 1994) et le *call-by-push-value* :

- `F : Objet → Monde` transforme une valeur en calcul ;
- `U : Monde → Objet` *suspend* un calcul en valeur : c'est une **description** d'effet ;
- la monade `effect = U ∘ F` du §10.2 n'est pas primitive : elle **dérive** de l'adjonction.

La pureté du §9.1 devient une propriété de la théorie des modes. Il n'existe **aucune
modalité** de `Monde` vers `Objet` qui exécute : on ne peut que suspendre (`U`). Seul le
runtime, au premier niveau, élimine `F`. « Les effets sont des valeurs » (§10) est exactement
la lecture de `U`.

### 5.3 Connaissance : une modalité graduée

Une valeur estimée a le type `[Estimated] Length.t`. Le typage propage les grades :

```ocaml
val thickness : [Estimated] Length.t
val width     : [Observed]  Length.t
let volume = Q.mul (Q.mul width height) thickness
(* : [Observed ⊔ Estimated] Volume.t = [Estimated] Volume.t *)
```

Ce sont les types à modalités graduées (Granule : Orchard–Liepelt–Eades, ICFP 2019 ; QTT :
Atkey 2018 ; et leur version dépendante : Moon–Eades–Orchard, ESOP 2021). La règle du §14.4,
« le LLM n'invente pas les valeurs », devient une règle de typage : un terme produit par le
LLM a au mieux le grade `Hypothesis`, et une action qui exige `[Observed]` le refuse
statiquement.

### 5.4 Méta : le staging comme frontière LLM

Davies–Pfenning (*A modal analysis of staged computation*, JACM 2001) identifient le code
typé à la modalité `□`. Pour le pipeline du §14 :

```ocaml
val transcribe : string -> Syntax.t effect                 (* sortie LLM : non typée *)
val elaborate  : Syntax.t -> (⇑ plate, diagnostic) result   (* code objet typé *)
```

On ne peut épisser (*splice*) que du `⇑A`, c'est-à-dire du code qui a passé l'élaboration.
Le pipeline « analysé → typé → validé → autorisé » (§14.3) devient une **chaîne de modalités**
qu'aucun programme ne peut court-circuiter.

---

## 6. Méta-algèbre réflexive

Le fil conducteur : **tout ce qu'Hypomnesis compose est une algèbre d'une théorie, et toute
substitution est un morphisme.**

### 6.1 Algèbre des domaines : syntaxe initiale, sémantiques multiples

- La syntaxe d'un DSL est l'**algèbre initiale** de sa signature.
- Une interprétation est l'unique morphisme d'algèbres qui en part (un *fold*).
- Un backend (Python, Z3, SciPy) est un **modèle** de la théorie, au sens de la sémantique
  fonctorielle de Lawvere (1963) : un foncteur de la théorie vers un univers de calcul.

Le critère « deux plugins substituables derrière la même interface » (§16.4, H6) reçoit une
définition : **deux modèles de la même théorie**. On peut alors les comparer : vérifier que
les lois tiennent par tests de propriétés (Hypothesis) ou par preuve.

Quand les backends parlent des **logiques différentes** (Z3 : logique du premier ordre
multi-sortée modulo théories ; un estimateur : modèle statistique ; Prolog : clauses de Horn),
il faut une notion de traduction *entre logiques*. Ce sont les **institutions**
(Goguen–Burstall, JACM 1992) et leurs morphismes : le cadre formel du « raisonnement
hybride » (OBJ-05). Un `Transpiler` vers Z3 est un morphisme d'institutions, et sa correction
est la condition de satisfaction de ce morphisme.

### 6.2 Algèbre des théories : composer les DSL

Les théories forment une catégorie : les objets sont les théories, les flèches les
traductions qui préservent les lois. On y compose :

| Opération | Construction | Usage |
|---|---|---|
| combiner deux DSL qui partagent `Length` | **colimite** (somme amalgamée, *pushout*) | `Mechanics + Materials` sans dupliquer les unités |
| paramétrer | théorie paramétrée, foncteur | `Mechanics (Q : Quantity)` |
| raffiner, implémenter | morphisme de théories | spécification → modèle Python |
| migrer des données | foncteurs Δ, Σ, Π (Spivak, 2012) | changer de schéma de base de connaissances |

C'est l'approche de Specware et de Clear/OBJ (Goguen) : **les DSL sont des objets d'une
catégorie et se composent par colimites.** OBJ-10 (« nouveau domaine sans toucher au noyau »)
devient : le noyau fournit la catégorie des théories, et chaque domaine en est un objet.

### 6.3 Algèbre des effets : un programme, trois handlers

Les effets algébriques (Plotkin–Power 2003 ; Plotkin–Pretnar, ESOP 2009) présentent un effet
comme une **théorie algébrique** : des opérations et des équations. Un programme à effets est
un terme du *modèle libre*, et un **handler** en est un modèle :

```ocaml
effect Motor = sig
  op move : motor_id -> angle -> move_result
end

handler simulate   : Motor   (* réponses fictives *)
handler dry_run    : Motor   (* valide et journalise, n'exécute pas *)
handler production : Motor   (* exige la permission actuator:motor.move *)
```

Les trois modes d'exécution du §10.3 sont **trois modèles de la même théorie d'effets**. La
garantie « sans modification de la logique métier » devient un théorème : le programme est le
même terme libre. Le contrat JSON Schema d'une opération est le *type* de son arité,
sérialisé.

### 6.4 Algèbre de la provenance : un terme, plusieurs lectures

Les semi-anneaux de provenance (Green–Karvounarakis–Tannen, PODS 2007) fournissent l'algèbre
précise du §7.2 :

- la provenance d'un fait est un polynôme de `ℕ[X]` sur les identifiants d'observations :
  `⊗` pour l'usage conjoint de prémisses, `⊕` pour des dérivations alternatives ;
- `ℕ[X]` est **universel** : pour tout semi-anneau commutatif `K`, il existe un unique
  homomorphisme `ℕ[X] → K` qui étend une valuation des observations.

On stocke donc **une** provenance et on en *calcule* les lectures par homomorphismes :

| Semi-anneau image | Lecture |
|---|---|
| treillis de support (⊕ = meilleur, ⊗ = pire) | grade épistémique (§4.3) |
| Viterbi `([0,1], max, ×)` | confiance |
| tropical `(ℝ∪{∞}, min, +)` | coût de dérivation |
| booléens | le fait tient-il encore ? |

La **révision** du §7.3 en découle : retirer une observation `x` revient à appliquer
l'homomorphisme `x ↦ 0`. Les conclusions qui s'annulent tombent, les autres sont conservées
avec leur provenance réduite. L'historique est préservé, car rien n'est muté.

### 6.5 Algèbres au niveau des types : les dimensions

Les dimensions forment un **groupe abélien libre** sur les dimensions de base. Kennedy
(*Dimension types*, ESOP 1994) montre que l'unification modulo la théorie des groupes
abéliens est décidable et donne des types principaux. Le M3 doit donc permettre à une
bibliothèque de déclarer une **théorie équationnelle de types** (§5.3 de la spécification),
associée à une procédure d'unification. Celle-ci est fournie par plugin et vérifiée par
certificat. Le noyau ne connaît ni les mètres ni les groupes abéliens, mais il sait
consommer une procédure d'unification déclarée.

```ocaml
theory Dimension = sig
  sort dim
  op one : dim
  op ( * ) : dim -> dim -> dim
  op inv : dim -> dim
  law assoc   : (a * b) * c = a * (b * c)
  law comm    : a * b = b * a
  law unit    : a * one = a
  law inverse : a * inv a = one
end   (* unification modulo AG : décidable, plugin certifié *)
```

### 6.6 Réflexivité sans paradoxe

« Réflexive » doit être pris au sens fort : **le M3 est décrit dans le M3.** Il y a trois
écueils et une solution.

1. **`Type : Type` est incohérent** (Girard, 1972). L'autodescription naïve de MOF ne peut
   donc pas être transposée telle quelle dans un cadre logique.
2. **La tour réflexive infinie** (3-Lisp, Smith 1984) offre la réflexion totale au prix de la
   perte de toute garantie statique.
3. **L'auto-interprétation d'un langage total** se heurte en général à l'argument
   diagonal. Brown–Palsberg (POPL 2016) en donnent une forme restreinte pour Fω : c'est
   possible, mais délicat.

**Solution : une réflexion stratifiée par univers de codes**, à la manière de la
*lévitation* (Chapman–Dagand–McBride–Morris, ICFP 2010).

- Le niveau méta contient un univers `Desc` de **descriptions** de signatures : des codes,
  manipulables comme données.
- Une fonction d'interprétation `El : Desc → Sig` donne à chaque code sa signature.
- `Desc` lui-même possède un code `⌜Desc⌝ : Desc`, et l'on a `El ⌜Desc⌝ ≅ Desc` **au niveau
  d'univers suivant**. Le M3 se décrit donc lui-même, sans jamais affirmer `Type : Type`.
- Les opérations sur les théories (§6.2) sont des fonctions sur `Desc` : elles sont donc
  **définissables dans le langage**. C'est le sens précis de « méta-algèbre réflexive » : les
  constructions de théories forment une algèbre, et cette algèbre est elle-même une théorie
  exprimable dans le M3.
- Le passage entre niveaux est explicite : `quote` du niveau `n` vers des codes du niveau
  `n+1`, `El` (ou l'épissage) dans l'autre sens. Il n'y a **pas d'`eval : Code → A` libre**
  dans le fragment total.

Cela donne aussi la métaprogrammation du §4.4 de la spécification : les macros sont des
fonctions méta de `Desc` ou `⇑A` vers `⇑B`, hygiéniques par construction puisque le code est
typé et les lieurs sont gérés par le cadre (HOAS).

---

## 7. Le noyau M3 minimal proposé

Huit primitives. Tout le reste (GAT, ML, règles, effets, connaissances) s'élabore vers elles.

| # | Primitive | Rôle |
|---|---|---|
| 1 | **λΠ** : `Π`, `λ`, application, univers `Type₀ : Type₁ : …` | substrat calculatoire et logique |
| 2 | **constantes de signature** | sortes, opérations, relations, règles d'un DSL |
| 3 | **règles de réécriture** (confluentes, terminantes, vérifiées) | lois, définitions calculatoires |
| 4 | **métavariables** `?x : A` avec contraintes | inconnues, objectifs (§5.5 de la spécification) |
| 5 | **modes et modalités** d'une théorie des modes fixée : Objet, Méta, Monde ; `⇑`, `F ⊣ U` | staging, pureté, effets |
| 6 | **grades** : modalité `[g]` sur un semi-anneau déclaré, avec ses 2-cellules `⊑` | statut épistémique, confiance |
| 7 | **univers de descriptions** `Desc` avec `El` | réflexion stratifiée, algèbre des théories |
| 8 | **certificats** : l'interface par laquelle un plugin rend un terme vérifiable | frontière de confiance LCF |

**Clôture réflexive.** La signature qui décrit ces huit primitives est elle-même un élément
`⌜M3⌝ : Desc`. C'est le test d'acceptation du M3 : il doit pouvoir exprimer, typer et
manipuler sa propre définition au niveau d'univers suivant.

---

## 8. Conséquences sur l'existant et le plan

| Élément actuel | Devient |
|---|---|
| langage ML de la phase 1, Core IR (ADR 0002) | **niveau objet** de la 2LTT, conservé |
| `external` et registre fermé (ADR 0003) | modèles primitifs de théories déclarées ; inchangé dans l'esprit |
| contrats JSON Schema (ADR 0004) | sérialisation des **arités** des opérations d'effets et des sortes |
| distinction provenance / observabilité (ADR 0005) | renforcée : provenance = terme de preuve et polynôme ; télémétrie = hors de la théorie |

Ordre de prototypage suggéré, dans l'esprit d'un noyau qui grossit par preuves de concept :

1. **Phase 2 revisitée : métavariables et provenance semi-anneau.** C'est la plus forte valeur
   immédiate, et elle est réalisable sans types dépendants : polynômes `ℕ[X]`,
   homomorphismes de grade et de confiance, révision par `x ↦ 0`. Elle valide H4.
2. **Théories en style GAT** comme signatures de modules ML enrichies de `law`, avec des
   modèles en style tagless-final et une vérification des lois par tests de propriétés.
   Elle valide H1 et H6.
3. **Effets algébriques et handlers** simulate / dry-run / production. Elle valide H5 et
   prépare la phase 5.
4. **Modalité graduée `[g]`** dans le typeur ML, d'abord non dépendante, avec un treillis de
   support fixé.
5. **Niveau méta λΠ-modulo** et `Desc` : c'est le chantier de recherche, à engager une fois
   que 1 à 4 ont montré quelles constructions sont réellement utilisées.

---

## 9. Questions ouvertes et risques

| Question | Enjeu | Piste |
|---|---|---|
| Décidabilité du typage avec réécriture | nécessite confluence et terminaison | vérificateurs de confluence et de terminaison, à la manière de Dedukti ; refus des règles non vérifiées |
| Unification modulo théories équationnelles | indécidable en général | n'accepter que les théories accompagnées d'une procédure (AG, AC, …) certifiée |
| Interaction grades × dépendances × effets | état de l'art récent | figer la théorie des modes dans le noyau V1, l'ouvrir plus tard |
| Le treillis de support est-il universel ? | un domaine peut vouloir d'autres grades (fraîcheur, juridiction) | grades = semi-anneau *déclaré par le domaine*, le noyau ne fixant que l'interface |
| Ergonomie pour humains et LLM | λΠ et les modes sont intimidants | surface ML conservée ; types dépendants et modes visibles seulement dans les DSL qui les utilisent |
| Coût de la vérification de certificats | Z3, estimateurs | certificats paresseux, vérification à la demande au moment de décider ou d'agir |
| Lien statuts de la spécification ↔ trois axes (§4.3) | demande d'amender le §7.1 | à valider avant la phase 2 |

---

## 10. Références

- Annenkov, Capriotti, Kraus, Sattler — *Two-level type theory and applications*, MSCS (2023).
- Atkey — *Syntax and semantics of quantitative type theory*, LICS 2018.
- Benton — *A mixed linear and non-linear logic*, CSL 1994.
- Brown, Palsberg — *Breaking through the normalization barrier: a self-interpreter for F-omega*, POPL 2016.
- Carette, Kiselyov, Shan — *Finally tagless, partially evaluated*, JFP 19(5), 2009.
- Cartmell — *Generalised algebraic theories and contextual categories*, APAL 32, 1986.
- Chapman, Dagand, McBride, Morris — *The gentle art of levitation*, ICFP 2010.
- Cousineau, Dowek — *Embedding pure type systems in the λΠ-calculus modulo*, TLCA 2007.
- Davies, Pfenning — *A modal analysis of staged computation*, JACM 48(3), 2001.
- Doyle — *A truth maintenance system*, Artificial Intelligence 12, 1979.
- Girard — thèse d'État, Paris VII, 1972 (paradoxe de `Type : Type`).
- Goguen, Burstall — *Institutions: abstract model theory for specification and programming*, JACM 39(1), 1992.
- Gratzer, Kavvos, Nuyts, Birkedal — *Multimodal dependent type theory*, LICS 2020.
- Green, Karvounarakis, Tannen — *Provenance semirings*, PODS 2007.
- Harper, Honsell, Plotkin — *A framework for defining logics*, JACM 40(1), 1993.
- Kennedy — *Dimension types*, ESOP 1994.
- Kovács — *Staged compilation with two-level type theory*, ICFP 2022.
- Lawvere — *Functorial semantics of algebraic theories*, thèse, Columbia, 1963.
- Moon, Eades, Orchard — *Graded modal dependent type theory*, ESOP 2021.
- Orchard, Liepelt, Eades — *Quantitative program reasoning with graded modal types*, ICFP 2019.
- Plotkin, Power — *Algebraic operations and generic effects*, Applied Categorical Structures 11, 2003.
- Plotkin, Pretnar — *Handlers of algebraic effects*, ESOP 2009.
- Smith — *Reflection and semantics in Lisp*, POPL 1984.
- Spivak — *Functorial data migration*, Information and Computation 217, 2012.
- Logiciels de référence : Dedukti (λΠ-modulo), AlgebraicJulia GATlab/Catlab (GAT), Specware (algèbre de spécifications), Granule (types gradués), Agda et Lean (métavariables, élaboration), OMG MOF et Ecore (M3 classique, point de comparaison).
