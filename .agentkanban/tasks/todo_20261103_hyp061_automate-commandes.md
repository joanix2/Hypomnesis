---
title: "HYP-061 · TODO"
lane: todo
created: 2026-11-04T14:30:00+01:00
updated: 2026-11-04T14:30:00+01:00
description: "Checklist de HYP-061"
---

# Iteration 1

État des lieux : `effects/dispatcher.py` enchaîne déjà Created → Validated → Authorized → Dispatched → Completed/Failed (+ Rejected, DryRun, Simulated) mais **sans table de transitions explicite**, sans état `Accepted`, sans délai d'expiration, sans politique de relance ni déduplication par `command_id`. Ce ticket extrait et complète l'automate ; la validation/permission (HYP-062) et le transport (HYP-063) restent hors périmètre. Sans GPU.

Fichiers : `src/hypomnesis/effects/commands.py` (nouveau), `src/hypomnesis/effects/dispatcher.py` (branchement), `tests/unit/test_commands.py` (nouveau). `tests/unit/test_effects.py` et `tests/integration/test_demo_plaque.py` ne doivent pas changer d'attentes.

- [ ] Lire §9.7 du cahier des charges ; figer dans le ticket la liste des états (Created, Validated, Authorized, Dispatched, Accepted, Completed, Rejected, Failed, Expired, + DryRun/Simulated de l'état de mode) et des états terminaux
- [ ] `commands.py` : `State` (Enum) et table `TRANSITIONS: dict[State, frozenset[State]]` ; fonction `can_move(a, b)` ; les états terminaux sont absorbants
- [ ] `CommandRecord` : `command_id`, état, historique `(état, détail)`, nombre de tentatives, échéance ; méthode `move(state, detail)` qui lève `IllegalTransition` si la table l'interdit
- [ ] Politique de relance `RetryPolicy` (tentatives max, délai) avec horloge injectée (aucun `time.sleep` dans les tests) ; `idempotent: bool` porté par la commande/l'actionneur
- [ ] Règle : une commande **non idempotente** n'est jamais relancée automatiquement après `Dispatched` ; une commande idempotente l'est jusqu'à la limite
- [ ] Déduplication par `command_id` : redonner la même commande rend l'issue existante, sans second appel à l'actionneur
- [ ] Expiration : une commande dépassant son échéance passe à `Expired` (terminal)
- [ ] Brancher `Dispatcher.dispatch` sur `CommandRecord` en gardant l'API de `Outcome` (`states`, `state`, `dispatched`) et le crochet `on_transition`
- [ ] Tests : toutes les paires (état, état) — autorisées vs interdites — par paramétrage exhaustif sur la table
- [ ] Tests : états terminaux absorbants ; déduplication ; expiration ; relance idempotente bornée
- [ ] Test de pannes de transport simulées (actionneur factice qui échoue / ne répond pas) : un compteur d'exécutions prouve qu'une commande non idempotente n'est exécutée qu'une fois (propriété Hypothesis sur des séquences de pannes)
- [ ] Vérifier `tests/unit/test_effects.py` et `tests/integration/test_demo_plaque.py` inchangés et verts
- [ ] Documenter la correspondance avec la future preuve HYP-066 (au plus une exécution) dans `docs/verification/proprietes.md` (statut « à prouver », sans toucher à `formal/`)
- [ ] `TECHNICAL.md` : section Commandes (automate, idempotence, déduplication)
- [ ] `./scripts/validate.sh complet`, commit en français, mettre la tâche en `qa`
