---
title: "HYP-041 · Registre de capacités et manifestes"
lane: doing
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-04T15:50:00+01:00
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
