---
title: "HYP-008 · Graphe de provenance des faits avec NetworkX"
lane: qa
created: 2026-11-03T21:36:21+01:00
updated: 2026-11-04T14:50:00+01:00
description: "P1 · M · Fondations et gouvernance · dépend de HYP-002 · migration vers bibliothèque"
---

## Conversation

### user

**Ticket** HYP-008 · **Priorité** P1 · **Taille** M · **Epic** Fondations et gouvernance · **Dépend de** HYP-002 · **Labels** python, networkx, dette

#### Contexte

`KnowledgeBase` (`src/hypomnesis/epistemics/knowledge.py`) gère à la main les prémisses des faits, l'invalidation en cascade lors d'un retrait et l'explication récursive. NetworkX fournit exactement ces opérations sur un graphe orienté. Les termes de provenance en semi-anneau (`provenance.py`), miroir du modèle Lean, restent la source de vérité du support et de la confiance.

#### Tâches proposées

- Représenter faits et sources comme nœuds d'un `networkx.DiGraph` (arête prémisse → conclusion).
- Invalidation : `nx.descendants` depuis la source retirée, au lieu de réévaluer chaque fait.
- Explication : parcours du graphe (arbre des prémisses) ; garder le rendu texte actuel.
- Exposer le graphe de provenance (export GraphML ou JSON node-link dans le rapport M0), utile au chatbot et à Graphify.
- Vérifier que l'invalidation par graphe coïncide avec l'évaluation booléenne de la provenance (propriété P10/P11) par un test Hypothesis.

#### Critères d'acceptation

- L'ensemble des faits invalidés est identique à celui d'aujourd'hui sur tous les tests (révision par mesure, réfutation d'hypothèse).
- Le rapport M0 contient le graphe de provenance exporté.
- Tous les tests existants passent sans modification de leurs attentes.
- `./scripts/validate.sh complet` vert.

#### Fichiers concernés

- `src/hypomnesis/epistemics/knowledge.py`
- `pyproject.toml`
- `tests/property/`

#### Références

- Ticket de coordination : HYP-007
- Conventions et définition de fini : `.agentkanban/memory.md` (« bibliothèques plutôt que code maison »)

### agent

**HYP-008 — fait (lane `qa`).** Commit de code : `a9a0029` ; la documentation et la fiche sont dans le commit suivant.

Ce qui a été fait (`epistemics/knowledge.py`) :

- `KnowledgeBase.graph(detailed=True)` : `nx.DiGraph` construit à la demande. Nœuds `fact:<clé>` et `source:<id>` (préfixes, car une clé de fait peut ressembler à un id de source ; les sources non déclarées comme `axiome` y figurent aussi). Arêtes `source → fait` (la provenance du fait cite la source) et `prémisse → conclusion` (`kind` = `provenance` ou `premise`).
- `retract_source` : le graphe donne l'ensemble **candidat** (descendants des sources qui ne tiennent plus : retirées ou non déclarées). La décision d'invalider reste l'évaluation **booléenne** de la provenance, candidat par candidat, dans l'ordre de `facts`. Un fait à deux dérivations (`plus`) survit donc, et le journal est identique.
- `explain` parcourt les prédécesseurs `premise`, avec le même rendu texte.
- `provenance_graph()` : export node-link JSON (`edges="edges"`), rechargeable par `nx.node_link_graph`. `ProcedureReport.to_json` l'inclut sous `provenance_graph` (une seule ligne ajoutée dans `procedure.py`, traçage intact).
- `TECHNICAL.md` : sous-section « Épistémique : graphe de provenance ».

Tests ajoutés (aucun test existant modifié) :

- `tests/integration/test_provenance_graph.py` : caractérisation de la révision par mesure et de la réfutation d'hypothèse (faits invalidés, journal, explications). Je l'ai vérifiée **verte sur l'ancienne implémentation** (copie du `knowledge.py` de HEAD) puis sur la nouvelle ; elle contient aussi le test du rapport M0.
- `tests/unit/test_knowledge_graph.py` : arêtes, chaîne de 60 faits, fait à deux dérivations, fait sans prémisse, prémisse remplacée, cycle, export.
- `tests/property/test_knowledge_graph.py` (Hypothesis) : révision = évaluation booléenne de tous les faits ; sur des bases à produits seuls, `descendants(source)` = faits invalidés ; avec `plus`, les candidats sur-approximent.

Validation : `./scripts/validate.sh rapide` vert, `./scripts/validate.sh complet` vert (tests, Lean, audit des axiomes).

Écarts et points de vigilance :

- **Sources non déclarées** : l'ancien code invalidait tout fait sans prémisse (provenance `axiome`) à n'importe quelle révocation, car `_holds` est faux pour `axiome`. Pour conserver ce comportement, les candidats incluent les descendants des sources non déclarées, pas seulement de la source retirée. Un simple `descendants(source_retirée)` aurait changé le résultat.
- **Cycle** : `derive("a", …, ["b"])` après `derive("b", …, ["a"])` crée un cycle de prémisses au niveau des clés. L'ancien `explain` récursait sans fin. Il lève maintenant `ValueError`. La révision reste correcte, puisqu'elle se fonde sur les provenances (test dédié). Je n'ai pas interdit ce cas dans `derive`, car ce serait un changement de comportement ; si on veut l'interdire, c'est un ticket à part.
- **Prémisses dupliquées** : deux prémisses identiques dans une même dérivation n'apparaissent plus qu'une fois dans `explain` (arête de `DiGraph`). Aucun programme existant n'en produit.
- **Prémisse absente** : une prémisse absente de `facts` donne l'absence d'arête, là où l'ancien code levait `KeyError`. Cela ne se produit que si le fait dérivé a lui aussi été invalidé.
- **Bug existant, non corrigé** : `support()` lève `KeyError` sur un fait à provenance `axiome` (source non déclarée), donc `to_json` aussi. Je ne l'ai pas touché ; à traiter dans un ticket.
- **Pyright** : lancé seul sur le dossier, il ne résout pas `hypothesis` (même erreur sur `test_properties.py`). Le pre-commit de `validate.sh complet` est passé. Aucun `type: ignore`.
- **CLI** : `src/hypomnesis/cli.py` non touché. Pour exposer le graphe (par exemple `hypomnesis lancer … --graphe-provenance`, ou un export GraphML/DOT), HYP-006 devra ajouter l'option ; `KnowledgeBase.provenance_graph()` est prêt. Je n'ai pas fait d'export GraphML : les valeurs de faits ne sont pas toutes scalaires.
- **TECHNICAL.md** contenait des modifications non commitées d'autres agents (HYP-006). Je n'ai commité que ma section, en indexant uniquement mon hunk.

### user
