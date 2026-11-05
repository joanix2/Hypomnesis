---
title: "HYP-023 · Lean F2 : polymorphisme dans les termes élaborés"
lane: doing
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P1 · L · Vérification formelle (Lean) · dépend de HYP-020"
priority: P1
tags: [certification, lean, metalangage]
---

## Conversation

### user

Étendre le pont P44 aux motifs scalaires et de paires, sans prendre les
constructeurs paramétriques comme acquis.

### agent

`RuntimePat` borne explicitement les motifs pris en charge aux littéraux,
variables, wildcard et paires. Le lemme `PatTy.erase_runtimePat` transforme
ces typages de motifs vers `Core.PatTy`, et le cas `case` du fragment réutilise
ensuite le véritable théorème `Core.eval_safe`. Une régression vérifie à tout
fuel le filtrage d'une paire qui lie la première composante ; l'ordre de pile
Core est conservé. Les cas de mismatch restent autorisés sous le contrat
`Core.Safe`.

Audit P44, catalogue, commentaires de syntaxe, `TECHNICAL.md` et checklist
mis à jour. Validations réussies : `validate.sh lean` (audit inclus),
`validate.sh rapide`, `validate.sh graphe`, `kanban.py check` (109 tâches) et
`git diff --check`. Les motifs nominaux/paramétriques, records,
`Coverage.Certified`, la sûreté des schémas multi-instanciés, le décodeur/CLI
et le véritable `List.map` du prélude restent ouverts. Cette étape n'est pas
la clôture de HYP-023.

### user

Poursuivre HYP-023 en étendant P44 à la récursion monomorphe.

### agent

`RuntimeFragment` accepte désormais les `fix` monomorphes lorsque le corps
conserve le même effacement spécialisé et polymorphe. La preuve existante
transfère le typage vers Core, puis réutilise `Core.eval_safe` sans modifier
les garanties de fuel. La régression `eval_safe_recursiveCountdownApplication`
prouve la sûreté à tout fuel d'une fonction récursive typée, et
`eval_recursiveCountdownApplication` vérifie son résultat concret.

Audit et catalogue P44, syntaxe et `TECHNICAL.md` sont synchronisés ; la
checklist distingue cette récursion mono du pont polymorphe encore absent.
La suite Lean ciblée compile. Les motifs/records/`Certified`, les schémas
polymorphes multi-instanciés, le décodeur/CLI et le vrai `List.map` du prélude
restent à faire. Aucun commit ni push pour cette étape.

### user

Poursuivre HYP-023 sur le pont de sûreté du runtime polymorphe.

### agent

Extension du pont P44 aux lambdas et applications monomorphes. `eraseMono`
conserve les annotations de fonction ; l'égalité d'évaluation avec
l'effacement Core réel est prouvée pour le fragment, avec une condition
explicite sur l'effacement du corps des fermetures. `RuntimeEnvRel` relie
l'environnement monomorphe aux valeurs Core, et la sûreté vaut à fuel
arbitraire. La régression `eval_safe_capturedIntLambdaApp` couvre une
fermeture qui capture puis restitue une liaison lexicale entière.

Les nouveaux théorèmes sont dans l'audit ; le catalogue P44, `TECHNICAL.md`
et la checklist précisent la portée et les limites. Vérifications réussies :
`./scripts/validate.sh lean` (audit inclus), `./scripts/validate.sh rapide`,
`./scripts/validate.sh graphe` et `git diff --check`. HYP-023 reste `doing` :
les valeurs/fermetures polymorphes générales, motifs/records/certification,
le décodeur/CLI et le vrai `List.map` du prélude restent à intégrer. Aucun
push effectué.

### user

Poursuivre HYP-023 à partir du typeur polymorphe et de sa relation déclarative.

### agent

Étape 4 : `Ty` possède maintenant une égalité booléenne structurelle prouvée
fidèle (`LawfulBEq`). Les termes à instanciation explicite et les liaisons
`let` polymorphes sont vérifiés par `typeOf`, et `HasType` décrit le même
fragment. Les théorèmes `typeOf_sound` et `typeOf_complete` établissent leur
équivalence sous une signature bien formée et un environnement bien scopé ;
le jugement exige aussi les portées contrôlées par le checker pour les
constructeurs et motifs. Une régression prouve le let identité aux types int
et bool ; les cas d'arité et de valeur incompatibles restent rejetés.

