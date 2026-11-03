# ADR 0001 — Prototype en Python, parsing LALR avec Lark

- **Statut :** acceptée
- **Date :** 2026-11-03

## Contexte

Le cahier des charges (§13.5, §15.1) fixe Python comme premier backend et Lark comme
technologie de parsing initiale. Le premier backend de plugins étant Python, un
interpréteur Python évite toute frontière de processus dans le MVP.

## Décision

- Le compilateur et le runtime V0 sont écrits en Python ≥ 3.11.
- La grammaire est une grammaire Lark **LALR(1)** (`src/hypomnesis/language/grammar/hypomnesis.lark`)
  avec lexer contextuel, plutôt qu'Earley :
  - les ambiguïtés sont détectées à la construction de la grammaire au lieu de produire des
    arbres ambigus à l'exécution ;
  - le parsing est linéaire, ce qui compte pour les programmes générés par LLM ;
  - les seuls conflits shift/reduce tolérés sont ceux d'OCaml (`match` imbriqué, application
    de constructeur dans les motifs), résolus en *shift*.
- Les opérateurs forment un ensemble fixe avec des niveaux de précédence explicites. Ils
  peuvent être redéfinis (`let ( +. ) a b = ...`) mais pas créés ; les opérateurs utilisateur
  arriveront avec la métaprogrammation (V0.3).

## Conséquences

- Les performances d'exécution sont celles d'un interpréteur Python ; le backend Rust/bytecode
  (V1.0) consommera la même Core IR.
- Les messages d'erreur de syntaxe s'appuient sur les terminaux attendus fournis par Lark.
