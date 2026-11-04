# ADR 0006 — Le M3 est une théorie des types à deux niveaux, modale et graduée

- **Statut :** proposée
- **Date :** 2026-11-03
- **Analyse détaillée :** [m3-metalangage.md](../architecture/m3-metalangage.md)

L'arbitrage humain HYP-005 du 4 novembre 2026 adopte les trois axes
épistémiques dans la [v0.3](../specification/cahier-des-charges-v0.3.md), mais
maintient explicitement cette ADR **proposée pour expérimentation**.
Il n'adopte pas l'ensemble du calcul méta dépendant, modal et gradué ;
ce calcul n'est pas présenté comme déjà implémenté.

## Contexte

Le méta-métamodèle classique (MOF, Ecore) ne porte ni calcul, ni équations, ni connaissance,
ni effets, et sa réflexivité (« MOF est conforme à MOF ») est informelle. Hypomnesis a besoin
d'un M3 qui donne un sens précis à la conformité, à la substitution de plugins, à la
provenance et à la séparation des effets.

## Décision proposée

1. **Niveaux MDA = niveaux de jugement.** M2 = signatures ; M3 = règles de formation des
   signatures (cadre logique).
2. **Deux niveaux (2LTT).** Un niveau méta en λΠ-calcul modulo réécriture, total, porte
   théories, lois, règles et preuves. Le niveau objet est le langage ML de la phase 1 et sa
   Core IR, inchangés. Le méta produit l'objet par staging.
3. **Une théorie des modes fixée.** Objet, Méta et Monde, avec `⇑` (code typé) et l'adjonction
   `F ⊣ U`, dont dérive la monade d'effets. Aucune modalité n'exécute Monde depuis Objet.
4. **Grades.** La connaissance porte une modalité graduée sur un semi-anneau déclaré. La
   provenance est un polynôme de `ℕ[X]` ; grade, confiance et coût en sont des images
   homomorphes, et la révision applique `x ↦ 0`.
5. **Inconnues = métavariables.** Estimateurs, solveurs et générateurs résolvent des
   métavariables ; les validateurs rendent des certificats vérifiés par un noyau de confiance
   de type LCF.
6. **Réflexivité stratifiée.** Un univers de descriptions `Desc` avec `⌜Desc⌝ : Desc` au
   niveau suivant (lévitation), jamais `Type : Type`, et pas d'`eval` libre dans le fragment
   total.
7. Le statut `Derived` du §7.1 est une *forme de preuve* et non un grade. Les statuts se
   décomposent en trois axes : existence, support, cohérence.

## Conséquences

- La phase 2 est réorientée vers les métavariables et la provenance en semi-anneau, sans
  dépendre des types dépendants.
- Les théories sont d'abord des signatures de modules ML enrichies de lois, avec des modèles
  en style tagless-final. Le niveau méta λΠ vient en dernier.
- Le §7.1 du cahier des charges est à amender si la décomposition en trois axes est retenue.
- Risques : décidabilité avec réécriture, unification modulo théories, ergonomie. Les pistes
  sont détaillées au §9 de la note.
