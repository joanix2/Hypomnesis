---
title: "HYP-120 · Démonstrateur MVP vertical : plaque de bout en bout"
lane: qa
created: 2026-11-03T18:51:02+01:00
updated: 2026-11-03T18:56:37+01:00
description: "P0 · L · Phase 8 — Stabilisation · dépend de HYP-002, HYP-025"
---

## Conversation

### user

**Ticket** HYP-120 · **Priorité** P0 · **Taille** L · **Epic** Phase 8 — Stabilisation · **Dépend de** HYP-002, HYP-025 · **Labels** python, exemple, mvp

#### Contexte

L'utilisateur veut itérer vite et voir si le framework tient ses promesses : une tranche verticale du scénario MVP du §16.2, qui traverse toutes les couches, plutôt que de finir chaque ticket isolément. Les tickets détaillés (HYP-030 à 033, 040, 051, 052, 054, 055, 060 à 064, 090) restent ouverts pour leur version complète.

#### Tâches proposées

- Connaissances avec provenance en semi-anneau, support, inconnues, journal, révision (versions minimales de HYP-030 à 033).
- Capacités : estimateurs interchangeables, solveur Z3 sur une Problem IR minimale avec certificat revérifié, validateur écrit dans le DSL Hypomnesis.
- Effets : commande d'export de géométrie contrôlée par contrat JSON Schema, permission et contraintes métier ; modes simulation, dry-run et production.
- Traces : journal de spans JSON.
- Transcription : déterministe (pas de clé API), branchable sur un LLM (HYP-081).
- CLI `hypomnesis demo plaque`, rapport lisible et JSON, tests.

#### Critères d'acceptation

- La demande en français produit un programme typé, une épaisseur estimée puis résolue, une validation, un fichier exporté et un rapport expliquant chaque conclusion par sa provenance.
- Changer d'estimateur ne modifie pas le programme métier.
- Une mesure d'épaisseur ultérieure révise les conclusions, dont le support change.
- Une commande invalide ou non autorisée n'atteint jamais l'actionneur ; le dry-run n'écrit rien.

#### Références

- `docs/specification/cahier-des-charges-v0.2.md` (§16)
- `docs/architecture/m3-metalangage.md` (§4.2 à 4.4, §6.3, §6.4)
- Conventions : `.agentkanban/memory.md`
### agent

Implémenté : `hypomnesis demo plaque`.

Le pipeline traverse toutes les couches :
1. demande en français ;
2. programme Hypomnesis typé (`Plaque.demande`), le domaine `domaine.hyp` portant règles et constantes ;
3. connaissances (dimensions observées, épaisseur inconnue) ;
4. estimation par un estimateur interchangeable (`regle` ou `abaque`) ;
5. problème construit à partir des constantes du DSL, résolu par Z3, solution revérifiée en rationnels exacts ;
6. validation par `Plaque.verifier` ;
7. export SVG et JSON contrôlé (contrat JSON Schema, permission, contraintes métier, modes) ;
8. rapport (explication par la provenance, journal, traces), et révision par une mesure.

Briques minimales ajoutées, à compléter dans leurs tickets :
- `epistemics/provenance.py` et `epistemics/knowledge.py` (HYP-030 à HYP-033) ;
- `ir/problem.py` (HYP-051) et `backends/z3_solver.py` (HYP-052, HYP-053) ;
- `effects/dispatcher.py` (HYP-061 à HYP-064) ;
- `observability/trace.py` (HYP-070).

Critères d'acceptation (11 tests dans `tests/integration/test_demo_plaque.py`) :
- la demande produit programme typé, épaisseur estimée puis résolue (3,2 mm estimés → 3 mm standard), validation, fichiers exportés et un rapport qui explique chaque conclusion : oui ;
- changer d'estimateur ne modifie pas le programme : oui ;
- une mesure révise les conclusions : les 4 conclusions dépendantes sont invalidées, et le support de la validité passe de « estimé » (confiance 0,6) à « observé » ; le journal garde l'historique ;
- une commande invalide (contrat), hors du répertoire de sortie (contraintes métier) ou non autorisée n'atteint jamais l'actionneur ; le dry-run n'écrit rien : oui.

Ce que la démonstration montre aussi : avec une masse maximale de 0,2 kg, l'estimation (3 mm, 0,226 kg) viole une règle du domaine, et le solveur choisit 2 mm. Si les règles sont infaisables, la conclusion est « Impossible ».

Limites honnêtes :
- la transcription est déterministe (expressions régulières), faute de clé API ; le LLM se branche au même endroit (HYP-081) ;
- les contraintes du solveur sont écrites en Python à partir des constantes du DSL, et non encore générées depuis le DSL ;
- les traces sont internes et non exportées en OTLP.

`./scripts/validate.sh complet` vert. Passée en `qa`.

### user

### agent

Ajout : le scénario secondaire du §16.3, `hypomnesis demo ventilation [--panne]` (`src/hypomnesis/demos/ventilation/`).

- Le capteur simulé envoie ses relevés dans l'enveloppe de message, validée puis contrôlée contre son contrat (§9.6).
- La règle `Ventilation.decider` (Hypomnesis, pure) décide la commande ; le dispatcher l'exécute.
- L'effet attendu dépend explicitement de l'hypothèse « le ventilateur fonctionne » (support « hypothèse »).
- Le second relevé confirme l'effet, ou le réfute : l'hypothèse est alors retirée, l'effet attendu invalidé, et la panne conclue des seules observations (support « observé »).
- La boucle est bornée par un budget (§11).

7 tests (`tests/integration/test_demo_ventilation.py`), dont le rejet d'un relevé hors contrat. Le ticket détaillé HYP-068 reste ouvert pour la version complète (transport fichiers, rejeu).

### user