P41, l'audit d'axiomes et la documentation technique sont mis à jour.
`./scripts/validate.sh lean`, `scripts/kanban.py check`, `git diff --check`
et `graphify update .` passent. La vérification établit l'équivalence du
checker et du jugement, pas encore la sûreté par rapport à l'évaluateur.
HYP-023 reste `doing` ; substitution de types sur les termes, préservation
opérationnelle, décodeur/CLI et véritable `List.map` restent ouverts. Aucun
commit ni push effectué.

### user

Périmètre global confirmé : keep-local-and-gates.

### agent

Le jalon des environnements de schémas est committé localement en
`9bc234e` (sans push). `validate.sh lean`, `validate.sh rapide`,
`validate.sh graphe` et `kanban.py check` passent ; le worktree est propre.
Le ticket reste en cours : les termes polymorphes, leur sûreté et le
branchement du vérificateur ne sont pas encore implémentés.

### user

Reprise après approbation du plan global de clôture des P1. Continuer
HYP-023 depuis le jalon e7271e6, sans sous-agent ni push.

### agent

Itération 3 ajoutée dans `Core/PolyTypes.lean` : contextes de variables
représentés par des schémas, instanciation indexée, conservation de portée,
et commutation de la substitution avec l'instanciation. Les régressions
couvrent `List.map` instancié à int/bool, l'arité invalide et une variable
de type extérieure. P40, l'audit d'axiomes et la documentation sont mis à
jour. `lake build` et l'audit Lean passent avec les seuls axiomes standard.

Cette étape ne type toujours pas les termes polymorphes, ne modifie pas
`Core.typeOf` ou le décodeur, et ne vérifie pas le corps du véritable
`List.map`. HYP-023 reste `doing` ; prochaine étape : termes et jugement de
typage, puis sûreté et branchement.

### user

**Ticket** HYP-023 · **Priorité** P1 · **Taille** L · **Epic** Vérification formelle (Lean) · **Dépend de** HYP-020 · **Labels** lean

#### Contexte

L'inférence HM produit des schémas `∀ᾱ.τ`. Pour que le certificat reste vérifiable par un algorithme simple, il doit expliciter les abstractions et instanciations de types, à la manière de Système F restreint au rang 1 : on ne prouve pas l'algorithme W, on vérifie son résultat.

#### Tâches proposées

- Ajouter variables de type, `Λ` (généralisation au `let`) et instanciation explicite aux termes élaborés.
- Substitution de types et lemmes associés (préservation du typage par substitution).
- Étendre la sûreté, `typeOf` et ses preuves.

#### Critères d'acceptation

- Preuves sans `sorry`.
- `List.map` du prélude s'exprime et se type dans le fragment.

#### Fichiers concernés

- `formal/Hypomnesis/Core/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`

### agent

Plan P1 approuvé. Inventaire initial : `Ty`, `Sig`, `HasType`, `typeOf`
et les certificats sont actuellement monomorphes. Le véritable `List.map`
du prélude dépend de `rev` et `fold_left` ; prouver seulement une autre
fonction map isolée ne satisfait pas le jalon. L'extension doit traiter
les signatures de données paramétriques et réparer les preuves de
filtrage/records/fuel couplées ; aucun changement partiel du noyau effectué.

L'ordre du lot est ajusté pour livrer d'abord la chaîne indépendante
d'observabilité HYP-070–073, sans faire dépendre ces tickets de HYP-023.
HYP-023 reste à implémenter ; aucune monomorphisation présentée comme
preuve du polymorphisme, aucun passage en QA.

### user

Suite du lot P1 : polymorphisme avant les services. Plan approuvé.

### agent

Implémentation séquentielle du plan approuvé, sans sous-agent et sans push.
Checklist dédiée créée. Rang 1 : schémas au let, arguments de fonctions et
récursion monomorphes ; les variables de types liées utilisent des indices
de de Bruijn. Les signatures nominales portent leurs arités et leurs
arguments de constructeurs paramétriques.

Première étape dans Core/PolyTypes : algèbre des types et schémas,
renommage/substitution, protection des variables liées, vérification de
portée et instanciation contrôlée par arité. Le noyau monomorphe et son
checker public restent intacts jusqu'au branchement vérifié.
Ce module préparatoire n'est pas un interpréteur de remplacement ; il ne
satisfait pas à lui seul HYP-023. Le schéma de type de map sert de régression
de représentation et n'est pas présenté comme preuve du corps du prélude.

