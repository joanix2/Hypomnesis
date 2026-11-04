# ADR 0012 — Génération de programmes séparée du moteur

- Statut : acceptée
- Date : 2026-11-04

## Contexte

L'utilisateur souhaite concentrer ce projet sur le moteur symbolique et le métalangage,
tout en conservant les expériences de génération de programmes. Le module `hypomnesis.llm`
était livré avec le moteur, ses commandes dans la même CLI et ses dépendances dans
l'extra `dev`. Un simple sous-module ne rendait pas cette frontière installable ni testable.

## Décision

- Extraire ce code dans la distribution optionnelle `hypomnesis-codegen`, sous
  `packages/codegen/`, avec le module Python `hypomnesis_codegen`.
- Dépendance unidirectionnelle : Codegen consomme les API du moteur ; ni le moteur, ni
  le compilateur, ni le LSP n'importent Codegen ou ses bibliothèques.
- Déplacer catalogue de prompt, prompting, recherche d'exemples, client Ollama,
  traduction/réparation, benchmarks et graphiques avec leurs tests et instantanés.
- CLI dédiée `hypomnesis-codegen` : `decrire`, `benchmark-llm`, `graphiques-llm`.
  Les anciennes commandes et imports ne sont pas conservés en compatibilité, selon
  le choix explicite de l'utilisateur.
- Le noyau conserve parseur, documentation structurée du langage, types, IR, runtime,
  certificats Lean, effets, estimateurs, validateurs et solveurs symboliques.
  Les futurs transpileurs déterministes ne sont pas assimilés à la génération LLM.
- Les données de démonstration restent sous `demo/` (ADR 0011). L'adaptateur M2 de
  transcription déterministe reste une extension métier, sans dépendance au LLM.

## Conséquences

Le moteur et son extra `dev` s'installent sans Ollama, scikit-learn, Jinja2, SciPy ou
matplotlib. La CI vérifie son fonctionnement sans Codegen, et teste aussi les deux
distributions ensemble. Les tests de frontière interdisent les imports inverses.
La validation complète exige d'installer les deux paquets ; `pytest tests` reste le
point d'entrée des seuls tests symboliques.

Cette décision précise la frontière d'empaquetage des fonctionnalités de l'ADR 0009,
sans modifier les exigences de documentation ni la sémantique du langage. Aucun banc
LLM réel ne fait partie de cette extraction.
