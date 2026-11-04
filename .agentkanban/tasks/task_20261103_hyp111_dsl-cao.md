---
title: "HYP-111 · DSL CAO : un langage pour la conception assistée par ordinateur"
lane: todo
created: 2026-11-03T17:50:18+01:00
updated: 2026-11-03T17:50:18+01:00
description: "P2 · L · Instances de domaines · dépend de HYP-056, HYP-052, HYP-053 · idée à planifier"
priority: P2
tags: [cao, dsl, idee]
---

## Conversation

### user

**Ticket** HYP-111 · **Priorité** P2 · **Taille** L · **Epic** Instances de domaines · **Dépend de** HYP-056, HYP-052, HYP-053 · **Labels** idée, dsl

#### Idée

Une instance de DSL pour la CAO paramétrique : esquisses, contraintes géométriques, fonctions de construction, assemblages, matériaux, contraintes de fabrication. Le scénario MVP du cahier des charges (§16.2, la plaque de 120 × 80 mm) relève naturellement de ce DSL.

#### Pistes de conception

- **Concepts** : point, esquisse, profil, fonction de construction (extrusion, poche, perçage, congé, chanfrein), pièce, assemblage et liaisons, matériau.
- **Unités dimensionnelles** obligatoires : additionner une longueur et une surface est une erreur de type (HYP-056).
- **Contraintes géométriques** (distance, parallélisme, tangence, coïncidence) : leur résolution est un problème de la Problem IR (HYP-051), confié à un solveur qui rend un certificat vérifié par le noyau (HYP-052, HYP-053). Le solveur **dReal** (arithmétique réelle non linéaire, δ-complète) serait un backend pertinent pour les contraintes non linéaires.
- **Inconnues** : un paramètre manquant (l'épaisseur, par exemple) est une métavariable résolue par un estimateur (HYP-032, DSL IA).
- **Backends** (modèles de la théorie CAO) : CadQuery/OpenCascade, FreeCAD.
- **Effets** : l'export STEP/STL et le pilotage d'un logiciel de CAO sont des actionneurs (HYP-060 à HYP-064).

#### Propriétés prouvables envisagées

- Cohérence dimensionnelle et invariance par changement d'unités (HYP-057).
- Une solution de contraintes acceptée satisfait réellement toutes les contraintes (certificat).
- La régénération d'une pièce paramétrique est déterministe.
- Les contraintes de fabrication déclarées (paroi minimale, perçage dans la matière, profondeur inférieure à l'épaisseur) sont respectées par toute pièce validée.

#### Questions ouvertes

- Quel backend de CAO cibler en premier ?
- Pièces seules, ou assemblages dès le départ ?

#### Références

- `docs/specification/cahier-des-charges-v0.2.md` (§4.2, §16.2)
- `examples/mechanics/` (plaque et unités existantes)
- Conventions : `.agentkanban/memory.md`