### user

### agent

Fondations implémentées et compilées dans `Core/PolyTypes.lean` :
monotypes ouverts, schémas, données nominales avec arguments de types et
arités déclarées. Preuves d'identité/composition des substitutions et
renommages, substitution sous quantificateurs sans capture, conservation
des portées, commutation substitution/instanciation et bonne portée des
types de constructeurs instanciés. L'inclusion des types historiques est
invariante par substitution ; ce n'est pas encore un pont des programmes.

Douze régressions calculées dans `Core/PolyTypeExamples.lean` :
signature de liste générique, schéma de map et instanciation int/bool,
arguments génériques, mauvaise arité, indices libres, données/constructeurs
inconnus, déclaration mal scopée, protection des variables liées et
conservation du contexte extérieur. Aucun programme map de remplacement.

`lake build` et l'audit compilent toutes les preuves existantes avec ces
nouveaux modules. Les vingt énoncés additionnels audités n'utilisent que
les axiomes standard autorisés. ADR 0020, catalogue P36–P39, stratégie et
document technique explicitent les limites. Le décodeur et le CLI restent
inchangés ; typage des termes et sûreté polymorphe restent à faire.
HYP-023 demeure doing. Validation du jalon avant commit en cours.

### user

### agent

Jalon des fondations validé : contrôles ciblés pre-commit, `validate.sh lean`,
`validate.sh rapide` et `validate.sh graphe` verts. La suite Lean comprend
les certificats et 500 cas différentiels générés, sans échec. Treize
régressions de types compilent (rectification du compte de douze ci-dessus).

Commit local de ce jalon, sans push. La suite du plan reste le typage
des termes polymorphes et des environnements, la sûreté, les preuves
couplées puis le branchement du véritable checker. HYP-023 n'est ni en
QA ni terminé ; aucune certification générique du corps de List.map
n'est encore annoncée.

### user

### agent

`Poly.HasType.subst` est maintenant prouvé sans `sorry` : toute dérivation
reste typable après substitution des variables de type lorsque la signature
est bien formée et que les images sont bien scopées. La preuve couvre les
liaisons `let` avec substitution relevée, les constructeurs paramétriques et
les contextes de motifs ; `Poly.PatTy.subst` en établit la compatibilité des
motifs. Une régression spécialise deux variables de type ouvertes en int/bool.

P42 est ajouté au catalogue et à l'audit. `lake build Hypomnesis.Core.PolyTypingExamples`,
`./scripts/validate.sh lean`, `git diff --check` et
`.venv/bin/python scripts/kanban.py check` passent ; l'audit ne relève que
les axiomes Lean standards et 109 tâches Kanban sont valides. Graphify a été
actualisé. HYP-023 reste `doing` : la sûreté par rapport à l'évaluateur, le
décodeur/CLI et le vrai `List.map` restent ouverts. Aucun commit ni push effectué.

### user

Continuer l'implémentation de HYP-023 après la preuve de préservation par
substitution, en poursuivant le pont vers la sûreté du runtime.

### agent

Poursuite de l'étude du pont de sûreté vers `Core.eval`. La réutilisation
directe de `Core.eval_safe` par simple effacement n'est pas valide pour le
fragment complet : `Core.Ctx` donne un type unique à une valeur liée, alors
qu'un même schéma `let` peut être utilisé à `int` et `bool` ; `Core.Sig`
fixe aussi un payload monomorphe, contrairement aux constructeurs de données
paramétriques de `Poly.Signature`. La sûreté polymorphe doit interpréter les
schémas et signatures dans une relation de valeurs/environnements, ou passer
par une spécialisation dont la préservation de l'évaluation est prouvée.

Les modules Lean polymorphes existants compilent toujours (`PolyTypes`,
`PolySyntax`, `PolyTyping`). Aucun faux pont ni changement du noyau Core
n'a été introduit. HYP-023 reste `doing` ; prochaine étape : formaliser la
relation polymorphe, puis prouver la sûreté en préservant les garanties de
motifs, `Certified` et fuel. Aucun commit ni push.

### agent

