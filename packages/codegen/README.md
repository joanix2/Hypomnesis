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
hypomnesis-codegen decrire demo/languages/mecanique --plugin chemin/manifestes/
hypomnesis-codegen benchmark-llm demo/languages/ventilation --modeles MODELE --sans-graphiques
hypomnesis-codegen graphiques-llm chemin/resultats.json
```

Les imports `hypomnesis.llm.*` deviennent `hypomnesis_codegen.*`.
La traduction s'utilise via `hypomnesis_codegen.translation.translate`. Le compilateur
reste responsable de vérifier les candidats ; le moteur conserve l'exécution et les
permissions. Aucun serveur ni modèle n'est lancé à l'installation.

`decrire` sélectionne le domaine par son langage et suit son DAG sans
importer ses adaptateurs. Le JSON et le Markdown incluent les signatures
publiques documentées, contrats et modules adaptateurs déclarés.
`--plugin` publie les métadonnées des seuls manifestes fournis par l'hôte,
sans charger leurs backends ; leurs permissions sont **requises**, jamais
accordées par cette publication. Le catalogue mécanique est testé sous
16 Kio UTF-8 ; ce budget explicite est une mesure de texte, pas une promesse
sur le tokenizer d'un modèle donné.

`translation.translate(client, model, language, request, examples=[],
max_repairs=2)` effectue au plus trois appels. Le client injecté implémente
`ChatClient` ; le client réseau optionnel existant est Ollama. Les erreurs
du compilateur alimentent les réparations. Un budget négatif, booléen ou
non entier est refusé avant tout appel. Un échec final conserve chaque
tentative et son diagnostic, sans renvoyer un programme accepté par défaut.

La vérification charge M2/M1 **statiquement**, sans évaluer le candidat :
être bien typé ne signifie ni terminer, ni être valide, ni être autorisé.
Une simulation supplémentaire n'a lieu qu'avec le callback `simulate`
explicitement fourni par l'hôte. Les tests emploient des réponses figées
(`model="fixture"`), pas un service ou modèle prétendument réel.

## Hypothèses et informations manquantes

Après vérification, l'hôte peut matérialiser les données pures du candidat,
puis appeler `hypotheses.capture_input(checker, type_fermé, valeur, base,
key="demande")`. Le type vient de M2 et de l'hôte, pas du texte généré.
Les feuilles concrètes sont des faits Hypothesis (confiance non étayée 0),
les options `None` deviennent des `MetaVar` typées sans proposition.
Records, alias, variants, listes et tuples sont parcourus.
`GeneratedInput.report()` liste les faits et les manques avec type et état.
Ni cette API ni la validation de types ne résolvent un trou implicitement.
Un estimateur choisi par l'hôte fournit une proposition puis l'hôte la résout.

Lors d'une exécution de candidat, utiliser impérativement
`run_procedure(..., generated=True)`. Le banc Codegen le fait. La CLI
`hypomnesis lancer --demande ...` le fait également ; un fichier de provenance
générée doit porter `--generated`. Un fichier ne révèle pas son auteur :
la provenance reste une décision de l'hôte. Le mode historique par défaut
est conservé pour les programmes déclarés de confiance.

En mode généré, **tous** les `Record` restent Hypothesis, même une revendication
Given, Estimated ou Derived ; seules les lectures réellement validées par
Observe peuvent être Observed. Cette politique conservatrice couvre aussi
les Record d'un M2 appelé par le candidat. Une estimation indépendante doit
être enregistrée par le chemin d'estimateur de l'hôte, pas auto-certifiée par
une constante M1. Les permissions et la validité métier restent des contrôles
distincts ; Hypothesis ne signifie pas automatiquement autorisé ou interdit.

Les résultats vont par défaut dans `demo/sortie/benchmark-llm/`, ignoré dans Git.
`benchmark.json`, les sources M2 et les exemples M1 restent des données des langages,
pas du code du moteur ni du paquet Codegen.

## Tests

```bash
pip install -e '.[dev]' -e packages/codegen
pytest packages/codegen/tests
```

Les tests utilisent des clients simulés : aucun appel LLM ni téléchargement de modèle.
Les instantanés du catalogue fixent le prompt octet pour octet ; tout changement
intentionnel doit être documenté et remesuré avant comparaison des anciens bancs LLM.
