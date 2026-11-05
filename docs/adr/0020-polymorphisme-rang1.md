# ADR 0020 — Polymorphisme explicite de rang 1 dans le noyau vérifié

- Statut : approche acceptée par l'utilisateur (plan HYP-023) ;
  implémentation en cours, fondations des types seulement.

## Contexte

L'IR Python et les certificats portent les quantificateurs des schémas et
les arguments de leurs instanciations. Le noyau Lean utilisé par le CLI
reste monomorphe : le décodeur spécialise les globales et les données
atteignables. Cela ne prouve ni le typage générique d'une définition ni
la généralisation au let.

## Décision

Formaliser explicitement le rang 1 : monotypes sans quantificateur interne,
schémas au let et instanciations explicites. Les paramètres de fonctions
et les occurrences récursives restent monomorphes. Ni rang supérieur ni
récursion polymorphe ; l'algorithme d'inférence W reste hors preuve.

Les variables de types sont des indices de de Bruijn. Dans le corps d'un
schéma d'arité `n`, les indices strictement inférieurs à `n` sont liés ;
les indices suivants désignent les variables du contexte extérieur.
Une substitution sous un schéma protège ces `n` variables et affaiblit
ses images pour éviter leur capture. L'instanciation exige exactement
`n` arguments, retire ces liaisons et conserve les variables extérieures.

Les données nominales portent leurs arguments de types. Une signature
déclare le nombre de paramètres et les types paramétriques des arguments
de ses constructeurs. Leur vérification de portée contrôle les indices
de données, les arités et les variables des types imbriqués.

## Mise en œuvre progressive et frontière

`Core/PolyTypes.lean` établit d'abord cette algèbre, les environnements
de schémas et leurs lemmes, avec des régressions compilées dans
`Core/PolyTypeExamples.lean`. Il est importé par le point d'entrée de la
bibliothèque et ses propriétés sont auditées.
La représentation historique est conservée pendant cette étape pour ne
pas retirer une garantie existante avant son adaptation.

Ce module n'est pas un second interpréteur et n'est pas encore utilisé
par `Core.typeOf` ou le décodeur. L'inclusion `Ty.ofCore` ne concerne que
les types : **elle ne constitue pas un pont conservatif des programmes**.
Le test du schéma de map ne vérifie pas le corps du véritable `List.map`.
HYP-023 reste ouvert jusqu'au typage des termes, à la sûreté, à la
préservation des garanties existantes et au branchement du checker réel.

Une éventuelle représentation distincte des termes devra posséder un
pont conservatif prouvé pour le fragment historique ; les tests seuls
ne remplaceraient pas cette obligation. Aucune substitution par une
monomorphisation, un exemple isolé ou un interpréteur réduit n'est acceptée.