Itération suivante : P43 prouve que `Expr.erase` commute avec toute
substitution de types, donc que l'évaluation `Core.eval` d'un terme effacé
est identique après spécialisation. Le corollaire transporte l'absence de
`stuck` d'une exécution Core déjà sûre vers ses substitutions. Cette propriété
est auditée et documentée ; elle ne fournit pas encore le cas de base de
sûreté pour une dérivation polymorphe. La régression distincte
`identity_polymorphic_let_is_checked_and_evaluated` établit le typage et
l'exécution du cas concret `int`/`bool`.

Vérifications : `./scripts/validate.sh lean`, `kanban.py check` (109 tâches),
`git diff --check` et `graphify update .` passent ; P43 et la régression
runtime n'ajoutent pas d'axiomes non standards. Le pont général vers la sûreté
reste ouvert, ainsi que l'intégration CLI et le vrai `List.map` ; HYP-023
demeure `doing`, sans commit ni push.

### agent

Itération suivante : `PolySoundness.lean` ajoute P44, un pont formel d'un
fragment sans fonction ni liaison vers le véritable `Core.eval_safe` :
constantes, conditions, produits, projections et opérations binaires. Une
dérivation polymorphe dans ce fragment donne un typage Core de l'effacement,
puis la sûreté Core à tout fuel. L'effacement des variables de type vers
`unit` est défini explicitement pour les types.

P44 est volontairement bornée et ne prétend pas résoudre le point bloquant :
la sûreté des schémas `let`, des fermetures, des constructions/données
paramétriques et des motifs. HYP-023 reste `doing`; relation polymorphe,
branchement CLI et `List.map` demeurent à faire.

### user

### agent

L'extension reçue pour P44 ajoute `RuntimeEnvRel` pour les environnements
monomorphes, le typage Core de l'effacement des `let` d'arité zéro et
`eval_safe_monoLetRuntimeFragment`, valable à tout fuel sur le véritable
`Core.eval`. La régression `eval_safe_discardedIntLet` vérifie un `let`
monomorphe évalué dont la liaison n'est pas utilisée. Le fragment n'a toujours
pas de constructeur de variable : cela ne prouve ni l'usage des liaisons ni
la sûreté des schémas polymorphes.

Les nouveaux théorèmes sont raccordés à l'audit d'axiomes ; il ne rapporte
que `propext`, `Classical.choice` et `Quot.sound`. `./scripts/validate.sh lean`,
`kanban.py check` (109 tâches), `git diff --check` et
`./scripts/validate.sh graphe` passent. La documentation technique et P44
précisent la portée actualisée. HYP-023 reste `doing`, sans commit ni push.

### agent

Extension supplémentaire : `RuntimeFragment` accepte désormais les variables
avec liste d'arguments de types vide. `HasType.erase_runtimeFragment` en déduit
le typage Core lorsque l'environnement ne contient que des schémas d'arité
zéro ; `eval_safe_monoLetRuntimeFragment` transporte cette preuve à travers
le véritable `Core.eval`. La régression `eval_safe_boundIntLet` démontre un
`let` monomorphe dont le corps lit la valeur liée.

Cela couvre l'usage des liaisons monomorphes, pas l'instanciation d'un même
schéma à plusieurs types. Les fonctions, les valeurs paramétriques et les
motifs restent hors de ce pont. L'audit inclut le nouveau théorème ; validation
ciblée Lean réussie. HYP-023 reste ouvert, sans commit ni push.

### agent

La régression `identity_polymorphic_let_is_safe_at_fuel_20` complète le cas
exécuté déjà présent : le `let` identité partagé par les instanciations `int`
et `bool` rend à fuel 20 une paire Core dont les composantes satisfont
`ValTy`. C'est une vérification concrète à fuel fixé, auditée sous P45 ; elle
ne démontre pas la sûreté générale des schémas polymorphes.

Vérifications après l'ajout : `./scripts/validate.sh lean` compile l'ensemble
des 31 modules et réussit l'audit d'axiomes ; le contrôle Kanban valide 109
tâches, `git diff --check` passe et Graphify est actualisé. Le travail de
sûreté générale, les fonctions et la liaison du CLI restent ouverts. Aucun
commit ni push.

### user

Continuer le pont de sûreté en examinant les signatures nominales et le
fichier de démonstration mécanique fourni.

### agent

P47 ajoute une correspondance formelle entre les déclarations de constructeurs
et leur table Core après effacement des payloads. Le lemme
`constructorType_zeroArity` établit le lien pour une déclaration sans
paramètre ; `monoBoxValue_type_and_runtime_safe` vérifie sur un même terme le
typage polymorphe et la sûreté de son effacement dans le véritable évaluateur
Core, à tout fuel.

