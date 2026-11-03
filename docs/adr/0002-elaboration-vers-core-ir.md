# ADR 0002 — Typage sur l'AST et élaboration vers la Core IR

- **Statut :** acceptée
- **Date :** 2026-11-03

## Contexte

Le §13.3 définit une Core IR minimale (Literal, Variable, Lambda, Apply, Let, Match, Record,
Constructor). Il faut décider où se font la résolution des noms et le typage, et ce que voit
le runtime.

## Décision

1. L'inférence Hindley-Milner (algorithme W avec niveaux de Rémy pour la généralisation) opère
   sur l'AST de surface, ce qui permet des diagnostics positionnés dans le source.
2. Le vérificateur **élabore** en même temps la Core IR : il produit un programme où
   - chaque nom est résolu en variable locale (`Local`) ou globale pleinement qualifiée
     (`Global("Mechanics.area")`) ; les redéfinitions reçoivent un suffixe interne `#n`, de
     sorte que les fermetures existantes ne sont jamais affectées ;
   - le sucre syntaxique disparaît : `if`, `&&`/`||`, listes, `|>`, `@@`, opérateurs,
     paramètres-motifs et `function` deviennent des `Match`, `Apply` et `Construct` ;
   - les constructeurs portent leur étiquette d'exécution et leur rang de déclaration.
3. Le runtime n'exécute que de la Core IR ; il ne fait aucune résolution de noms.
4. Le vérificateur est incrémental (prélude, fichiers successifs, REPL) et transactionnel :
   une phrase rejetée laisse l'environnement inchangé.
5. Le langage étant pur (aucune référence mutable), toutes les liaisons `let` sont
   généralisées ; la restriction aux valeurs n'est pas nécessaire.

## Conséquences

- La Core IR est le contrat stable entre le frontend et tout futur backend.
- Les Domain IR, Problem IR et Effect IR (§13.3) seront produites à partir de la Core IR ou à
  côté d'elle, sans modifier le noyau fonctionnel.
