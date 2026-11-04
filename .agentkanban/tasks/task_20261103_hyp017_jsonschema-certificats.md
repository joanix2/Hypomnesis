---
title: "HYP-017 · Certificats : valider avec jsonschema au lieu d'accesseurs écrits à la main"
lane: todo
created: 2026-11-03T21:36:21+01:00
updated: 2026-11-04T08:55:00+01:00
description: "P2 · S · Fondations et gouvernance · dépend de HYP-002 · migration vers bibliothèque"
---

## Conversation

### user

**Ticket** HYP-017 · **Priorité** P2 · **Taille** S · **Epic** Fondations et gouvernance · **Dépend de** HYP-002 · **Labels** python, jsonschema, contrats, dette

#### Contexte

Le chargeur de certificats (`src/hypomnesis/certify/load.py`) ne valide pas le certificat contre son schéma : il revérifie la structure du JSON avec des accesseurs écrits à la main (`_obj`, `_list`, `_int`, `_str`, `_single`). Or `certificate-1.0.0.json` décrit déjà cette structure en entier (types, définitions, expressions, motifs, littéraux, objets à une seule clé), et `jsonschema` est déjà une dépendance du projet, utilisée par `SchemaRegistry`.

Décision de l'utilisateur : le JSON Schema reste l'unique description de la structure (ADR 0004). Pydantic n'est pas retenu : il en ajouterait une seconde, à maintenir en parallèle. Le manifeste de langage est hors périmètre : `load_language` le valide déjà avec `SchemaRegistry`.

#### Tâches proposées

- Dans `load_definitions`, valider le certificat entier une seule fois, à l'entrée, avec `SchemaRegistry` et `CERTIFICATE_SCHEMA_ID` ; convertir les problèmes en `CertificateError` en gardant leur chemin JSON.
- Supprimer les contrôles de structure devenus redondants ; ne garder de `_single` et `_literal` que la déconstruction et la conversion.
- Garder les contrôles sémantiques qu'un JSON Schema ne peut pas exprimer : indice de de Bruijn hors de portée, variable de type non liée, emplacement cible non lié par le motif, emplacements de motif mal numérotés, liaison récursive qui n'est pas une fonction.
- Mesurer le coût de la validation sur le plus gros certificat des exemples.
- Remplacer « Pydantic » par « JSON Schema (`jsonschema`) » dans la ligne « Types et contrats » du cahier des charges (§15.1).

#### Critères d'acceptation

- `export(load(c)) = c` sur tous les exemples, comme aujourd'hui.
- Un certificat de structure invalide (champ manquant, champ en trop, mauvais type, objet à plusieurs clés, version inconnue) lève `CertificateError` avec le chemin JSON du champ fautif ; un test couvre chacun de ces cas.
- Tous les tests existants passent sans modification de leurs attentes, y compris les rejets sémantiques (`out of scope`, `unbound type variable`).
- Aucune nouvelle dépendance dans `pyproject.toml`.
- `./scripts/validate.sh complet` vert.

#### Fichiers concernés

- `src/hypomnesis/certify/load.py`
- `tests/unit/test_certificate.py`
- `docs/specification/cahier-des-charges-v0.2.md`

#### Références

- Ticket de coordination : HYP-007
- Schéma : `src/hypomnesis/contracts/schemas/certificate-1.0.0.json`
- Conventions et définition de fini : `.agentkanban/memory.md` (« bibliothèques plutôt que code maison »)