Ce jalon ne relie pas encore les constructeurs/motifs nominaux au théorème
général du fragment et ne traite pas les données paramétriques ; ces limites
sont ajoutées à la checklist et à la documentation. Le fichier
`demo/programs/mecanique/plaque_120x80.hyp` décrit un programme de démonstration
du DSL, mais ne relève pas du pont formel HYP-023 et n'a pas été modifié.

Validations : `validate.sh lean` avec audit d'axiomes (seuls axiomes Lean
standards), `validate.sh rapide`, `validate.sh graphe`, `kanban.py check`
(109 tâches) et `git diff --check` réussis. HYP-023 reste ouvert ; aucun push
effectué.

### user

Clarification d'architecture : le noyau reste générique ; le DSL compose des
fonctions/capacités typées et décrit les validations, tandis que les plugins
en fournissent le sens métier et que l'hôte lie les plugins autorisés.
L'OCR, Z3 et les validateurs sont des plugins. Le plan global P1 a été
approuvé ; reprendre HYP-023 en premier, sans benchmark LLM/GPU ni clôture
automatique des tickets en QA.

### agent

Le plan P1 est actualisé et le suivi de session synchronisé. `./scripts/validate.sh
lean` réussit sur les 31 modules avec l'audit d'axiomes. `graphify update .`
confirme que les fichiers `.lean` ne sont pas classifiés par l'extracteur
(69 fichiers non pris en charge) ; les requêtes ne peuvent donc pas fournir
les lignes des preuves HYP-023. Aucun fichier Lean n'a été lu ou modifié.
Pour respecter le contrôle de lecture demandé, l'inspection formelle est en
pause jusqu'à confirmation de la marche à suivre.

### user

### agent

Ajout de `PatTy.erase_monoCtorPattern` : un motif de constructeur d'une
déclaration sans paramètres est transporté vers `Core.PatTy` si son motif
payload appartient au fragment runtime déjà prouvé. La régression
`monoBoxPatternCase` est typée et sa sûreté à fuel arbitraire passe par le vrai
`Core.eval` ; un théorème confirme aussi le résultat concret à fuel 20.
L'audit d'axiomes et les documents P48 décrivent ce résultat comme un jalon
borné, pas comme l'intégration générale des motifs nominaux ni comme une preuve
pour les données paramétriques.

Le module ciblé compile avec `cd formal && PATH="$HOME/.elan/bin:$PATH" lake build Hypomnesis.Core.PolySoundness`.
`./scripts/validate.sh lean` réussit : 31 modules compilent, l'audit d'axiomes
accepte les nouvelles preuves et les tests du vérificateur de certificats
passent. `./.venv/bin/python scripts/kanban.py check` valide 109 tâches ;
`graphify update .` et `git diff --check` réussissent.

### user

Mettre à jour le Kanban avec le jalon de preuve Lean sur les motifs de constructeurs.

### agent

Kanban synchronisé avec le jalon P48 : l'itération 7 de la checklist documente
la preuve d'effacement du motif mono, la régression exécutée par `Core.eval`,
l'audit, la documentation et les validations ; ces éléments sont cochés.
HYP-023 reste en `doing` : l'intégration générale au `RuntimeFragment`, les
données paramétriques, les records et `Coverage.Certified` restent ouverts.
Je ne déplace pas la lane, qui relève de la décision utilisateur.

Validation constatée : `./scripts/validate.sh lean`, `./.venv/bin/python
scripts/kanban.py check` (109 tâches), Graphify et `git diff --check`.

### user

Pourquoi le travail bloque-t-il et que manque-t-il pour terminer les tickets ?

### agent

Diagnostic : il n'y a pas de blocage d'environnement ni de dépendance externe
pour HYP-023. Lean compile et l'audit passe ; HYP-020, sa dépendance, est déjà
en QA. J'ai toutefois laissé HYP-023 occuper tout l'avancement, jalon isolé
après jalon, au lieu de basculer aussi vers les P1 indépendants déjà prêtes.
C'est un problème de découpage et de pilotage de ma part, pas un obstacle sur
le Mac.

Ce qui manque à HYP-023 :

