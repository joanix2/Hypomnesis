# Transports et scénarios enregistrés (HYP-063)

Le moteur expose `Transport.send(envelope)` et `Transport.receive()`.
Un `receive()` retourne une enveloppe détachée, ou `None` si la file est vide.
Ces transports ne connaissent aucun capteur, solveur ou domaine.

- `MemoryTransport(registry)` : FIFO en mémoire.
- `FileTransport(path, registry)` : FIFO persistante JSONL, un message par ligne,
  écriture en ajout seulement, curseur de lecture propre à chaque instance.
- `replay(source, target)` : copie les messages d'une source finie, dans l'ordre,
  vers la cible et retourne leur nombre.

Les deux transports valident les mêmes messages à l'envoi **et** à la lecture :
JSON strict (pas de NaN, tuples ou clés numériques), enveloppe
`envelope/1.0.0`, cohérence de version et contrat nommé par `schema_id`.
Un message invalide ne rentre jamais dans une file ; une ligne invalide lève
une erreur sans avancer le curseur. Clés dupliquées et dernière ligne
incomplète d'un fichier sont refusées, jamais réparées silencieusement.
Le registre fourni doit inclure l'enveloppe et les contrats de charge.

Le contenu des messages est capturé à l'envoi : modifier le dictionnaire
initial après `send` ne modifie pas la file ou le fichier. Les identifiants,
horodatages, corrélations, entiers et contexte de trace sont conservés.

## Enregistrer et rejouer

```python
from pathlib import Path
from hypomnesis.effects.transports import FileTransport, MemoryTransport, replay

# registry contient envelope/1.0.0 et les contrats des messages.
log = FileTransport(Path("scenario.jsonl"), registry)
log.send(envelope)
assert log.receive() == envelope

# Une nouvelle instance commence la lecture au début du journal existant.
target = MemoryTransport(registry)
assert replay(FileTransport(log.path, registry), target) == 1
assert target.receive() == envelope
```

Le rejeu lit et valide la source entière avant le premier envoi à la cible.
Il n'est pas transactionnel entre deux stockages, ne réinitialise pas un curseur
existant et ne régénère aucun identifiant ni horodatage. Il restitue un
**scénario de messages**, pas une nouvelle exécution des actions physiques.

Les transports MVP sont synchrones et destinés à un seul processus ;
ils ne sont ni un broker concurrent, ni une file distribuée avec accusés de
réception. Le curseur n'est pas persistant : une nouvelle instance relit le
journal. Ne pas traiter cette relecture comme une permission de réexécuter
les commandes enregistrées. Les erreurs disque et de contrat sont remontées
au demandeur. Aucun message `Accepted` asynchrone n'est fabriqué.

## Périphériques de ventilation

La pièce simulée reste dans `demo/languages/ventilation/adaptateurs/piece.py`,
le domaine n'entre pas dans le moteur. Ses décorateurs Python restent les
seuls points de branchement I/O. Ses manifestes statiques sont dans
`demo/languages/ventilation/peripheriques/` ; les schémas sont dans `contrats/`.
Ces manifestes documentent les périphériques, sans déclencher d'import
d'adaptateur ni les convertir en backends de sous-processus.

L'option hôte `environment={"transport": "files"}` choisit le transport
fichiers ; par défaut il est en mémoire. Chaque lecture transporte une
requête et un relevé ; chaque exécution de ventilateur transporte une commande
et une réponse corrélée. En fichiers, les échanges d'une exécution sont
enregistrés dans `OUT/scenarios/<identifiant-unique>.jsonl`, sans écraser un
scénario antérieur. Les modes `dry-run` et `simulate` ne passent pas dans
l'adaptateur d'exécution du ventilateur.

Exemple complet, sans matériel réel et sans LLM :

```bash
.venv/bin/python examples/robotics/transport.py demo/sortie/transport
```

Le programme M1 existant régule la pièce simulée. L'exemple enregistre ses
messages puis vérifie leur égalité exacte après rejeu en mémoire. Il échoue
explicitement si la procédure est interrompue, si une commande échoue ou
si le rejeu diffère.
