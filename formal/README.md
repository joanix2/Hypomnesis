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
| `Hypomnesis/Epistemics/Provenance.lean` | provenance en semi-anneau, révision, monotonie du support |

```bash
lake build                 # vérifie toutes les preuves
lake env lean Audit.lean   # liste les axiomes utilisés
```

Aucune dépendance (pas de Mathlib) ; version de Lean fixée dans `lean-toolchain`.
