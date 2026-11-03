# ADR 0007 — Sémantique de référence en Lean 4 et compilation certifiante

- **Statut :** acceptée
- **Date :** 2026-11-03

## Contexte

Hypomnesis est un compilateur dont la promesse principale (H2) est la fiabilité : un
programme accepté ne doit pas échouer de certaines façons. Ces garanties doivent être
établies et maintenues en même temps que le compilateur évolue.

## Décision

- Le projet `formal/` contient une **sémantique de référence en Lean 4**, exécutable :
  syntaxe de la Core IR, typage, évaluation, moteur épistémique. La version de Lean est fixée
  et le projet n'a aucune dépendance.
- On **prouve le vérificateur, pas le compilateur** : le compilateur Python émet un
  certificat (Core IR élaborée et annotée) que le vérificateur Lean `typeOf`, prouvé correct
  et complet, revérifie.
- L'écart entre l'interpréteur Python et la sémantique Lean est couvert par des tests
  différentiels.
- Toute évolution de la Core IR met à jour la formalisation dans le même changement (voir
  [strategie.md](../verification/strategie.md)).
- La CI construit les preuves, refuse `sorry` et audite les axiomes.

## Conséquences

- Déjà prouvés sur le fragment formalisé : sûreté du typage, correction et complétude du
  vérificateur, unicité des types, monotonie du budget, propriétés de la révision par
  provenance (voir [proprietes.md](../verification/proprietes.md)).
- Lean devient une compétence requise pour modifier la Core IR.
- Le niveau méta de l'ADR 0006 pourra être prototypé directement en Lean avant d'être porté.
