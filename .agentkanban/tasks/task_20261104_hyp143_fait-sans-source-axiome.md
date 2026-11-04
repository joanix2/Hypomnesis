---
title: "HYP-143 · KnowledgeBase : un fait sans source déclarée (axiome) fait échouer support() et to_json"
lane: todo
created: 2026-11-04T14:45:00+01:00
updated: 2026-11-04T14:45:00+01:00
description: "P2 · S · Phase 2 — Moteur épistémique · dépend de HYP-008 · bug"
---

## Conversation

### user

**Ticket** HYP-143 · **Priorité** P2 · **Taille** S · **Epic** Phase 2 — Moteur épistémique · **Dépend de** HYP-008 · **Labels** python, bug

#### Contexte

Signalé par l'implémenteur de HYP-008. `KnowledgeBase.derive(key, value, method, [])` (aucune prémisse) donne au fait la provenance `obs("axiome")` (`epistemics/knowledge.py`, L142). Or `axiome` n'est enregistrée dans aucun `sources` : la provenance mentionne une source **non déclarée**.

Reproduit le 2026-11-04 :

- `kb.support("c.k")` et `kb.confidence("c.k")` lèvent `KeyError: 'axiome'` (la fonction passée à `evaluate` fait `self.sources[s]`) ; `to_json` et l'export du graphe, qui lisent le support, échouent donc aussi sur ce fait.
- Plus grave : `_holds("axiome")` rend toujours `False` (`source_id in self.sources`). La première rétractation de **n'importe quelle** source invalide donc ce fait, même sans lien (reproduit : `derive("c.k", 1, "constante", [])`, puis `observe("a", …)` et `retract_source` de `a` → `c.k` invalidé).

Aujourd'hui `engine/procedure.py` (L256) dérive après avoir vérifié les prémisses, ce qui masque le cas ; il apparaît dès qu'un langage dérive une constante sans prémisse.

#### Décision à prendre (à documenter)

- **Option A — support par défaut** : un fait sans prémisse est une *constante du programme* : on déclare une source `axiome` (type `default`, support `Defaulted`, confiance 1.0, jamais rétractée). Le fait reste utilisable, et sa provenance est cohérente avec `sources`.
- **Option B — refus explicite** : `derive` sans prémisse lève une erreur claire (`ValueError`), l'appelant doit passer par `observe` ou `hypothesis`.

Recommandation de l'agent : A. Le §7.1 prévoit un support « par défaut » ; refuser (B) empêcherait les constantes de domaine. La décision, avec la valeur de support retenue, va dans `docs/` (ADR courte ou note dans `docs/architecture/`), et dans la docstring de `derive`.

#### Tâches proposées

- Écrire d'abord un test qui reproduit les deux symptômes (échec de `support`/`confidence`/`to_json`, et invalidation par une rétractation sans rapport).
- Appliquer l'option retenue dans `KnowledgeBase`.
- Vérifier que `graph()` et l'export JSON se comportent bien (nœud `source:axiome` déclaré si l'option A).
- Étendre les tests de propriétés (`tests/property/`) : une rétractation ne touche pas un fait qui ne dépend pas de la source.

#### Critères d'acceptation

- Un test reproduit le bug (rouge avant le correctif) puis passe.
- La décision (support par défaut ou refus explicite) est documentée, avec ses conséquences sur P10/P11.
- `./scripts/validate.sh complet` vert.

#### Fichiers concernés

- `src/hypomnesis/epistemics/knowledge.py`
- `tests/unit/`, `tests/property/`
- `docs/architecture/` (ou `docs/adr/`)

#### Références

- Ticket d'origine : HYP-008 (graphe de provenance)
- `src/hypomnesis/epistemics/provenance.py` (`evaluate`, `obs`)
- `docs/specification/cahier-des-charges-v0.2.md` §7.1
- Conventions et définition de fini : `.agentkanban/memory.md`

### user

