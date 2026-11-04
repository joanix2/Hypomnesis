---
title: "HYP-113 · DSL DREAL : un langage pour la règlementation environnementale"
lane: hypothese
created: 2026-11-03T17:50:18+01:00
updated: 2026-11-04T19:36:05+01:00
description: "P2 · L · Instances de domaines · dépend de HYP-050, HYP-031, HYP-056 · idée à planifier"
priority: P2
tags: [dsl, humain, idee, reglementation]
---

## Conversation

### user

**Ticket** HYP-113 · **Priorité** P2 · **Taille** L · **Epic** Instances de domaines · **Dépend de** HYP-050, HYP-031, HYP-056 · **Labels** idée, dsl, humain

#### Idée

Une instance de DSL pour les domaines instruits par la DREAL (Direction régionale de l'environnement, de l'aménagement et du logement) : qualifier une installation ou un projet au regard de la règlementation, avec une justification traçable de chaque conclusion.

> Interprétation à confirmer : « DREAL » désigne ici l'administration, et non le solveur dReal (évoqué dans HYP-111).

#### Pistes de conception

- **Périmètres candidats** : nomenclature des installations classées (ICPE), nomenclature IOTA de la loi sur l'eau, examen au cas par cas de l'évaluation environnementale, incidences Natura 2000.
- **Concepts** : installation, activité, rubrique, seuil, régime (non classé, déclaration, enregistrement, autorisation), dossier, prescription.
- **Règles juridiques comme règles du moteur** (HYP-050), chacune portant sa **source** : article, texte, version et date d'application. La provenance (HYP-031) rattache donc chaque conclusion aux textes appliqués, ce qui sert directement l'explicabilité (HYP-084).
- **Temporalité** : une règle a une période de validité ; on qualifie une situation à une date donnée.
- **Quantités avec unités** (tonnes, MW, m³, hectares), pour refuser toute comparaison à un seuil dans une unité incompatible (HYP-056).
- **Support épistémique** : une quantité déclarée ou mesurée est `Observed`, une quantité estimée (par le DSL IA par exemple) est `Estimated`, et une décision qui en dépend est marquée **provisoire**.
- **Effets** : production de documents, comme un pré-dossier ou une liste de pièces, par des actionneurs.

#### Propriétés prouvables envisagées

- **Monotonie** : augmenter une quantité ne fait jamais baisser le régime.
- **Totalité et unicité** : toute activité reçoit exactement un régime par rubrique applicable.
- **Justification** : toute conclusion cite au moins une source en vigueur à la date considérée.
- Une conclusion fondée sur une estimation est toujours marquée provisoire (P12, monotonie du support).

#### Points d'attention

- Les règles et seuils réels doivent être **saisis et validés par un expert** à partir des textes officiels en vigueur ; le système assiste l'instruction et ne remplace pas la décision administrative.
- Ne pas présenter d'exemples fictifs comme des valeurs règlementaires réelles.

#### Questions ouvertes

- Confirmer l'interprétation de « DREAL ».
- Par quel périmètre commencer (ICPE, IOTA, cas par cas) ?
- Qui sont les utilisateurs : porteurs de projet, bureaux d'études, services instructeurs ?

#### Références

- `docs/architecture/m3-metalangage.md` (§4.2–4.3 connaissance et support, §6.4 provenance)
- `docs/verification/proprietes.md`
- Conventions : `.agentkanban/memory.md`

### agent

Reclassement demandé par l'utilisateur : `todo` → `hypothese`. Le sens de
DREAL, les utilisateurs et le périmètre réglementaire restent à confirmer.
Les réserves sur la validation experte sont conservées, ainsi que priorité
et dépendances ; aucune règle réglementaire n'est adoptée.

### user
