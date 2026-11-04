# Validation des effets (HYP-062)

Le dispatcher existant conserve l'automate HYP-061 et la déduplication locale
des identifiants de commande. Les modes restent `simulate`, `dry-run`,
`production`. Ce document décrit les contrôles Python ; il ne revendique
pas de nouvelle preuve Lean.

## Ordre et trace

Chaque `Outcome.checks` contient des `PipelineCheck(stage, passed, detail)`
pour les étapes réellement parcourues ; un refus arrête la suite.
`ProcedureReport.to_json()` les expose dans `commands[].checks`.

| Étape du §9.8 | Stage et comportement |
|---|---|
| 1. Structure JSON | `structure` : données JSON strictes, nombres finis, clés chaînes, pas de coercition des tuples |
| 2. Contrat | `contract` : schémas de commande et réponse enregistrés par identifiants versionnés, charge conforme au contrat de l'actionneur ; `command_id` cohérent avec l'enveloppe s'il est présent |
| 3. Permissions | `permission` : permission exacte de l'actionneur accordée par l'hôte |
| 4. Métier | `business` : `Actuator.constraints(payload)` |
| 5. Sécurité | `safety` : `Actuator.safety(payload)` |
| Accord humain éventuel | `approval` : si `requires_human=True`, le callback de l'hôte doit retourner exactement `True` |
| 6. Adaptateur | `execute` : l'appel réel est commencé, sans garantie de succès ; tentatives dans l'historique de l'automate |
| 7. Réponse | `response` : objet JSON strict validé par son schéma |
| 8. Résultat | `result` : résultat enregistré dans l'Outcome |
| 9. Observation réelle | `observation` : contrôle optionnel après enregistrement du résultat |

`Validated` ne signifie pas encore autorisé. L'état `Authorized` n'est
atteint qu'après permission, métier, sécurité et accord humain éventuel.
Une commande invalide ou refusée ne peut donc pas atteindre `execute`.
Les schémas sont immuables par identifiant dans `SchemaRegistry` ; le dispatcher
ne négocie ni ne devine un autre contrat à partir du contenu non fiable.

## Politiques et points d'extension

```python
from hypomnesis.effects.permissions import PermissionPolicy

policy = PermissionPolicy(
    allowed=frozenset({"actuator:export"}),
    denied=frozenset({"actuator:delete"}),
)
assert policy.permits("actuator:export")
assert not policy.permits("actuator:delete")
```

`Dispatcher(..., policy=policy, approve=callback)` utilise la politique
déclarative si elle est fournie ; sinon, le jeu historique `permissions`
reste utilisé. Les refus explicites prévalent sur les autorisations et
les noms ne sont pas interprétés comme des motifs ou des préfixes.
`run_procedure(..., policy=..., approve=...)` expose ces paramètres à l'hôte.
Ni le programme M1 ni une sortie LLM ne peuvent fournir l'accord humain.
Sans callback, une commande exigeant l'accord est refusée, jamais approuvée
par défaut. Ce callback est une frontière de confiance de l'application :
le moteur ne prétend pas authentifier lui-même une personne.

`constraints` et `safety` retournent une liste de violations, vide si acceptée.
`observe_effects(payload, result)` fait de même après l'exécution réelle.
Les callbacks de validation reçoivent des copies détachées pour éviter que
leur mutation ne remplace la charge validée. Une erreur ou un format de
résultat invalide de ces callbacks est enregistré explicitement comme un
refus ; une erreur de l'observation finale produit `Failed`, en conservant
le résultat reçu et sans relancer l'action.

## Modes et limites

Après les contrôles communs, `Dispatcher` sélectionne `_dry_run`, `_simulate`
ou `_production`. Ces trois handlers ont la même signature
`(actuator, outcome, move) -> None` et interprètent la même commande :
aucune branche de logique métier n'est ajoutée au programme M1.
L'hôte choisit le mode dans `run_procedure(mode=...)` ou par
`hypomnesis lancer ... --mode dry-run|simulate|production`. Le défaut est
`dry-run` ; il n'existe pas d'effet M1 permettant de modifier ce choix.

- `dry-run` parcourt les préconditions puis s'arrête sans adaptateur.
- `simulate` parcourt les préconditions et valide la réponse fictive ;
  une réponse fictive non conforme est refusée. Aucun observateur physique
  ni adaptateur de production n'est appelé.
- `production` appelle l'adaptateur, puis valide la réponse, conserve le
  résultat et appelle l'observateur réel optionnel.

Les étapes `checks` complètent les états existants, sans les remplacer.
Le détail de chaque envoi et relance est dans `Outcome.record.history`.
Dans les rapports de procédures, le span `command.dispatch` couvre
validation et sélection du handler. Le span `actuator.execute` couvre
uniquement un appel réel au callback `execute`, y compris chaque relance :
il n'apparaît ni en dry-run ni en simulation. C'est une correction de
l'ancien nom ambigu qui couvrait aussi la validation sans exécution.
La déduplication est locale à une instance en mémoire et ne fournit pas
de garantie d'exécution physique unique après redémarrage ou contre un
périphérique qui exécute deux fois un message. La preuve HYP-066 doit
expliciter ces hypothèses, pas les dissimuler.
