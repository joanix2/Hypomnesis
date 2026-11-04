---
title: "HYP-149 · Hypothèse : résolution générale et recherche constructive"
lane: hypothese
created: 2026-11-04T19:04:05+01:00
updated: 2026-11-04T19:04:05+01:00
description: "P2 · L · Recherche — Solver abstrait, Search spécialisé, synthèse typée et heuristiques optionnelles"
priority: P2
tags: [hypothese, architecture, moteur-symbolique, metalangage, solveurs, synthese]
---

## Conversation

### user

**Ticket** HYP-149 · **Priorité** P2 · **Taille** L · **Epic** Hypothèses et recherche · **Dépend de** aucune · **Labels** hypothese, recherche

Créer une colonne hypothèse et y conserver la proposition partagée.
Cette entrée est une piste à évaluer, pas une décision architecturale acceptée
ni une tâche à lancer automatiquement.

#### Hypothèse centrale

Séparer un contrat général de résolution (`Solver`) d'une spécialisation
de recherche constructive (`Search`), puis exprimer la synthèse d'AST comme
un problème de recherche au même titre que la planification ou la construction
d'un modèle d'application.

- Le problème décrit états, actions, transitions, contraintes et objectif ;
  la stratégie définit l'exploration, indépendamment du domaine.
- La validité syntaxique, le typage et les contraintes restent symboliques.
  Une heuristique neuronale facultative classe les actions admissibles ou
  propose leurs paramètres ; toute proposition est validée avant application.
- Le codegen et les intégrations LLM restent hors du compilateur/métalangage
  (ADR 0012). Le noyau ne dépend pas d'un modèle neuronal.
- SMT/SAT, optimisation et unification ne sont pas forcés à devenir des
  recherches explicites dans un espace d'états.

#### Questions à expérimenter avant adoption

