# Architecture Decision Records

Chaque ADR consigne une décision structurante, son contexte et ses conséquences.
Un ADR accepté n'est pas modifié : on le remplace par un nouvel ADR qui le rend caduc.

| N° | Titre | Statut |
|---|---|---|
| [0001](0001-prototype-python-lark.md) | Prototype en Python, parsing LALR avec Lark | Acceptée |
| [0002](0002-elaboration-vers-core-ir.md) | Typage sur l'AST et élaboration vers la Core IR | Acceptée |
| [0003](0003-noyau-pur-et-primitives-natives.md) | Noyau pur, primitives natives par registre fermé | Acceptée |
| [0004](0004-contrats-json-schema.md) | Contrats JSON Schema 2020-12 et enveloppe indépendante du transport | Acceptée |
| [0005](0005-provenance-et-observabilite-distinctes.md) | Provenance épistémique et observabilité restent distinctes | Acceptée |
| [0006](0006-m3-theorie-des-types-a-deux-niveaux.md) | Le M3 est une théorie des types à deux niveaux, modale et graduée | Proposée pour expérimentation (HYP-005) |
| [0007](0007-semantique-de-reference-lean.md) | Sémantique de référence en Lean 4 et compilation certifiante | Acceptée |
| [0008](0008-niveaux-m3-m2-m1-m0.md) | Séparation stricte des niveaux M3, M2, M1, M0 | Acceptée |
| [0009](0009-langage-auto-documente-et-prompt-compile.md) | Langage M2 auto-documenté et prompt LLM compilé | Proposée |
| [0010](0010-types-et-json-reversible.md) | Types statiques, JSON Schema et encodage réversible | Acceptée |
| [0011](0011-demonstrations-isolees.md) | Démonstrations isolées dans `demo/` | Acceptée |
| [0012](0012-codegen-separe-du-moteur.md) | Génération de programmes séparée du moteur | Acceptée |
| [0013](0013-couches-declarees-en-hypomnesis.md) | Couches déclarées en Hypomnesis, imports DAG et I/O décorées | Acceptée |
| [0014](0014-backend-scientifique-optionnel.md) | Backend scientifique optionnel | Proposée pour revue (HYP-054 en QA) |
| [0016](0016-declarations-language-struct.md) | Déclarations language avec struct / let / end | Acceptée ; remplace la syntaxe de 0013 |
| [0017](0017-imports-locaux-python.md) | Imports locaux avec syntaxe Python | Acceptée |
| [0018](0018-signatures-opaques.md) | Signatures lexicales et scellement opaque | Acceptée |
| [0019](0019-identite-producteurs-metriques.md) | Identité standard des producteurs de métriques indépendants | Acceptée |
