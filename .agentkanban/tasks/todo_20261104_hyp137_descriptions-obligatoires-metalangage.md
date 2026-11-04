---
title: "HYP-137 · TODO"
lane: doing
created: 2026-11-04T14:50:00+01:00
updated: 2026-11-04T14:55:00+01:00
description: "Checklist de HYP-137"
---

# Iteration 1

Reste à faire (le reste est fait, voir l'entrée `### agent` de la fiche) : l'**erreur de compilation** quand un élément d'un langage M2 n'a pas de description, et le test « les descriptions n'ont aucun effet ». Sans GPU.

Décision de cadrage (sans attendre HYP-012) : est **public** tout élément déclaré dans un fichier source d'un langage M2 dont le nom ne commence pas par `_`. HYP-012 (signatures de modules) pourra restreindre cette notion plus tard. Les programmes M1 ne sont pas concernés.

État du code : `language/docs.py::declarations(source, program)` rend `Declaration(kind, path, doc, type_text)` pour module, valeur, type, champ, constructeur, mais **sans position**, et le champ `doc` d'un constructeur vaut toujours `None` (L110-113). `engine/language.py::load_language` charge `manifest["sources"]` dans la session. `tests/unit/test_docs.py` protège l'extraction.

Fichiers : `src/hypomnesis/language/docs.py`, `src/hypomnesis/engine/language.py`, `tests/unit/test_docs.py`, `tests/unit/test_language_docs.py` (nouveau), `docs/language/reference.md`, `docs/adr/0009-…` (passer à « acceptée » si l'utilisateur confirme). Éviter `cli.py` (HYP-130 y travaille).

- [x] Ajouter `span: Span | None` à `Declaration` et le remplir pour chaque genre (module, valeur, type, champ, constructeur)
- [x] Constructeurs : décider comment les décrire (commentaire `(** … *)` sur la ligne précédant `| Ctor`) et étendre `declarations` en conséquence ; sinon, restreindre la règle aux constructeurs écrits un par ligne — consigner le choix dans la fiche
- [x] `docs.py` : fonction `missing_descriptions(source) -> list[Declaration]` (publics sans `doc`, noms commençant par `_` exclus ; un élément `@interne` doit être décrit)
- [x] Balise `@interne` : `Doc.tag("interne")` détecté ; `llm/describe.py` n'inclut pas ces éléments dans le catalogue ni dans `decrire` ; test dédié (un élément décrit et `@interne` est absent du catalogue mais ne produit pas d'erreur de description manquante)
- [x] `load_language` : après le chargement des sources, lever `LanguageError` pour la première description manquante, avec le chemin qualifié (`Plaque.demande.largeur`), le fichier et la ligne:colonne ; option interne `strict=False` pour les tests de langages jouets
- [x] Test : retirer la description d'un champ de `languages/mecanique/plaque.hyp` (copie temporaire) donne une erreur qui nomme ce champ, à sa position
- [x] Test : un langage dont tous les éléments sont décrits charge sans erreur ; un M1 sans description passe (`session.check`)
- [x] Vérifier que `mecanique` et `ventilation` chargent toujours (ils sont déjà décrits) ; `test_languages.py` inchangé
- [x] Test de propriétés (Hypothesis ou paramétré sur tous les fichiers `.hyp` des langages et exemples) : supprimer tous les commentaires de description d'une source ne change ni la Core IR élaborée ni le certificat exporté (`export_certificate`)
- [x] Le test d'architecture (aucun domaine dans M3) passe toujours : la règle est générique
- [x] `docs/language/reference.md` : syntaxe `(** … *)`, balises, règle « public », exception `_` ; mettre à jour l'ADR 0009
- [ ] `./scripts/validate.sh rapide`, puis `complet` ; commit en français, mettre la tâche en `qa`
