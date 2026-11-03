---
title: "HYP-017 · Certificats et manifestes : modèles Pydantic au lieu d'accesseurs écrits à la main"
lane: todo
created: 2026-11-03T21:36:21+01:00
updated: 2026-11-03T21:36:21+01:00
description: "P2 · M · Fondations et gouvernance · dépend de HYP-002 · migration vers bibliothèque"
---

## Conversation

### user

**Ticket** HYP-017 · **Priorité** P2 · **Taille** M · **Epic** Fondations et gouvernance · **Dépend de** HYP-002 · **Labels** python, pydantic, contrats, dette

#### Contexte

Le chargeur de certificats (`src/hypomnesis/certify/load.py`) valide la structure du JSON par des accesseurs écrits à la main (`_obj`, `_list`, `_int`…), et le chargeur de langages lit le manifeste comme un dictionnaire brut. Pydantic, prévu dans la stack du cahier des charges (§15.1), fournit des modèles typés et des erreurs localisées ; les JSON Schema restent le contrat d'échange (ADR 0004).

#### Tâches proposées

- Modèles Pydantic pour le certificat (types, définitions, expressions, motifs) et pour le manifeste de langage.
- Vérifier que le JSON Schema généré par Pydantic est compatible avec les schémas publiés, ou générer l'un à partir de l'autre (choisir et documenter dans une ADR).
- Supprimer les accesseurs maison.

#### Critères d'acceptation

- `export(load(c)) = c` sur tous les exemples, comme aujourd'hui.
- Un certificat ou un manifeste invalide donne une erreur qui pointe le champ fautif.
- Tous les tests existants passent sans modification de leurs attentes.
- `./scripts/validate.sh complet` vert.

#### Fichiers concernés

- `src/hypomnesis/certify/load.py`
- `src/hypomnesis/engine/language.py`
- `pyproject.toml`

#### Références

- Ticket de coordination : HYP-007
- Conventions et définition de fini : `.agentkanban/memory.md` (« bibliothèques plutôt que code maison »)

