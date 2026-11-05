---
title: "HYP-043 · Lean F5d : aller-retour JSON et conformité au schéma"
lane: qa
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P1 · L · Vérification formelle (Lean) · dépend de HYP-042, HYP-021"
priority: P1
tags: [certification, contrats, lean, moteur-symbolique]
---

## Conversation

### user

**Ticket** HYP-043 · **Priorité** P1 · **Taille** L · **Epic** Vérification formelle (Lean) · **Dépend de** HYP-042, HYP-021 · **Labels** lean

#### Contexte

Contrepartie prouvée de HYP-042, pour le fragment de types formalisé.

#### Tâches proposées

- Modéliser JSON et un sous-ensemble de JSON Schema (types, propriétés requises, `additionalProperties: false`).
- Prouver : `decode (encode v) = some v` et `ValTy v t → conforms (encode v) (schemaOf t)`.

#### Critères d'acceptation

- Théorèmes sans `sorry`, ajoutés à l'audit.

#### Fichiers concernés

- `formal/Hypomnesis/Contracts/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`

### agent

Plan / todo / implement du lot Mac approuvé, sans sous-agent. HYP-042 et
HYP-021 sont en QA. Construire un modèle de frontière JSON indépendant du
décodeur de certificats : nombres rationnels exacts, booléens séparés,
tableaux et objets, schémas fermés et décodage piloté par le type.

Premier fragment annoncé : int, bool, string, unit, listes, paires,
options étiquetées et records nominaux imbriqués à champs distincts.
Les alias et paramètres concrets se projettent après résolution. Prouver
l'aller-retour sous ValTy et la conformité à un schéma indépendant, puis
confronter encode/decode/schémas aux vrais TypeCodec et validateurs JSON.
Tester objets permutés, champs absents/supplémentaires, options unit et
grands entiers au travers du texte JSON.

La preuve ne couvrira pas implicitement les flottants binary64, les
variants généraux ou la résolution récursive de `$ref` : ces limites
resteront explicites et leurs tests HYP-042 conservés. Une conformité à
ce sous-ensemble ne vaut ni équivalence de tout JSON Schema ni preuve
du parseur texte Python/Lean.

### user

### agent

P32 `Contracts.decode_encode` et P33 `Contracts.encode_conforms` compilent
sans `sorry` et sont ajoutés à l'audit. Le modèle distingue valeur typée,
JSON rationnel exact et conformité au schéma : propriétés obligatoires,
aucune propriété supplémentaire, objets indépendants de leur ordre.
Le décodeur consomme les champs et restitue l'ordre déclaré et le nom
nominal du record. None et Some unit ont des représentations distinctes.

96 compositions concrètes concordent avec les vrais TypeCodec :
encodage via texte JSON, valeur décodée, schéma résolu non récursif et
sondes valides/invalides (champs, tags, tableaux, nombres et booléens).
Alias et paramètres concrets inclus ; grands entiers de 300 chiffres
préservés. Les 48 tests ciblés passent, y compris les propriétés HYP-042
sur flottants et récursion, sans en revendiquer une nouvelle preuve.

Validation complète verte : tous les linters/Pyright, noyau, Codegen,
audit Lean et 90 tests obligatoires, dont 500 termes différentiels.
P32 utilise seulement propext, Classical.choice et Quot.sound ; P33
seulement propext et Quot.sound. CI et validate.sh lean/complet exigent
la correspondance réelle. Catalogue, frontière Core et TECHNICAL actualisés.
Passage en QA sur le fragment annoncé ; les limites restent explicites
et done demeure une décision humaine.

### user

### agent

Rapide et graphe également verts après QA. Jalon vérifié prêt au commit
local, sans push ; poursuite du lot Mac sur les tickets indépendants.

### user
