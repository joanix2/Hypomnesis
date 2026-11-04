# Au plus un appel non idempotent — HYP-066

Modèle : [Commands.lean](../../formal/Hypomnesis/Effects/Commands.lean),
raffinement de l'automate [HYP-065](dispatch.md). Tous les théorèmes principaux
sont dans [Audit.lean](../../formal/Audit.lean).

## Ce qui est prouvé

`Execution idempotent limit permitted state history events` représente
l'exécution locale d'une commande identifiée, dans un dispatcher séquentiel :

- `advance` applique une transition de la table. Une autorisation exige
  toujours la permission. La relance `Dispatched → Dispatched` exige
  `mayRetry`, soit idempotence, état Dispatched et budget restant.
- `lost` ajoute une perte de réponse après dispatch, sans effacer l'historique.
  Le périphérique peut déjà avoir agi. La terminaison en UnknownOutcome ou
  TimedOut et les éventuelles relances restent des transitions explicites.
- `duplicate` ajoute la livraison dupliquée de la **même** commande au
  dispatcher ; le journal en cache est conservé, sans nouvel appel.

Le journal d'états et la liste d'événements réseau sont distincts et inversés
chronologiquement. `attempts` compte les événements Dispatched, comme
`CommandRecord.attempts`. Les pannes et doublons peuvent être en nombre
arbitraire ; aucune hypothèse de succès ou de terminaison n'est nécessaire.

| Théorème | Énoncé |
|---|---|
| `non_idempotent_at_most_once` | toute Execution non idempotente compte au plus un handoff à l'actionneur, pertes et doublons compris |
| `attempts_bounded` | sous `0 < limit`, toute Execution compte au plus `limit` handoffs |
| `terminal_absorbing` | aucun état terminal n'a de transition sortante dans l'automate |
| `Execution.toRun` | retirer les événements de réseau et les gardes de relance donne un Run HYP-065 ; les propriétés d'ordre et permission restent donc applicables |

Une trace concrète vérifiée dans Lean inclut un envoi non idempotent, une
perte de réponse, une livraison dupliquée, puis UnknownOutcome avec un seul
handoff. La borne n'est donc pas obtenue en interdisant ces pannes du modèle.
Les preuves des bornes utilisent `propext` et `Quot.sound` via l'arithmétique
du noyau ; absorption et effacement utilisent `propext`. Aucun axiome métier.

## Correspondance Python

- `commands.py`, `TRANSITIONS` et `TERMINAL` : `canMove` et `terminal`.
- `commands.py`, `CommandRecord.attempts` : `attempts`.
- `commands.py`, `may_retry` : `mayRetry`. Le constructeur `RetryPolicy`
  impose `max_attempts >= 1`, hypothèse de la borne générale.
- `dispatcher.py:150–156` : la livraison dupliquée retourne l'Outcome connu ;
  même identifiant et autre contenu lève DuplicateCommand, sans nouvel appel.
- `dispatcher.py:299–303` : premier Dispatched puis premier appel.
- `dispatcher.py:304–324` : une perte de transport après un appel peut
  avoir une issue inconnue ; un nouvel appel n'est possible qu'après
  relance explicitement gardée. L'échéance peut seulement empêcher une
  tentative supplémentaire, sans affaiblir les bornes du modèle.
- Les modes, refus, erreurs ordinaires, observations et terminaisons suivent
  la table HYP-065. Une fois terminal, les nouvelles livraisons ne ressuscitent
  pas la commande.

[EffectsTable.lean](../../formal/EffectsTable.lean) calcule la table et les
gardes. [test_effects_model.py](../../tests/integration/test_effects_model.py)
compare 144 paires d'états, les 12 statuts terminaux et 384 combinaisons de
relance (état, idempotence, tentatives et limite). Les histoires synthétiques
utilisées pour tester la fonction de garde ne prétendent pas toutes être
des exécutions légales ; les preuves concernent uniquement Execution.
Les tests Hypothesis existants de
[test_commands.py](../../tests/unit/test_commands.py) couvrent en plus
pertes avant/après action, erreurs et livraisons dupliquées au dispatcher.

## Ce que « au plus une fois » ne veut pas dire

La propriété porte sur les **appels/handoffs locaux**, pas sur une garantie
physique exactly-once. Le journal est supposé conservé pendant la vie du
dispatcher, les callbacks hôte sont de confiance et ne réentrent pas pour
contourner le journal.

Il serait faux d'en déduire une exécution physique unique si :

- un adaptateur ou le réseau **après** ce handoff duplique lui-même une
  requête vers un périphérique sans déduplication ;
- un périphérique exécute deux actions à un seul appel ;
- un redémarrage perd le cache et le même ordre est soumis à une nouvelle
  instance ;
- l'hôte modifie les journaux ou appelle directement l'adaptateur.

Ces situations ne sont pas modélisées comme des doublons d'entrée au même
dispatcher : elles nécessiteraient un journal durable et/ou une déduplication
réceptrice sous contrat, absents du MVP. Une perte de réponse produit donc
UnknownOutcome, jamais la promesse que l'action n'a pas eu lieu.
La correspondance Python est testée et documentée, pas formellement raffinée.
