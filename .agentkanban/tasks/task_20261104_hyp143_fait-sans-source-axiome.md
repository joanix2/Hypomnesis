---
title: "HYP-143 · KnowledgeBase : un fait sans source déclarée (axiome) fait échouer support() et to_json"
lane: doing
created: 2026-11-04T14:45:00+01:00
updated: 2026-11-04T14:55:00+01:00
description: "P1 · S · Phase 2 — Moteur épistémique · dépend de HYP-008 · bug"
---

## Conversation

### user

**Ticket** HYP-143 · **Priorité** P1 · **Taille** S · **Epic** Phase 2 — Moteur épistémique · **Dépend de** HYP-008 · **Labels** python, bug

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

### agent

**Décisions de l'utilisateur (2026-11-04).** Priorité portée à **P1**. Option **A** retenue : un fait sans prémisse est une constante du programme ; on déclare une source `axiome` (type `default`, support « par défaut », confiance 1,0, **jamais rétractée**). Le **second symptôme** (invalidation à tort au premier `retract_source`, même sans lien) est à corriger dans ce ticket : une source déclarée et non rétractée tient, et une rétractation ne doit toucher que les faits dont la provenance mentionne la source retirée. Critères d'acceptation complétés : le test rouge sur l'invalidation à tort passe ; `retract_source` d'une source sans rapport laisse le fait `axiome` intact.

### user

Option A confirmée ; corriger les deux symptômes.

### agent

**HYP-143 implémenté (option A).** Fichiers : `src/hypomnesis/epistemics/knowledge.py`, `tests/unit/test_knowledge_graph.py`, `tests/property/test_knowledge_graph.py`, `TECHNICAL.md` (section HYP-008, « Limites connues »).

- **Tests rouges d'abord** (4 tests unitaires en échec : `KeyError: 'axiome'` sur `support`/`confidence`/`to_json`, invalidation à tort par une rétractation sans rapport), puis correctif.
- **Correctif** : `derive` sans prémisse déclare, une fois par base, la source `axiome` (constante `AXIOM` ; type `default`, support « par défaut », confiance 1,0, origine « constante du programme ») et donne au fait `obs("axiome")`. `retract_source("axiome", …)` lève `ValueError`. `_holds` ne considère plus « faux » une source inconnue : seule la rétractation explicite compte, et les candidats de la révision sont les descendants des seules sources retirées.
- **Propriétés** (Hypothesis) : les faits sans prémisse survivent à la rétractation de toute autre source ; aucun fait dont la provenance omet la source retirée n'est touché (P11). Les propriétés existantes excluent `axiome` du tirage des sources à rétracter.
- **P10/P11** : formulations et miroir Lean inchangés (`axiome` n'est qu'un identifiant d'observation vrai) ; `formal/` et `proprietes.md` non modifiés.
- **Écart au plan** : deux tests existants de `test_knowledge_graph.py` figeaient précisément le bug (`test_premise_less_fact_is_invalidated_by_any_retraction`, `test_undeclared_sources_appear_as_such` avec `axiome`) ; ils ont été réécrits (le premier affirme l'inverse ; le second teste désormais une source réellement non déclarée, posée à la main, et l'axiome déclaré a son propre test). Aucun autre test modifié ; `test_languages` et `test_provenance_graph` passent sans changement.
- **Vigilance** : `TECHNICAL.md` contenait des modifications non commitées d'un autre agent (HYP-130) ; seuls mes hunks (HYP-008) sont commités. Une provenance construite à la main avec une source non déclarée fait toujours échouer `support()` (KeyError) : hors périmètre, `derive` ne produit plus ce cas.
- Validation : `./scripts/validate.sh rapide` vert (avant le dernier ajout de la fiche). `complet` **non vert à cause d'autres agents**, pas de ce ticket : pre-commit/ruff (1 erreur hors de mes fichiers) et pyright (6 erreurs dans `src/hypomnesis/language/docs.py`, HYP-130/137), et un échec `tests` transitoire ; la partie Lean (audit des axiomes, vérificateur de certificats) est verte. **Reste** : relancer `./scripts/validate.sh complet` une fois ces fichiers corrigés par leurs propriétaires, puis passer la fiche en `qa` (laissée en `doing`). Rien d'autre à faire dans `knowledge.py` ni dans les tests.

### user
