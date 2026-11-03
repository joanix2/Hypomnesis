# ADR 0003 — Noyau pur, primitives natives par registre fermé

- **Statut :** acceptée
- **Date :** 2026-11-03

## Contexte

Le §9.1 impose que le noyau fonctionnel n'interagisse pas directement avec le monde extérieur,
et le §13.5 interdit l'exécution de code Python arbitraire généré par un LLM. Le langage a
pourtant besoin de primitives (arithmétique, chaînes, comparaison structurelle).

## Décision

- Les primitives sont déclarées dans le source avec `external nom : type = "symbole"`.
- Le symbole doit appartenir au `NativeRegistry` de la session ; un symbole inconnu est une
  erreur **statique**. Aucune syntaxe ne permet d'importer un module Python ou d'évaluer du code.
- L'arité déclarée par le type doit correspondre à l'arité enregistrée.
- Le prélude (`src/hypomnesis/stdlib/prelude.hyp`) n'utilise `external` que pour les
  primitives ; `List`, `Option`, `Result`, `String.concat`, `@`… sont écrits en Hypomnesis.
- Le registre par défaut ne contient que des fonctions totales ou échouant proprement
  (`failwith`, division par zéro) et **aucune primitive à effet** : pas d'entrée/sortie, pas
  d'horloge, pas d'aléa.
- Les effets (capteurs, actionneurs) seront des **valeurs** décrites par l'Effect IR et
  interprétées par le runtime d'effets (phase 5), jamais par une primitive native.

## Conséquences

- Une application hôte peut étendre le registre (nouvelles primitives pures) sans modifier le
  compilateur.
- Le REPL et la CLI affichent les valeurs des liaisons de premier niveau au lieu d'offrir un
  `print`, ce qui garde le noyau pur.
