# Hypomnesis — preuves formelles (Lean 4)

Sémantique de référence et preuves de propriétés du cahier des charges.
Catalogue des propriétés : [docs/verification/proprietes.md](../docs/verification/proprietes.md).
Stratégie (certificats, tests différentiels) : [docs/verification/strategie.md](../docs/verification/strategie.md).

| Module | Contenu |
|---|---|
| `Hypomnesis/Core/Syntax.lean` | fragment de la Core IR (de Bruijn, lambdas annotées) |
| `Hypomnesis/Core/Typing.lean` | typage déclaratif `HasType` |
| `Hypomnesis/Core/Eval.lean` | interpréteur de référence à environnements et budget |
| `Hypomnesis/Core/Soundness.lean` | sûreté : un terme bien typé ne se bloque jamais |
| `Hypomnesis/Core/Check.lean` | vérificateur exécutable, correct et complet ; décidabilité ; unicité |
| `Hypomnesis/Core/Fuel.lean` | le budget ne change jamais un résultat obtenu |
| `Hypomnesis/Core/Examples.lean` | longueur d'une liste d'entiers : typage établi par calcul, exécution |
| `Hypomnesis/Core/Records.lean` | records nominaux dérivés, construction/projection/mise à jour typées et sûres |
| `Hypomnesis/Core/RecordExamples.lean` | deposit : solde 150, propriétaire inchangé ; propriétaire encodé en points de code, pas de support natif string |
| `Hypomnesis/Epistemics/Provenance.lean` | provenance en semi-anneau, révision, monotonie du support |
| `Hypomnesis/Certificate.lean` | décodage des certificats JSON vers le fragment (non prouvé, hors base de confiance) |
| `Main.lean` | exécutable `hypomnesis-check` (`check`, `eval`) |

```bash
lake build                 # vérifie toutes les preuves
lake env lean Audit.lean   # liste les axiomes utilisés
lake build hypomnesis-check && lake exe hypomnesis-check check ../cert.json
```

Depuis la racine : `hypomnesis check demo/examples/basics/certifiable.hyp --certify`.
L'export `--emit-certificate` seul n'appelle pas Lean.
Couverture et refus hors fragment : [certification](../docs/verification/certification.md).

Aucune dépendance (pas de Mathlib) ; version de Lean fixée dans `lean-toolchain`.
