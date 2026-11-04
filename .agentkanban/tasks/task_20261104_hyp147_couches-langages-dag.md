---
title: "HYP-147 · Couches de langages réutilisables : imports et DAG de dépendances"
lane: qa
created: 2026-11-04T17:37:30+01:00
updated: 2026-11-04T18:19:29+01:00
description: "P1 · L · Métalangage · composer des descriptions symboliques par imports explicites"
priority: P1
tags: [architecture, dsl, metalangage, moteur-symbolique, tests]
---

## Conversation

### user

**Ticket** HYP-147 · **Priorité** P1 · **Taille** L · **Epic** Métalangage · **Labels** architecture, dsl, metalangage, moteur-symbolique

« il faudrait aussi créer un ticker pour avoir des layers DAG de dépendance entre les
description. si je défini la logique booléen ou aritmétique, je veux pouvoir les importé
dans d'autres languages »

#### Objectif

Définir une couche symbolique une seule fois et la réutiliser dans plusieurs langages :
logique booléenne, arithmétique, puis combinaisons et langages métier. Les « descriptions »
sont ici les définitions symboliques du langage (types, opérations, règles, contraintes,
et lois lorsqu'elles seront disponibles), pas seulement les commentaires de documentation.
Les dépendances entre couches forment un graphe orienté sans cycle.

Exemple conceptuel, sans imposer de syntaxe :

```text
LogiqueBooleenne ----\
                     > Contraintes --> LangageMetierA
Arithmetique -------/             \--> LangageMetierB
```

Les flèches ci-dessus indiquent la construction d'une couche à partir d'une autre.
L'export du graphe devra documenter précisément son orientation.

#### État actuel et articulation

- `load_language` charge les fichiers `sources` d'un seul manifeste, dans une session.
  Cela ne fournit pas encore d'import de couches indépendantes entre paquets de langages.
- Réutiliser les mécanismes de modules et de résolution de noms existants ; ne pas
  fabriquer une simple concaténation textuelle ou recopier les définitions.
- HYP-041 fournit le registre et la résolution de versions des extensions : réutiliser
  ses mécanismes si des contraintes de versions sont retenues, sans confondre extension
  de backend et paquet de langage.
- HYP-012 (signatures) et HYP-046 (théories avec lois) sont liés, mais ne doivent pas
  bloquer les premiers imports de couches avec les modules déjà disponibles.
- Fonction du moteur symbolique, indépendante du paquet Codegen/LLM de HYP-146.

#### Travail proposé

- Définir la frontière d'une couche importable : identité, sources, exports publics,
  documentation et dépendances explicites. Une bibliothèque symbolique doit pouvoir
  être importée sans définir une procédure métier exécutable.
- Proposer une syntaxe d'import et/ou une évolution du manifeste dans une ADR, avant
  implémentation ; préciser résolution locale, espaces de noms, visibilité et collisions.
- Construire le DAG transitif avec NetworkX, détecter les cycles en donnant leur chemin
  et charger les dépendances avant les couches qui les importent.
- Partager une dépendance commune sans double définition ni double chargement dans
  une même session, notamment dans un diamant d'import.
- Conserver types, signatures, descriptions et positions d'origine des déclarations :
  les erreurs doivent indiquer la couche et le fichier responsables.
- Exposer le graphe et ses niveaux de dépendance pour inspection, avec un format stable.
- Câbler les mêmes règles de résolution dans le chargement, `check`, l'exécution et le
  LSP, y compris les modifications non enregistrées de dépendances ouvertes.
- Préserver les manifestes existants sans import et leurs programmes.

#### Critères d'acceptation

- Une couche de logique booléenne et une couche arithmétique sont chacune définies une
  seule fois, importées et composées dans au moins deux langages distincts.
- Un programme du langage composé peut utiliser les symboles importés avec leur vrai
  typage ; un appel mal typé est rejeté avant exécution.
- Un import transitif et un diamant fonctionnent ; une dépendance commune n'est chargée
  qu'une fois par session.
- Cycle, dépendance absente et collision ambiguë produisent un diagnostic explicite,
  sans masquer l'erreur par un chargement partiel présenté comme réussi.
- Le DAG exporté permet de retrouver les dépendances et les couches topologiques.
- CLI et LSP donnent des résultats cohérents avec les sources importées.
- Tests de régression des langages actuels, documentation et exemple de création
  d'une couche réutilisable ; validation complète et obligations Lean si la Core IR
  ou sa sémantique doivent changer.

#### Fichiers concernés

- `src/hypomnesis/engine/language.py`
- `src/hypomnesis/language/`
- `src/hypomnesis/contracts/schemas/language-manifest-1.0.0.json`
- `src/hypomnesis/lsp/`
- `src/hypomnesis/cli.py`
- `tests/`
- `demo/languages/`
- `demo/programs/`
- `docs/architecture/`
- `docs/adr/`

#### Références

- HYP-012, HYP-041, HYP-046, HYP-146.
- `docs/architecture/m3-metalangage.md`.
- Conventions et définition de fini : `.agentkanban/memory.md`.

### agent

Ticket créé à la demande de l'utilisateur, priorité proposée P1. Il concerne la
composition réelle des langages symboliques, pas les dépendances entre tickets ni
la génération de prompts. Aucun développement de cette fonctionnalité lancé.
La syntaxe, les règles de visibilité et les éventuelles versions seront à décider
pendant sa phase de planification.

### user

Continuer l'implémentation. Précision : « je pense que language.json doit disparaitre
au profit d'une déclaration directement dans le language ».
Choix confirmés : remplacer les anciens manifestes sans compatibilité et intégrer
toute la configuration actuelle dans la déclaration `.hyp`.

### agent

Plan et checklist établis (ADR 0013) : déclaration statique `language nom = { … }`,
imports locaux de dossiers ou fichiers `.hyp`, définition des symboles par les modules
existants. Entrée conventionnelle `langage.hyp`, bibliothèques sans procédure autorisées.
Partage d'un résolveur DAG pour chargement, CLI, LSP et catalogue Codegen ; validation
des branches dans leur fermeture propre, déduplication des diamants, refus des cycles
et collisions. Migration des démonstrations et tests, sans changer la Core IR ni
la sémantique du runtime. Registre distant et versions d'import hors périmètre.
Les changements Codegen précédents sont conservés ; pas de commit ou push prévu.

### user

« pour les input et les output on a juste besoin de décorateur python »
Précisions confirmées : tous les points Python (capteurs, actionneurs, environnement,
transcription) sont déclarés par décorateurs ; les modules sont indiqués explicitement
et ne sont jamais importés pendant `check` ou l'analyse LSP.

### agent

Périmètre ajusté : `adapters` liste des modules Python locaux dans la déclaration
`.hyp`, sans références `fichier.py:fonction`, tables de capteurs ou actionneurs dans
la configuration. Ajout de `@sensor`, `@actuator`, `@environment`, `@transcriber`,
découverte à l'exécution seulement et registre propre à chaque langage.

### user

### agent

Implémentation terminée : `language nom = { … }` est une déclaration statique native
avec AST et positions, et les manifestes JSON des démonstrations sont supprimés.
Bibliothèques sans procédure, imports relatifs de fichiers ou dossiers, vérification
des fermetures propres à chaque branche, partage transitif/diamants, confinement des
ressources du paquet, diagnostics d'origine et refus des cycles/identités/collisions
sont implémentés. `hypomnesis layers LANGAGE` exporte le DAG et ses couches.

Les modules explicitement déclarés portent les décorateurs Python demandés :
`@sensor`, `@actuator`, `@environment`, `@transcriber`. Découverte à l'exécution,
contrôle des signatures et des identifiants, pas d'héritage implicite des I/O ou
permissions d'une dépendance. `check` et le LSP n'importent aucun adaptateur et
n'évaluent pas les définitions ; les certificats gardent leur frontière de prélude.

Le LSP utilise les déclarations et sources transitives non enregistrées et n'analyse
pas les sources suivantes quand on édite un fichier antérieur. Catalogue et prompt
Codegen utilisent le même plan ; leurs instantanés historiques restent identiques.
Les couches `booleen` et `arithmetique`, composées via `contraintes`, sont réutilisées
par `composition_a` et `composition_b` avec deux programmes d'exemple.

Validation complète verte : 735 tests (658 moteur, 77 Codegen), Ruff, Pyright des
deux distributions, schémas, Kanban, Lean et audit/certificat. Roues construites
depuis leurs archives source : indépendance LLM du cœur confirmée ; 70 tests de
composition/I/O/démonstrations et 77 tests Codegen réussis sur les paquets installés.
Sept tests TextMate, TypeScript, test dans un hôte VS Code réel et VSIX réussis ;
extension mise à jour dans VS Code. Graphe rafraîchi, dossiers temporaires nettoyés,
aucun résultat généré dans le dépôt. Documentation et ADR 0013 complétées.

Core IR et runtime inchangés. Aucun banc LLM réel, commit ou push ; changements
Codegen précédents conservés. Couloir inchangé, vérification humaine à effectuer.

### user

Est-il possible d'utiliser le graphe de dépendances des tickets pour les traiter en
parallèle avec des sous-agents sur des branches différentes ?

### agent

Oui. Le graphe Kanban existant peut alimenter un ordonnanceur de tâches prêtes :
dépendances intégrées et validées, sélection par priorité, puis exclusion des travaux
qui modifient les mêmes surfaces ou interfaces. Chaque agent doit avoir sa branche
et son propre worktree Git ; des branches seules dans un dossier partagé ne suffisent pas.

Flux recommandé : stabiliser et committer le travail actuel avant de créer les worktrees,
commencer avec deux agents, leur attribuer des tâches bornées et leurs checklists,
valider chaque branche, puis intégrer séquentiellement sur une branche d'intégration
avec validation complète après chaque fusion. Débloquer les successeurs seulement après
intégration de leurs dépendances. Les statuts Kanban, fichiers de documentation partagés
et reconstructions Graphify doivent être coordonnés par l'orchestrateur.

Le calcul des tâches prêtes existe (`scripts/kanban.py status --json`), mais l'exécution
multi-worktrees et l'intégration ne sont pas automatisées actuellement. Aucun agent,
branche, worktree ou commit lancé pour cette question.

### user

Commit tout.

### agent

Autorisation de committer tous les changements en attente : extraction Codegen
(HYP-146), déclarations natives et DAG des couches, décorateurs Python (HYP-147),
démonstrations, tests, extension VS Code, documentation et suivi Kanban.
Validation complète avant commit ; caches, dépendances et résultats générés exclus.
Aucun push ni lancement de sous-agents inclus dans cette demande.

### user

Peux-tu mettre le Kanban à jour ?

### agent

Réconciliation du tableau avec les implémentations et validations enregistrées :
HYP-004, HYP-131, HYP-132, HYP-144, HYP-145, HYP-146 et HYP-147 passent de `todo`
à `qa`, avec leurs checklists. HYP-147 et l'extraction Codegen sont committés dans
`6e2962f` ; validation intégrée verte (735 tests, Python/Lean et extension VS Code).
Les couloirs des anciennes checklists sont synchronisés avec leurs tickets et
les cases de validation devenues obsolètes sont régularisées.

HYP-007 reste bloqué par HYP-014 et sa comparaison réelle avant/après ; HYP-139
reste en cours, ses mesures GPU et critères réels n'étant pas attestés.
La CI distante attestée pour HYP-004 concerne le commit publié `7d89099`, pas les
commits locaux suivants. Aucun ticket passé en `done`, aucun push ni exécution
parallèle lancé. Le contrôle Kanban et la réinjection du graphe sont à vérifier
sur cette mise à jour documentaire.

### user

### agent

Vérifications de cette mise à jour réussies : 101 tickets valides, aucune
désynchronisation ticket/checklist, `git diff --check` vert. Graphe Kanban
réinjecté : 181 nœuds et 863 relations. Bilan du tableau : 70 `todo`, 2 `doing`,
26 `qa`, 3 `done`. Seuls le suivi Kanban et la mémoire projet ont été modifiés ;
aucun code ni test changé. Modifications non committées et non poussées.

### user

Continuer avec plusieurs tickets symboliques sur des worktrees séparés.
Plan confirmé : HYP-044, HYP-051 et nouvel ordonnanceur réutilisable HYP-148,
maximum trois travaux, intégration locale séquentielle validée, aucun push.

### agent

Kanban committé dans `baa3130`, cadrage/checklists dans `2deee5b`.
Trois branches et worktrees isolés plus un worktree d'intégration préparés,
environnements Python séparés vérifiés. Les agents d'implémentation et de revue
n'avaient aucun outil disponible : aucun changement de leur part. Reprise directe
par le coordinateur, sans prétendre à une exécution parallèle réussie des agents.

HYP-044, HYP-051 et HYP-148 sont livrés sur leurs branches puis intégrés
séquentiellement, avec validation complète après chaque merge. Backend Python
contractuel avec timeout, Problem IR/JSON/plans déclaratifs, CLI locale de
coordination des worktrees. Lot intégré : 784 tests et validation Python/Lean verts.
Les trois tickets passent en `qa`, jamais en `done`. Revue indépendante non
réalisée faute d'outils ; relecture directe et tests enregistrés dans chaque ticket.
Documentation centrale et graphe à rafraîchir avant avance rapide finale de `main`.
Aucun travail LLM ni push.

### user

### agent

Validation finale de l'arbre consolidé réussie : 784 tests collectés et exécutés,
707 moteur et 77 Codegen, sans tests ignorés sur cette dernière exécution ;
Ruff, Pyright des deux paquets, schémas, Kanban, Lean/audit/certificat verts.
Graphify rafraîchi sans appel LLM et relations Kanban réinjectées.
102 tickets valides. Les branches de travail sont conservées ; la branche
d'intégration propre est prête pour l'avance rapide locale de `main`.

### user
