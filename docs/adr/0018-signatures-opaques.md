# ADR 0018 — Signatures lexicales et scellement opaque

- Statut : acceptée par l'utilisateur (HYP-012).

## Décision

```hyp
module type S = sig
  val make : int -> t
  type t
  val read : t -> int
end
module M : S = struct
  type t = int
  let make x = x
  let read x = x
  let secret = 0
end
```

Les spécifications de types abstraits ou d'alias manifestes et de valeurs
sont indépendantes de leur ordre. Une signature est résolue dans son
environnement de déclaration, pas dans celui de son implémentation.
Les types et valeurs promis sont obligatoires, les membres supplémentaires
sont masqués. Les valeurs sont vérifiées par subsomption : une implémentation
peut être plus polymorphe que son interface, pas moins.

Chaque scellement introduit des identités abstraites distinctes. Les
constructeurs, champs et égalités de représentation ne traversent pas
`type t`. `type t = float` révèle au contraire cette égalité. Les alias
d'import partagent les mêmes identités, sans resceller le module.
Cette itération ne comprend ni foncteurs, ni `with type`, ni descriptions
de sous-modules ou de représentations algébriques dans les signatures.

## Frontière de vérification

La structure est élaborée dans son environnement privé. Des liaisons Core
explicites adaptent les instanciations polymorphes à la signature exportée.
L'export des certificats abaisse les types abstraits vers leur représentation
concrète, y compris dans les déclarations de types qui les utilisent.
Le format du certificat et la sémantique Lean ne changent pas.

Le checker Lean vérifie le programme après élaboration et abaissement.
Il ne prouve pas l'implémentation Python du scellement ni la confidentialité
de la représentation dans le certificat. L'opacité est une propriété du
typage du métalangage, pas un mécanisme cryptographique ou de sandbox.

Un contrat JSON dérivé d'un type opaque est refusé explicitement : publier
un codec de sa représentation contournerait son interface. Les catalogues
et exigences de documentation portent sur les seuls membres visibles.