- P48 ne couvre qu'un exemple `monoBox` à déclaration sans paramètre. Il ne
  transporte pas encore les motifs nominaux dans `RuntimeFragment`.
- `Core.Ctx` donne un type unique par valeur runtime et `Core.Sig` efface les
  arguments des types de données. Le pont actuel ne permet donc pas de déduire
  la sûreté d'une même fermeture ou donnée paramétrique utilisée à plusieurs
  types ; il faut une relation runtime qui interprète les schémas/arguments de
  type, ou une spécialisation dont la préservation est prouvée.
- Le `List.map` présent est un exemple Lean autonome, pas le `List.map` réel du
  prélude et ses dépendances (`rev`, `fold_left`). Il faut vérifier ce dernier
  dans le fragment visé. Le branchement décodeur/CLI et les régressions de
  certificats sont des exigences supplémentaires de la checklist actuelle.
- Les records, motifs nominaux généraux et `Coverage.Certified` doivent rester
  préservés ; la checklist ne permet pas de les ignorer au nom de P48.

Le tableau Kanban indique aussi 11 tâches prêtes, dont HYP-152 (bindings de
services), et 71 en QA qui attendent une revue humaine. Les tickets en QA ne
sont pas « bloqués » techniquement, mais seul l'utilisateur les passe en
`done`. Les neuf tickets réellement bloqués attendent leurs dépendances
listées par Kanban. HYP-023 ne devrait donc pas empêcher HYP-152 ni les autres
travaux indépendants d'avancer.

Pour débloquer le flux, il faut découper HYP-023 en prochains jalons vérifiables
(intégration des constructeurs au fragment, relation polymorphe/runtime,
véritable `List.map` du prélude, puis branchement certificats/CLI et validation
complète) et travailler en parallèle sur les P1 prêtes au lieu d'attendre la
preuve générale avant tout autre ticket. Ne pas passer HYP-023 en QA tant que
ses critères et la validation complète ne sont pas satisfaits.

### user

### agent

HYP-023 reste le ticket de suivi en `doing` ; ses critères initiaux sont
conservés. Les livrables restants sont répartis en quatre sous-tickets, avec
leurs dépendances explicites :

- HYP-156 : relation runtime polymorphe et sûreté du véritable évaluateur.
- HYP-157 : constructeurs paramétriques, motifs, records et couverture certifiée.
- HYP-158 : véritable `List.map` du prélude et ses dépendances.
- HYP-159 : branchement décodeur/CLI et régressions de certificats.

HYP-157 suit HYP-156 ; HYP-158 suit HYP-156 et HYP-157 ; HYP-159 suit les
trois. La checklist parent conserve les validations globales et suit ces
livrables sans déclarer de travail terminé ni changer de lane.

### user

Redécouper les tickets trop gros en sous-tickets.

### agent

Découpage des tickets de taille L encore actionnables (`todo`, `doing` ou
`blocked`) en enfants vérifiables, sans déplacer de lane ni marquer de travail
terminé :

- HYP-023 → HYP-156 relation runtime polymorphe, HYP-157 constructeurs/motifs
  paramétriques et preuves liées, HYP-158 véritable `List.map` du prélude,
  HYP-159 branchement décodeur/CLI.
- HYP-056 → HYP-160 ADR, HYP-161 types et inférence dimensionnels,
  HYP-162 bibliothèque Units et exemple mécanique.
- HYP-057 → HYP-163 formalisation et sûreté, HYP-164 invariance d'échelle.
- HYP-152 → HYP-165 contrats typés, HYP-166 bindings hôte,
  HYP-167 vérifications statiques et permissions.
- HYP-153 → HYP-168 exécution/branches paresseuses, HYP-169 continuité de
  l'état symbolique, HYP-170 budgets, erreurs, annulation et traces.

Les tickets parents conservent leurs critères et restent des tickets de suivi.
HYP-154 et HYP-155 ne sont pas découpés : les choix de cycle de vie/arrêt des
services, de fournisseurs et de démonstrateur nécessitent un arbitrage qui
n'est pas fixé par leurs descriptions actuelles. Les tickets en QA et les
hypothèses sont hors du périmètre de ce découpage.

Vérifications : `kanban.py check` valide 124 tâches ; `./scripts/validate.sh
graphe` a reconstruit Graphify et réinjecté 212 nœuds/2395 relations Kanban.
Les tickets parents restent ouverts et aucun commit/push n'a été effectué.

### user
