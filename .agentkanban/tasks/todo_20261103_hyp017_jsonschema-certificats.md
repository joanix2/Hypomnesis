---
title: "HYP-017 · TODO"
lane: todo
created: 2026-11-04T15:00:00+01:00
updated: 2026-11-04T15:00:00+01:00
description: "Checklist de HYP-017"
---

# Iteration 1

État des lieux (vérifié) : `certify/load.py` (264 lignes) contient les accesseurs `_obj`, `_list`, `_int`, `_str`, `_single`, `_literal` (L25-67) qui revérifient la structure ; les contrôles **sémantiques** (variable de type non liée L92, « recursive binding is not a function » L104, « target slot … not bound by the pattern » L120, « de Bruijn index … out of scope » L156, « pattern slots are not numbered 0..n-1 » L263) doivent rester. `jsonschema` et `SchemaRegistry` (`contracts/registry.py`, `with_builtin_schemas`, `issues`) sont déjà des dépendances ; `certify/export.py` expose `CERTIFICATE_SCHEMA_ID` et `CertificateError`. `cli.py::_emit_certificate` valide déjà l'**export** par le schéma. Tests protecteurs : `tests/unit/test_certificate.py` (aller-retour `export(load(c)) == c`, rejets `out of scope` et `unbound type variable`).

Fichiers (disjoints de tous les autres lots) : `src/hypomnesis/certify/load.py`, `tests/unit/test_certificate.py`, `docs/specification/cahier-des-charges-v0.2.md` (§15.1, remplacer « Pydantic » par « JSON Schema (`jsonschema`) »). Aucune nouvelle dépendance.

Risque : un certificat que le schéma accepte mais dont les accesseurs rejetaient une forme (ou l'inverse) ; les messages `CertificateError` ne doivent pas changer pour les rejets sémantiques.

- [x] Avant de toucher au code : test qui liste, pour chaque forme invalide listée dans les critères (champ manquant, champ en trop, mauvais type, objet à plusieurs clés, version inconnue), l'erreur actuelle ; sert de référence (référence relevée par script : champ manquant → `KeyError 'forall'` ; champ en trop → accepté ; mauvais type → `CertificateError expected an integer` sans chemin ; plusieurs clés → `CertificateError` sans chemin ; version inconnue → acceptée)
- [x] `load_definitions` : valider le certificat entier **une seule fois** à l'entrée par `SchemaRegistry.with_builtin_schemas().issues(CERTIFICATE_SCHEMA_ID, certificate)` ; convertir chaque `ValidationIssue` en `CertificateError` en conservant le chemin JSON du champ fautif
- [x] Vérifier que le schéma couvre bien « objet à une seule clé » (`minProperties`/`maxProperties`/`oneOf`) et la version ; sinon, compléter le schéma (`certificate-1.0.0.json`) plutôt que le code, et regénérer `formal/` seulement si le schéma publié change réellement (alors prévenir : changement de contrat)
- [x] Supprimer `_obj`, `_list`, `_int`, `_str` redondants ; ne garder de `_single` et `_literal` que la déconstruction et la conversion (types garantis par le schéma, `typing.cast` ou `assert isinstance` acceptés, pas de `type: ignore`)
- [x] Conserver les contrôles sémantiques avec leurs messages exacts (`out of scope`, `unbound type variable`, …)
- [x] Tests : un certificat par cas invalide (champ manquant, champ en trop, mauvais type, objet à plusieurs clés, version inconnue) lève `CertificateError` dont le message contient le chemin JSON ; les rejets sémantiques existants passent inchangés
- [x] `export(load(c)) == c` sur tous les exemples (test existant) ; les certificats du prélude et de `examples/` se rechargent
- [x] Mesurer le coût de la validation sur le plus gros certificat des exemples (prélude + `tour.hyp`) ; consigner le chiffre dans la fiche
- [x] `cahier-des-charges-v0.2.md` §15.1 : « Pydantic » → « JSON Schema (`jsonschema`) »
- [x] Vérifier que `pyproject.toml` n'a pas changé pour ce ticket
- [x] (`rapide` vert ; `complet` bloqué par le travail en cours sur `cli.py`/`observability`, voir la fiche) `./scripts/validate.sh rapide`, puis `complet` (l'étape « lean (vérificateur de certificats) » relit le certificat) ; commit en français, mettre la tâche en `qa`
