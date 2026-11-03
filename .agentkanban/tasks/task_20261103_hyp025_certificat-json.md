---
title: "HYP-025 · Pont F3b : schéma et export JSON du certificat"
lane: qa
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T18:38:53+01:00
description: "P0 · M · Vérification formelle (Lean) · dépend de HYP-024"
---

## Conversation

### user

**Ticket** HYP-025 · **Priorité** P0 · **Taille** M · **Epic** Vérification formelle (Lean) · **Dépend de** HYP-024 · **Labels** python, contrats

#### Contexte

Le certificat est la Core IR élaborée, en indices de de Bruijn, sérialisée en JSON et validée par un JSON Schema versionné (ADR 0004).

#### Tâches proposées

- Écrire `src/hypomnesis/contracts/schemas/certificate-1.0.0.json` (Draft 2020-12).
- Écrire `src/hypomnesis/certify/export.py` : traduction noms → indices, déclarations de types, définitions globales.
- Ajouter `hypomnesis check --emit-certificate FICHIER`.

#### Critères d'acceptation

- Chaque exemple produit un certificat valide contre le schéma.
- Test d'aller-retour : réimporter le certificat redonne une Core IR équivalente.

#### Fichiers concernés

- `src/hypomnesis/contracts/schemas/`
- `src/hypomnesis/certify/`
- `src/hypomnesis/cli.py`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`

### agent

Plan (suite de HYP-024, à la demande de l'utilisateur).

Format du certificat `certificate/1.0.0` (JSON Schema 2020-12) :
- `types` : déclarations de types (variants, records et types prédéfinis ; les abréviations sont déjà expansées). Paramètres notés `{"param": i}`.
- `definitions` : dans l'ordre d'exécution, `value`, `rec` ou `native`, chacune avec ses quantificateurs (`forall`) et son type.
- **Types** : `{"con": nom, "args": [...]}` (dont `->` et `*`) ou `{"var": nom}`. Les variables sont renommées `a0, a1…` par définition, dans l'ordre des quantificateurs.
- **Variables locales en indices de de Bruijn** : chaque lieur empile ses variables de gauche à droite et l'indice 0 désigne la plus récente. Lieurs : paramètres de `lam`, `let`, les membres de `letrec`, et les variables de motif.
- **Variables de motif par emplacement** : un motif lie n emplacements, et chaque feuille `{"bind": k}` dit lequel. C'est ce qui rend les alternatives `A x | B x` et les alias exprimables sans ambiguïté.
- Les littéraux portent leur sorte (`int`, `float`, `string`, `bool`, `unit`), car JSON ne distingue pas `1` de `1.0`.

Vérification de l'aller-retour : un import `certificate → Core IR` permet de tester que `export(import(c)) = c` et que la Core IR réimportée s'exécute avec les mêmes résultats que l'originale.

CLI : `hypomnesis check FICHIERS --emit-certificate cert.json`. Le certificat contient le prélude, dont les programmes dépendent.

### user

### agent

Implémenté.

- `contracts/schemas/certificate-1.0.0.json` : schéma Draft 2020-12 récursif (types, gabarits de déclarations, littéraux, motifs, expressions, définitions). Il est chargé automatiquement par `SchemaRegistry.with_builtin_schemas()`.
- `certify/export.py` : export avec indices de de Bruijn, emplacements de motifs, variables de type nommées par définition, littéraux typés. Il échoue (`CertificateError`) sur une annotation manquante ou une variable de type libre.
- `certify/load.py` : import inverse avec accesseurs typés et rejet des certificats incohérents (indice hors portée, variable de type non liée, emplacements non contigus).
- `Session.definitions` conserve toutes les définitions élaborées, prélude compris.
- CLI : `hypomnesis check FICHIERS --emit-certificate cert.json`. Le certificat est validé contre le schéma avant écriture (environ 70 Ko pour le prélude et un exemple).

Critères d'acceptation :
- chaque exemple produit un certificat valide contre le schéma : testé pour le prélude seul, le tour et la mécanique ;
- l'aller-retour donne une Core IR équivalente : `export(load(c)) = c` à l'identique, et le programme réimporté, réexécuté, donne les mêmes valeurs que l'original pour toutes les globales non fonctionnelles.

16 tests (`tests/unit/test_certificate.py`) ; `./scripts/validate.sh complet` vert.

Pour HYP-026 : le vérificateur Lean ne couvre aujourd'hui que le fragment monomorphe sans variants. Il devra rejeter proprement ce qu'il ne sait pas encore vérifier (polymorphisme, variants, records) tant que HYP-020, HYP-021 et HYP-023 ne sont pas faits.

La tâche peut passer en `done` (couloir à ta main).

### user
