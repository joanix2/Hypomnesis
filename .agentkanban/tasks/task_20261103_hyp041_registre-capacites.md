---
title: "HYP-041 · Registre de capacités et manifestes"
lane: todo
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-04T15:50:39+01:00
description: "P0 · M · Phase 3 — Extensions et contrats · dépend de HYP-040"
---

## Conversation

### user

**Ticket** HYP-041 · **Priorité** P0 · **Taille** M · **Epic** Phase 3 — Extensions et contrats · **Dépend de** HYP-040 · **Labels** python, contrats

#### Contexte

§6.1 : une extension doit être découvrable et inspectable sans exécuter son code métier. Le schéma `extension-manifest/1.0.0` existe déjà dans `src/hypomnesis/contracts/schemas/`.

#### Tâches proposées

- `engine/registry.py` : charger des manifestes JSON, les valider, indexer par identifiant, rôle et version.
- Résolution de dépendances entre extensions avec contraintes de version.
- `hypomnesis plugins list|show` dans la CLI.

#### Critères d'acceptation

- Un manifeste invalide est refusé à l'enregistrement.
- L'inspection ne charge pas le code Python de l'extension (vérifié par test).

#### Fichiers concernés

- `src/hypomnesis/engine/registry.py`
- `src/hypomnesis/cli.py`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`

### agent

Note de HYP-040 : les neuf protocoles existent dans `src/hypomnesis/capabilities/` (`protocols.py`). `ROLES` associe chaque valeur de l'énumération `role` du manifeste à son protocole (cohérence testée) ; `roles_of(plugin)` rend les rôles qu'un objet satisfait structurellement ; `guarded` (`safe.py`) contient les exceptions d'un plugin dans un `Result`. Le registre peut donc vérifier, après chargement du module (jamais à l'inspection), que l'objet lié à un manifeste de rôle `R` satisfait `ROLES[R]`. Les protocoles sont `runtime_checkable` : seule la présence des méthodes est contrôlée, pas leurs signatures.

### user

### agent

2026-11-04 — Activation de HYP-041 après confirmation dans le chat : **plan → todo →
implement**. Le travail de ce dépôt se concentre désormais sur le moteur symbolique et le
métalangage ; les expérimentations LLM et la traduction du langage naturel sont menées à part.

Préalable : fusion de `origin/llm` dans `main` en avance rapide (39 commits, sans conflit).
L'environnement de ce Mac a été préparé avec Python 3.12, les dépendances `dev` et Lean 4.35.
La validation a révélé une incompatibilité de `mktemp --suffix` avec macOS ; correction
autorisée explicitement par l'utilisateur avant revalidation et publication de la fusion.

Plan HYP-041 :

1. Réutiliser `SchemaRegistry` et `extension-manifest/1.0.0` pour enregistrer des manifestes
   JSON, sans importer ni instancier les backends. Refuser les doublons contradictoires.
2. Indexer les extensions par identifiant, rôle et version. L'inspection reste possible
   même si une dépendance n'est pas encore installée.
3. Résoudre explicitement les dépendances et contraintes de version, y compris les
   dépendances transitives, conflits et cycles ; rendre un ordre dépendances avant dépendants.
   Réutiliser des bibliothèques courantes pour les versions et la résolution plutôt que
   réimplémenter leurs règles.
4. Ajouter `hypomnesis plugins list|show` avec chemins de manifestes explicites, sélection par
   rôle/version et diagnostics lisibles ; aucune découverte n'exécute du Python.
5. Tester les refus, la résolution et les commandes, avec un backend piégé qui échouerait
   s'il était importé. Documenter l'API et les limites ; validation complète avant publication.

Le chargement effectif des backends reste dans HYP-044 ; ni la Core IR ni sa sémantique ne
changent ici. Le couloir reste géré par l'utilisateur/l'extension conformément à INSTRUCTION.md.

### user

### agent

2026-11-04 — Implémentation engagée sur `hyp-041-registre-capacites`.
Choix : `semantic-version` pour SemVer/SimpleSpec, `resolvelib` pour la sélection cohérente
avec backtracking, NetworkX existant pour le graphe sélectionné et son ordre topologique.
L'enregistrement par lot et par chemins est atomique ; inspection et résolution rendent des
copies profondes. L'inspection n'exige pas les dépendances installées.

Écart nécessaire découvert par les tests : le `$ref` de version du manifeste vers l'enveloppe
refusait les métadonnées `+build` pourtant valides en SemVer. Le champ `version` du seul schéma
de manifeste accepte désormais SemVer 2.0.0 complet ; l'enveloppe n'est pas modifiée.
Les cycles sont refusés dans le graphe sélectionné, après résolution ; aucune recherche
supplémentaire de solution acyclique. Le garde-fou de résolution est de 10 000 tours.

Contrairement au constat initial, `graphify update .` est disponible et a reconstruit le graphe
local avec succès. Aucun paquet Graphify n'a été installé.

### user

### agent

2026-11-04 — **HYP-041 implémentée et vérifiée ; contrôle utilisateur attendu en `qa`.**

Livraison :

- `src/hypomnesis/engine/registry.py` : `ExtensionRegistry`, API `add`, `add_many`, `load`,
  `load_paths`, `ids`, `versions`, `list`, `show`, `resolve`. Validation par
  `SchemaRegistry`/`MANIFEST_ID`, index par id/rôle/version, lots atomiques, doublons
  contradictoires refusés, copies profondes à l'entrée et à la sortie.
- Résolution transitive SemVer : une version cohérente par id, backtracking et ordre
  dépendances avant dépendants ; erreurs distinctes pour manifeste invalide, doublon,
  absence, conflit de versions et cycle.
- `src/hypomnesis/cli.py` : `plugins list --manifest CHEMIN [--manifest CHEMIN …] [--role ROLE]`
  et `plugins show ID --manifest CHEMIN [--version VERSION]`. JSON indenté ; chemins explicites
  seulement ; dossiers non récursifs ; aucune résolution imposée à l'inspection.
- `pyproject.toml` : seules nouvelles dépendances, `semantic-version>=2.10,<3` et
  `resolvelib>=1.2,<2` (NetworkX réutilisé).
- `src/hypomnesis/contracts/schemas/extension-manifest-1.0.0.json` : SemVer 2.0.0 complet,
  y compris préversions arbitraires et métadonnées `+build`, sans règle PEP 440.
- `tests/unit/test_extension_registry.py`, `tests/unit/conftest.py`,
  `tests/unit/test_cli_contract.py`, `tests/contracts/test_contracts.py` : 55 nouveaux tests.
  Backend piégé importable qui créerait un fichier puis lèverait : API et CLI vérifient
  qu'aucun import ni effet n'a lieu. Couverture des mutations, invalides, lots atomiques,
  neuf rôles, versions multiples, backtracking, dépendances transitives et absentes,
  conflits, cycles, erreurs d'usage et sorties JSON.
- `TECHNICAL.md`, `README.md` : API, exemples, contraintes, erreurs et limites documentés.
  Tâche et checklist actualisées sans réécriture des anciens messages.

Vérifications (avec `PATH="$PWD/.venv/bin:$HOME/.elan/bin:$PATH"`) :

- `pytest tests/unit/test_cli_contract.py tests/unit/test_extension_registry.py tests/contracts/test_contracts.py`
  : **85 tests passent**.
- `ruff check .`, `ruff format --check .`, `pyright` : verts, aucune erreur de typage.
- `./scripts/validate.sh` : vert, **555 tests** (baseline : 500).
- `./scripts/validate.sh complet` : vert, tous les hooks pre-commit, schémas, workflows,
  tests, compilation Lean, audit des axiomes et vérificateur de certificats.
- Diff relu après pre-commit : aucune correction automatique supplémentaire ;
  `git diff --check` vert.
- `graphify update .`, puis `./scripts/validate.sh graphe` : verts ; graphe local reconstruit
  et enrichi du Kanban, fichiers générés ignorés par Git. Aucune installation Graphify.

Commits locaux :

- `2c4767a` — HYP-041 : ajouter le registre statique et la résolution SemVer
  (validation rapide verte : 542 tests).
- `cc3d584` — HYP-041 : exposer l'inspection statique des extensions dans la CLI
  (rapide et complet verts : 555 tests).
- Le présent bilan est conservé dans le commit « HYP-041 : consigner la validation et préparer
  la vérification utilisateur ». Aucun push ni fusion.

Écarts et limites : correction ciblée du champ SemVer du manifeste, explicitée ci-dessus.
Les cycles du graphe sélectionné sont refusés après résolution, sans rechercher une autre
sélection acyclique ; limite de 10 000 tours du résolveur. Dossiers inspectés sans récursion ;
aucune découverte de paquets, lecture distante de schémas ou vérification du code backend.
Le chargement et la conformité aux protocoles restent dans HYP-044.
Ni Core IR, ni runtime, ni formalisation, ni tickets LLM, ni `scripts/validate.sh`, ni
`CONTRIBUTING.md` modifiés. Aucun blocage restant pour HYP-041 ; vérification humaine à faire.

### user

### agent

Complément de vérification finale : après les premiers rafraîchissements Graphify réussis,
une nouvelle exécution de `./scripts/validate.sh graphe` a été refusée par le garde-fou de
Graphify : nœud sémantique `kanban_path_src_hypomnesis_engine_registry_py` absent du graphe
reconstruit. Le graphe précédent a été préservé ; la réinjection du Kanban seule a réussi.
Le défaut d'outillage est consigné dans **HYP-144**, sans correction hors périmètre et sans
contournement du garde-fou. Il n'affecte pas les validations rapide/complet ni HYP-041.
La liste de fichiers comprend donc aussi la fiche
`.agentkanban/tasks/task_20261104_hyp144_graphify-rafraichissement-kanban.md`.

### user

### agent

2026-11-04 — Contrôle final : validation complète relancée avec succès sur les 555 tests,
les linters, le typage, les schémas, Lean et les certificats. La CI de la fusion LLM sur
`main` est également verte (exécution 41850422329).

Correction administrative : le sous-agent avait passé la tâche en `qa`, contrairement à
la consigne de laisser le couloir à l'utilisateur/l'extension. Le couloir initial `todo`
est rétabli ; cela ne remet pas en cause l'implémentation vérifiée et prête pour revue humaine.
Les commits locaux du sous-agent sont conservés sans réécriture.
Publication par fusion en avance rapide dans `main`, conformément au workflow du projet.
La limite sur les cycles et le défaut Graphify HYP-144 restent explicités ci-dessus.

### user
