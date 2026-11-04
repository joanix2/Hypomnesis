---
title: "HYP-061 · Automate d'états des commandes, délais, relances"
lane: qa
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P0 · M · Phase 5 — Effets et actionneurs · dépend de HYP-060"
priority: P0
tags: [effets, moteur-symbolique, python, runtime]
---

## Conversation

### user

**Ticket** HYP-061 · **Priorité** P0 · **Taille** M · **Epic** Phase 5 — Effets et actionneurs · **Dépend de** HYP-060 · **Labels** python

#### Contexte

§9.7 : `Created` → `Validated` → `Authorized` → `Dispatched` → `Accepted` → `Completed`, plus les états d'échec ; idempotence.

#### Tâches proposées

- Automate explicite (table des transitions), états terminaux absorbants.
- Identifiants de commande, délais d'expiration, politique de relance.
- Déduplication par `command_id` : une commande non idempotente n'est jamais relancée automatiquement.

#### Critères d'acceptation

- Test exhaustif des transitions autorisées et interdites.
- Simulation de pannes de transport : aucune double exécution d'une commande non idempotente.

#### Fichiers concernés

- `src/hypomnesis/effects/commands.py`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`

### agent

**État : implémentation terminée, fiche laissée en `doing` car `./scripts/validate.sh complet` n'est pas vert pour une cause étrangère à ce ticket.**

Fait :
- `src/hypomnesis/effects/commands.py` (nouveau, pur) : `State` (StrEnum, états de §9.7 + `DryRun`/`Simulated`), table `TRANSITIONS`, `TERMINAL` (absorbants), `can_move`, `CommandRecord` (journal, `attempts`, échéance, `move` → `IllegalTransition`), `RetryPolicy`, `NO_RETRY`, `may_retry`, `TransportError`.
- `src/hypomnesis/effects/dispatcher.py` : `Dispatcher` branché sur `CommandRecord` ; déduplication par `command_id` (`DuplicateCommand` si même id et autre contenu) ; `clock`/`sleep` injectables ; `Actuator.idempotent` (défaut `False`), `.retry`, `.timeout` ; `Outcome` garde `states`/`state`/`dispatched` (+ `attempts`, `record`).
- `tests/unit/test_commands.py` : toutes les paires d'états (table exhaustive), terminaux absorbants, déduplication, relances bornées, expiration, deux propriétés Hypothesis sur pannes de transport simulées (non idempotent : au plus une exécution, même redélivré). Aucun `sleep` réel.
- Docs : `TECHNICAL.md` (section « Automate des commandes (HYP-061) », embarquée par erreur dans le commit b136d75 d'un autre agent), `docs/verification/proprietes.md` (miroir de HYP-066, statut « à prouver »). `formal/` non touché.

Commits : aa29350 (code + tests) ; docs et fiche dans le commit suivant.

Écarts : états `TimedOut`/`UnknownOutcome` (noms de §9.7) au lieu de `Expired`. `Accepted` est dans la table mais non émis (transport asynchrone, HYP-063). Exception ordinaire de l'actionneur → `Failed` sans relance ; seul `TransportError` déclenche relance (idempotent) ou `UnknownOutcome`. `tests/unit/test_effects.py` ne concerne pas le dispatcher : la non-régression est couverte par `tests/integration/test_languages.py` (vert).

Reste à faire : relancer `./scripts/validate.sh complet` ; dernier état : seul échec = pyright sur `src/hypomnesis/language/docs.py` (l.83-132, `int | None`, chantier HYP-130/137, pas ce ticket) ; ruff, tests (tout `tests/`) et Lean sont verts. Quand `complet` est vert : cocher la dernière case du todo, passer la fiche en `qa`.

### user
