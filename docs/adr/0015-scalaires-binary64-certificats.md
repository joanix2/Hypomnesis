# ADR 0015 — Scalaires binary64 et certificats 1.1

- Statut : proposée pour revue ; implémentation HYP-150.

## Contexte

Les exemples utilisent des floats Python et des chaînes Unicode. Des réels
exacts ou des chaînes représentées uniquement par des points de code dans
un exemple ne décrivent pas leur exécution. Le parseur JSON Lean normalise
le zéro négatif en zéro positif.

## Décision proposée

Utiliser Float de Lean 4.35, avec son modèle logique binary64 pour
add/sub/mul/div, et String Unicode. Catalogue fermé de signatures et
comportements ; aucun axiome de signature fourni par le certificat.
L'égalité flottante est IEEE ; les comparaisons d'ordre suivent compare
du runtime (NaN avant toute autre valeur). Les erreurs de primitives sont
distinctes du blocage et de l'échec de filtrage.

Écrire certificate/1.1.0 : chaque littéral flottant fini porte sa valeur
numérique et ses bits IEEE, vérifiés. Garder le schéma 1.0 intact et sa
lecture Python ; réexporter les anciens floats avant certification Lean.

## Conséquences

La sûreté du typage et la correction/complétude restent prouvées sur le
fragment étendu ; ce n'est pas une preuve de raffinement Python complète,
ni une garantie d'exactitude réelle ou physique. Les primitives non
modélisées restent explicitement refusées.
