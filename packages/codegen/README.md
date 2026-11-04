# Hypomnesis Codegen

Paquet optionnel de génération de programmes par LLM, indépendant de la distribution du
compilateur et du métalangage. Il **dépend de** `hypomnesis`, jamais l'inverse.

Il regroupe le catalogue de prompt, les stratégies de prompting, le mini-RAG, le client
Ollama, la traduction langage naturel → programme M1 et ses réparations, les benchmarks
et leurs graphiques. Il ne contient ni compilateur, ni solveur symbolique.

## Installation depuis le dépôt

Depuis la racine :

```bash
pip install -e . -e packages/codegen
```

Le moteur seul reste installable avec `pip install -e .` ; ses outils de développement
(`pip install -e '.[dev]'`) n'installent pas Codegen ni ses dépendances.

## CLI et API

Les anciennes commandes LLM quittent la CLI `hypomnesis`, sans alias de compatibilité :

```bash
hypomnesis-codegen decrire demo/languages/ventilation
hypomnesis-codegen decrire demo/languages/mecanique --format json
hypomnesis-codegen benchmark-llm demo/languages/ventilation --modeles MODELE --sans-graphiques
hypomnesis-codegen graphiques-llm chemin/resultats.json
```

Les imports `hypomnesis.llm.*` deviennent `hypomnesis_codegen.*`.
La traduction s'utilise via `hypomnesis_codegen.translation.translate`. Le compilateur
reste responsable de vérifier les candidats ; le moteur conserve l'exécution et les
permissions. Aucun serveur ni modèle n'est lancé à l'installation.

Les résultats vont par défaut dans `demo/sortie/benchmark-llm/`, ignoré dans Git.
`benchmark.json`, les sources M2 et les exemples M1 restent des données des langages,
pas du code du moteur ni du paquet Codegen.

## Tests

```bash
pip install -e '.[dev]' -e packages/codegen
pytest packages/codegen/tests
```

Les tests utilisent des clients simulés : aucun appel LLM ni téléchargement de modèle.
Les instantanés du catalogue doivent rester identiques octet pour octet.
