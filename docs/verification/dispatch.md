# Validation avant dispatch — HYP-065

## Énoncés prouvés

Modèle : [Dispatch.lean](../../formal/Hypomnesis/Effects/Dispatch.lean).
Pour une commande fixée `c`, `Run permitted state history` représente la
projection de son journal sur les états, du plus récent au plus ancien.
`permitted` est la permission de `c` effectivement accordée par l'hôte au
moment de son contrôle, **pas** une permission inférée du JSON de la commande.

- `dispatch_ordered` : pour **toute occurrence** de `Dispatched`, son passé
  contient `Authorized`, immédiatement précédé chronologiquement de
  `Validated`. L'énoncé quantifie les suffixes et préfixes arbitraires :
  il ne porte pas seulement sur le dernier dispatch ni sur la simple présence
  des deux événements quelque part dans le journal.
- `dispatch_permitted` : si `Dispatched` figure dans le journal, `permitted`.
- `no_dispatch_without_permission` : sous `¬ permitted`, aucun événement
  `Dispatched` ne figure dans le journal.

Les trois preuves utilisent seulement `propext`, sans axiome métier.
Elles sont listées dans [Audit.lean](../../formal/Audit.lean).

## Construction et portée

`State` et `canMove` reprennent tous les états et les 19 transitions
de `commands.py`, y compris `Accepted`, les états des modes et la relance
`Dispatched → Dispatched`. `Run.init` crée le journal initial ; `Run.advance`
ajoute un événement seulement si `canMove` l'autorise. L'entrée dans
`Authorized` exige la preuve de `permitted` : c'est la condition locale
de la transition, et non la propriété globale d'absence de dispatch
qu'on chercherait à supposer.

La preuve procède par induction sur les transitions : seule `Validated`
précède directement `Authorized` ; seul `Authorized` ou un ancien
`Dispatched` précède un nouveau `Dispatched`. L'induction couvre donc
aussi chaque relance et conserve le passé validé et autorisé.

Les identifiants sont portés par `CommandRecord.command_id` côté Python ;
le modèle fixe un identifiant à la fois. Il ne prouve pas l'implémentation
du dictionnaire Python ni un ordonnanceur concurrent multi-commandes.
Dans le dispatcher synchrone, chaque `move` ajoute à l'Outcome de la commande
en cours ; le journal par commande est cette projection. Les transitions
supplémentaires de la table, non empruntées par le dispatcher actuel, sont
une surapproximation sûre pour ces propriétés de trace. Les bornes de relance
et l'idempotence ne sont pas nécessaires à cette preuve d'ordre.

## Correspondance avec Python

Les numéros ci-dessous correspondent aux fichiers après HYP-064.
La vérification de correspondance est une obligation de revue et de tests,
**pas** un théorème de raffinement automatique du code Python.

| Python | Opération | Correspondance |
|---|---|---|
| `dispatcher.py:145–148` | construction de l'enveloppe interne Command | le `command_id` fixe le journal considéré |
| `dispatcher.py:150–156` | retour de l'issue mise en cache ou refus d'un contenu différent | aucun événement supplémentaire |
| `dispatcher.py:157–163` | actionneur, échéance, Outcome et cache | `Run.init`, état Created |
| `dispatcher.py:165–168` | `move` délègue à `CommandRecord.move` puis notifie l'hôte | `Run.advance` et ajout au journal ; callback observateur de confiance |
| `dispatcher.py:170–185` | callback de validation, erreur explicite ou liste de violations | stase ou transition Rejected, jamais Dispatched |
| `dispatcher.py:187–191` | notification Created, actionneur absent | init, puis Rejected possible |
| `dispatcher.py:192–199` | structure JSON stricte | stase ou Rejected |
| `dispatcher.py:200–206` | présence des deux contrats | stase ou Rejected |
| `dispatcher.py:207–215` | conformité de la charge et cohérence d'identité | stase ou Rejected |
| `dispatcher.py:216` | `move(Validated)` | Created → Validated |
| `dispatcher.py:217–225` | décision de politique ou appartenance aux permissions hôte ; retour si refus | garde `permitted`, ou Validated → Rejected |
| `dispatcher.py:226–229` | métier et sécurité | stase ou Rejected |
| `dispatcher.py:230–243` | accord humain éventuel strictement True | stase ou Rejected |
| `dispatcher.py:244` | `move(Authorized)` | Validated → Authorized avec permission accordée |
| `dispatcher.py:245–251` | sélection du handler fourni par l'hôte | stase, ne change pas la permission |
| `dispatcher.py:253–256` | handler dry-run | Authorized → DryRun, aucun Dispatched |
| `dispatcher.py:258–274` | réponse fictive ou erreur explicite | Authorized → Simulated/Rejected, aucun Dispatched |
| `dispatcher.py:276–282` | contrôle d'échéance de production, puis `_execute` | Authorized → TimedOut ou suite |
| `dispatcher.py:294–303` | premier envoi à l'adaptateur | Authorized → Dispatched avant le callback |
| `dispatcher.py:304–324` | perte de transport, délai, éventuelle relance idempotente bornée | Dispatched → TimedOut/UnknownOutcome/Dispatched |
| `dispatcher.py:325–326` | exception ordinaire de l'adaptateur | Dispatched → Failed |
| `dispatcher.py:328–335` | délai et contrat de réponse | Dispatched → TimedOut/Failed ou stase |
| `dispatcher.py:336–353` | résultat, observation physique optionnelle, terminaison | Dispatched → Failed/Completed |
| `commands.py:48–70` | table et `can_move` | `canMove`, comparaison exécutable exhaustive |
| `commands.py:99–125` | CommandRecord, historique, validation avant ajout | représentation inverse de la liste d'états de `Run` |
| `permissions.py:7–19` | politique exacte et refus prioritaires | interprétation hôte de la proposition `permitted` |

`PipelineCheck` contient aussi des détails de validation, sans créer de
transition d'état supplémentaire. Les spans sont de la télémétrie, pas
les événements de la preuve.

## Vérification de correspondance exécutable

[EffectsTable.lean](../../formal/EffectsTable.lean) exporte le calcul
de `canMove` pour toutes les paires d'états ; sa liste couvre tous les
constructeurs de State (lemme `states_complete`). Le test
[test_effects_model.py](../../tests/integration/test_effects_model.py)
compare les 144 paires aux transitions Python. Il exige Lean/Lake et
construit le module nécessaire, sans ignorer la comparaison si Lean manque.
Les tests HYP-062/064 couvrent en plus les décisions du dispatcher, les
refus avant actionneur, les relances et la fidélité des traces.

## Frontière de confiance

Ne sont pas prouvés ici : correction de jsonschema et des callbacks,
fidélité de l'interpréteur Python, absence de mutation externe d'un
Outcome ou des permissions, exécution concurrente, redémarrage, fiabilité
du capteur, authenticité de l'accord humain et sécurité physique.
Un hôte Python capable de modifier le journal ou d'appeler directement
`Actuator.execute` est hors du modèle.

Le résultat est une propriété des **traces du modèle de dispatch**,
accompagnée d'une correspondance testée/documentée avec Python, pas une
certification du matériel ni de tout le programme Python.