- Distinguer `Unsatisfiable` (preuve d'absence de solution), `Exhausted`
  (exploration ou candidats épuisés), `Timeout` et `Unknown` ; une recherche
  bornée ou heuristique ne démontre pas à elle seule l'insatisfaisabilité.
- Définir les schémas d'actions et la génération bornée de candidats pour les
  espaces infinis, avec budgets, coût et traces explicites.
- Ne pas confondre AST complet/bien typé et conformité à l'intention :
  formaliser cette dernière par contraintes, exemples ou propriétés vérifiables.
- Évaluer une même interface sur labyrinthe, synthèse d'expressions typées et
  construction d'un modèle CRUD, sans réécrire le moteur.
- Étudier la composition avec les solveurs spécialisés et l'IR existante ;
  HYP-051 fournit des descriptions déclaratives, pas encore un planificateur.

#### Références

- `docs/architecture/problem-ir.md`
- `docs/adr/0012-codegen-separe-du-moteur.md`
- `.agentkanban/tasks/task_20261103_hyp051_problem-ir.md`

#### Proposition originale conservée

Le texte ci-dessous est conservé tel que partagé, y compris les exemples
d'interfaces proposées. Il ne décrit pas des APIs actuellement disponibles.

---

Exactement. Et je pense que tu viens de mettre le doigt sur une abstraction qui pourrait devenir **centrale dans Hypomnesis**.

L'idée n'est pas de créer un solveur spécialisé pour ton décodeur, puis un autre pour la génération d'applications, puis un troisième pour la planification d'agents.

C'est de définir **ce qu'est un problème à résoudre**, indépendamment du domaine.

Ensuite, ton décodeur d'AST, ton générateur d'applications et même un agent deviennent différentes instanciations du même modèle.

## 1. Le solveur comme abstraction générale
Je proposerais de distinguer trois choses :

1. **Le problème** définit les états, les actions, les contraintes et les objectifs.
2. **Le solveur** explore les possibilités pour trouver une solution.
3. **La stratégie** détermine comment explorer efficacement.
Cette séparation est importante : un problème ne devrait pas connaître l'algorithme qui le résout.

### Modèle mathématique
On peut définir un problème de résolution par :

\[ \boxed{\mathcal P=(S,A,T,s_0,G,C)} \]Avec :

ÉlémentSignification\(S\)Ensemble des états possibles\(A(s)\)Actions disponibles depuis l'état \(s\)\(T(s,a)\)Transition produite par l'action \(a\)\(s_0\)État initial\(G(s)\)Prédicat indiquant si l'objectif est atteint\(C(s,a)\)Coût éventuel d'une action

Une solution est alors une séquence d'actions :

\[ \pi=(a_1,a_2,\ldots,a_n) \]telle que :

\[ G(T(\ldots T(T(s_0,a_1),a_2)\ldots,a_n))=\mathrm{vrai} \]Ce modèle couvre déjà beaucoup de problèmes.

Mais il faut éviter une confusion : **tout solveur n'est pas nécessairement un algorithme de recherche explicite dans un espace d'états**.

Un solveur SMT, par exemple, manipule des contraintes symboliques. Il peut être intégré dans notre architecture, mais il ne fonctionne pas nécessairement en énumérant des actions métier.

Il faut donc distinguer une abstraction générale de *résolution* et une spécialisation *planification/recherche d'états*.

---

## 2. Deux niveaux dans Hypomnesis
Je verrais deux bibliothèques.

### `Solver` : abstraction générale
Elle décrit le contrat commun :

```
type 'solution result =
  | Solved of 'solution
  | Unsatisfiable
  | Exhausted
  | Timeout
  | Unknown
```

Conceptuellement :

```
solve : Problem.t -> Strategy.t -> Solution.t result
```

Ce niveau pourrait accueillir différents moteurs :

- recherche dans un graphe ;
- solveur de contraintes ;
- programmation par contraintes ;
- optimisation ;
- synthèse de programmes ;
- planification.
Il fournit un vocabulaire commun sans imposer une représentation interne unique.

### `Search` : solveur à transitions d'états
C'est là que ton idée « état actuel + actions possibles » devient directement exploitable.

```
type ('state, 'action) problem = {
  initial : 'state;
  actions : 'state -> 'action list;
  transition : 'state -> 'action -> 'state;
  is_goal : 'state -> bool;
  cost : 'state -> 'action -> float
}
```

**Attention :** ce code est une proposition d'interface, pas une API déjà implémentée dans Hypomnesis.

Une fois ce contrat établi, tu peux changer de stratégie sans réécrire ton problème :

```
                 SearchProblem
                       │
          ┌────────────┼────────────┐
          │            │            │
         BFS          A*         Beam Search
          │            │            │
          └────────────┼────────────┘
                       │
                    Solution
```

C'est aussi ce qui permettrait d'utiliser une stratégie déterministe pour les tests et une stratégie guidée par un modèle neuronal en production.

---

## 3. Ton décodeur d'AST devient un problème de recherche
Prenons une intention :

> « Créer une fonction qui additionne deux entiers. »
Le décodeur doit construire un AST valide.

### État
L'état n'est pas seulement l'AST partiel.

Je le représenterais plutôt comme :

\[ s=(AST_{\text{partiel}},\Gamma,H,\Phi) \]où :

- \(AST_{\text{partiel}}\) est l'arbre en cours de construction ;
- \(\Gamma\) est l'environnement de typage ;
- \(H\) est l'ensemble des trous à compléter ;
- \(\Phi\) est l'ensemble des contraintes accumulées.

### Actions
Une action correspond à une transformation autorisée :

```
InsertLiteral(value)
InsertVariable(name)
InsertLambda(parameter)
InsertApplication(function)
InsertConstructor(constructor)
FillHole(hole, expression)
```

### Préconditions
Les actions ne sont pas toutes disponibles dans tous les états.

Si le trou courant attend un `int`, le système peut proposer :

```
IntLiteral(42)
Variable("x")       si x : int
Add(expr1, expr2)   si Add : int -> int -> int
```

Mais pas :

```
StringLiteral("bonjour")
```

sauf si une conversion explicite est autorisée.

La contrainte de typage réduit donc l'espace de recherche **avant** l'évaluation neuronale.

### Objectif
\[ G(s)= \operatorname{Complete}(AST) \land \operatorname{WellTyped}(AST) \land \operatorname{SatisfiesSpec}(AST) \]Il faut distinguer ces trois conditions : un AST complet et bien typé peut parfaitement ne pas faire ce que l'utilisateur demande. Le typage élimine certaines erreurs, pas les erreurs de sens.

---

## 4. Le modèle neuronal ne génère plus directement l'AST
C'est probablement la conséquence architecturale la plus intéressante.

Au lieu de :

```
Intention
   ↓
LLM
   ↓
AST
   ↓
Validation
   ↓
Échec éventuel
```

Tu obtiens :

```
                  Intention
                      │
                      ▼
                État initial
                      │
                      ▼
              Actions admissibles
                      │
             ┌────────┴────────┐
             │                 │
             ▼                 ▼
        Type checker      Contraintes
             │                 │
             └────────┬────────┘
                      ▼
             Actions autorisées
                      │
                      ▼
              Modèle neuronal
              (classement)
                      │
                      ▼
              Stratégie de recherche
                      │
                      ▼
                Nouvel état
                      │
                Objectif atteint ?
                  │         │
                 Non       Oui
                  │         │
                  └──↺      ▼
                        AST final
```

Le réseau neuronal devient une **heuristique de recherche**.

Il ne décide pas de ce qui est valide. Il estime ce qui est prometteur.

Mathématiquement :

\[ \operatorname{score}_{\theta}(a\mid s,I) \]où \(I\) représente l'intention et \(\theta\) les paramètres du modèle.

Le solveur sélectionne une action parmi les actions admissibles :

\[ a^*=\arg\max_{a\in A(s)} \operatorname{score}_{\theta}(a\mid s,I) \]Pour une recherche *beam*, il conserverait plusieurs états candidats au lieu d'un seul.

**Avantage :** tu peux remplacer le modèle neuronal sans changer la sémantique du langage ni les règles de typage.

---

## 5. Ton générateur d'applications devient lui aussi un solveur
C'est ici que les projets que nous venons d'examiner se rejoignent.

Supposons que l'utilisateur demande :

> « Je veux une application de gestion de devis, avec des clients, des droits d'accès et un workflow de validation. »
Le système peut partir d'un modèle incomplet :

```
Application
├── Client
├── Quote
├── Relation Client → Quote
├── Permissions ?
├── Workflow ?
└── Pages ?
```

Le solveur dispose d'actions :

```
AddEntity
AddField
AddRelation
AddConstraint
AddPermission
AddWorkflow
AddPage
BindPageToEntity
```

Il cherche un modèle qui satisfait :

\[ G(s)= \operatorname{WellTyped}(s) \land \operatorname{Consistent}(s) \land \operatorname{RequirementsSatisfied}(s) \]Et la génération de code devient une étape distincte :

\[ \boxed{ \text{Intention} \xrightarrow{\text{Solveur}} \text{Modèle AppLang valide} \xrightarrow{\text{Compilateur}} \text{Application} } \]C'est une séparation importante.

Le solveur **construit une spécification valide**.

Le compilateur **traduit cette spécification en code**.

On évite ainsi de mélanger raisonnement métier, résolution de contraintes et production de fichiers.

---

## 6. Le point difficile : la définition des actions
Il y a néanmoins un problème théorique à résoudre.

Si `actions(state)` doit calculer toutes les actions possibles, l'espace peut être infini.

Par exemple :

```
InsertInteger(0)
InsertInteger(1)
InsertInteger(2)
...
```

Ou :

```
CreateVariable("a")
CreateVariable("b")
CreateVariable("c")
...
```

Tu ne peux donc pas toujours énumérer les actions.

Je proposerais de distinguer :

**Les schémas d'actions**, qui décrivent les transformations possibles, et **les actions instanciées**, qui fournissent leurs paramètres.

Par exemple :

```
Schéma :
    InsertLiteral(type = Int)

Instanciations :
    InsertLiteral(0)
    InsertLiteral(1)
    InsertLiteral(42)
```

Le solveur peut alors demander à un générateur de candidats de proposer quelques instanciations pertinentes.

C'est aussi là que les modèles neuronaux peuvent être utiles : ils ne choisissent pas uniquement parmi des actions déjà énumérées, ils peuvent proposer les paramètres d'une action.

Il faudra cependant valider chaque proposition avant de l'appliquer.

---

## 7. Une architecture qui permet aux solveurs de se composer
Je pousserais même l'idée un cran plus loin.

Un solveur peut déléguer certains sous-problèmes à d'autres solveurs.

Par exemple, ton décodeur :

```
AST Solver
    │
    ├── Type Solver
    │     └── Unification
    │
    ├── Constraint Solver
    │     └── SMT
    │
    ├── Search Solver
    │     └── Beam Search
    │
    └── Semantic Evaluator
          └── Tests / propriétés
```

Mais attention à la récursion conceptuelle : **le fait qu'un composant aide à résoudre un problème ne signifie pas qu'il faut obligatoirement le modéliser lui-même comme un solveur à états**.

L'unification de types, par exemple, peut rester un algorithme spécialisé appelé par le moteur de recherche.

Je garderais donc une architecture extensible, sans chercher à tout faire entrer artificiellement dans le même moule.

---

## 8. Ce que je construirais en premier dans Hypomnesis
Je commencerais par un noyau minimal :

ComposantResponsabilité`SearchProblem`Définir état, actions, transition, objectif`SearchStrategy`Choisir l'ordre d'exploration`SearchResult`Retourner solution, chemin, statut`ActionGenerator`Proposer des actions candidates`ConstraintChecker`Rejeter les états invalides`SearchTrace`Enregistrer les décisions et les échecs

Puis j'implémenterais **trois problèmes très différents avec le même moteur** :

1. **Labyrinthe** : vérifier que le modèle sait résoudre un problème simple et déterministe.
2. **Synthèse d'expressions typées** : vérifier que les contraintes réduisent correctement les actions.
3. **Construction d'une application CRUD** : vérifier que l'abstraction s'applique à AppLang.
Si le troisième exemple nécessite de réécrire le moteur, c'est que l'abstraction n'est pas encore assez générale.

### Mon principal désaccord avec une généralisation trop rapide
Je ne définirais pas immédiatement *tous les solveurs* comme des systèmes « état + actions + objectif ».

C'est une excellente abstraction pour la **recherche constructive**, la planification et la synthèse.

Mais pour couvrir proprement SMT, SAT, optimisation continue et résolution algébrique, il vaut mieux définir au-dessus un contrat de résolution plus abstrait, puis spécialiser les mécanismes.

Autrement, tu risques de transformer Hypomnesis en une immense architecture générique où chaque algorithme doit se déguiser en recherche d'actions. Ce serait assez ironique pour un projet censé simplifier la formalisation.

## La proposition centrale
Je formaliserais donc :

\[ \boxed{ \text{Hypomnesis} = \text{Langage de modèles} + \text{Bibliothèques de problèmes} + \text{Moteurs de résolution} } \]Avec cette propriété :

\[ \boxed{ \text{Décodeur AST} \subset \text{Problèmes de synthèse} \subset \text{Problèmes de recherche} \subset \text{Problèmes de résolution} } \]**Ton décodeur ne serait plus un composant spécial d'Hypomnesis. Il deviendrait une application de ses propres abstractions.**

Et c'est un test architectural particulièrement fort : si Hypomnesis peut exprimer et résoudre le problème de construction de ses propres programmes, tu disposes d'un premier mécanisme concret de métaprogrammation guidée par contraintes, sans avoir besoin de prétendre avoir déjà construit une AGI.

### agent

Colonne `hypothese` créée avant `todo`. Proposition enregistrée sous HYP-149,
avec son texte original et une synthèse des points à vérifier. Elle reste hors
des tâches prêtes et des lots parallèles ; sa présence n'adopte aucune API.
Le statut CLI expose les hypothèses séparément, en texte et en JSON.

Validation : 36 tests ciblés Kanban/ordonnanceur passent ; le texte partagé
est conservé intégralement et HYP-149 apparaît seulement dans la catégorie
`hypothese`. Le dépôt contient 103 tickets valides. Validation complète verte :
785 tests (708 cœur, 77 Codegen), linters, Pyright, schémas, build Lean,
audit des axiomes et vérificateur de certificats. Graphe Graphify actualisé.
L'hypothèse reste dans son couloir, pas en `qa`, car ces validations portent
sur son enregistrement et l'outillage, pas sur la démonstration de la proposition.

### user
