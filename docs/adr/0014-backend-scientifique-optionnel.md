# ADR 0014 — Backend scientifique optionnel

- Statut : proposée pour revue (implémentation HYP-054 en QA)
- Complète : ADR 0012, sans la modifier

## Contexte

L'estimateur de régression demandé par HYP-054 utilise scikit-learn.
Ce n'est pas de la génération LLM et il n'a pas à imposer une bibliothèque
scientifique à toutes les installations du moteur. L'ADR 0012 acceptée
doit conserver son texte historique ; la précision ajoutée pendant HYP-054
est donc déplacée ici.

## Décision proposée, mise en œuvre pour revue

L'extra explicite `sklearn` ajoute le backend de régression scientifique.
Il ne fait partie ni des dépendances de base ni de `dev`, et aucune
bibliothèque scientifique n'est importée avant construction explicite.
Le job core-only reste sans ces bibliothèques. Le backend est générique ;
données et sens physique restent en M2.

Les tests de frontière n'autorisent scikit-learn que dans ce backend et
dans cet extra, jamais Codegen, Ollama ou les autres dépendances LLM.
La suite `tests/optional` exige cet extra ; `pytest tests` couvre les tests
symboliques et optionnels, tandis que le job noyau l'exclut. Les scénarios
optionnels qui assemblent Codegen exigent aussi son installation explicite.

## Conséquences

L'isolation du noyau reste testable ; le modèle scientifique n'est ni
obligatoire ni confondu avec une preuve de validité. La validation humaine
de l'implémentation et de cette précision reste à effectuer en QA.
