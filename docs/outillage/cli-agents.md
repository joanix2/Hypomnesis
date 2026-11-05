# CLI pour les agents

Aucune inférence n'est nécessaire pour découvrir, écrire, vérifier et simuler
un programme. Deux distributions, conformément à l'ADR 0012 :
`hypomnesis-codegen` publie le catalogue existant ; `hypomnesis` vérifie
et exécute. Ne pas chercher de commande `describe` dans le noyau.

```sh
hypomnesis-codegen decrire demo/languages/ventilation --format json > catalogue.json
hypomnesis check programme.hyp --langage demo/languages/ventilation --format json
hypomnesis lancer demo/languages/ventilation programme.hyp \
  --mode simulate --format json --generated --sortie /tmp/hyp-simulation
hypomnesis lancer demo/languages/ventilation programme.hyp \
  --mode dry-run --format json --generated --sortie /tmp/hyp-dry-run
```

Le catalogue donne modules, types, champs, signatures, descriptions, tags
(dont les squelettes de programmes), contrats, adaptateurs et plugins
explicitement publiés avec leurs permissions **requises, pas accordées**.
Sa lecture ne charge aucun adaptateur/backend. Les modèles, prompts et
bancs Codegen ne sont pas invoqués par ces commandes.

Chaque document porte `version: "1.0.0"` et possède un schéma embarqué :

| Sortie | Identifiant du schéma |
|---|---|
| `decrire --format json` | `https://schemas.example.org/hypomnesis/language-catalogue/1.0.0` |
| `check --format json` | `https://schemas.example.org/hypomnesis/diagnostics/1.0.0` |
| `lancer --format json` | `https://schemas.example.org/hypomnesis/cli-execution/1.0.0` |

Validation locale : `SchemaRegistry.with_builtin_schemas().validate(id, document)`.
Les schémas sont dans `src/hypomnesis/contracts/schemas/` ; pas de téléchargement
à partir des identifiants. Le format historique des diagnostics est conservé.
Catalogue et résultat d'exécution sont validés avant leur émission.

## Protocole

- **stdout** : un seul document JSON, sans en-tête ni clôture Markdown.
- **stderr** : journaux, taille du catalogue et messages d'usage. En exécution
  JSON, les impressions Python des adaptateurs sont redirigées sur stderr.
- Aucune invite interactive. Les chemins/options invalides détectés par
  Typer restent des erreurs d'usage sur stderr, sans document stdout.
- Une description impossible reste un refus sur stderr, sans catalogue partiel.
- `check` fournit `diagnostics` : étape, gravité, message, fichier et étendue
  1-based, fin exclusive ; positions nulles quand indisponibles.
- `lancer` fournit `mode`, `status`, `report` et `diagnostics`. `status: "ok"`
  signifie procédure terminée, **pas** vérité de sa conclusion ni réussite de
  chaque commande. Lire les états et contrôles de `report.commands`.
  Les valeurs métier `result`/`knowledge.*.value`, le graphe et les attributs
  télémétriques restent des données JSON extensibles.
- `status: "stopped"` conserve le rapport partiel et un diagnostic d'erreur :
  budget épuisé, résultat non établi. `status: "error"` contient les diagnostics
  et un rapport nul ; ce n'est pas une garantie qu'aucun effet antérieur n'a eu lieu.
- `--generated` préserve les assertions du programme comme hypothèses ; il
  n'accorde aucune permission. `simulate`/`dry-run` n'appellent pas le callback
  de production de l'actionneur. `production` exige une demande explicite et
  reste soumis aux gardes habituelles ; aucune approbation automatique ajoutée.
- Le rapport M0 existant reste écrit dans `--sortie/rapport.json`.

| Code | Signification |
|---|---|
| 0 | Vérification acceptée, catalogue publié ou procédure terminée ; avertissements possibles. |
| 1 | Refus de chargement/typage/certification/exécution, ou exécution JSON arrêtée par budget. |
| 2 | Erreur d'usage Typer : arguments manquants, chemin invalide, mode/option inconnu. |
| 64 | `lancer` sans programme ni demande transcriptible ; diagnostic JSON si demandé. |

Un refus de commande peut être un résultat normal traité par la procédure :
ne pas inférer un effet exécuté à partir du seul code 0. Une réparation se
fait en réécrivant le programme depuis le catalogue et les diagnostics, puis
en relançant `check` avant la simulation. Les tests exécutent réellement cette
boucle en sous-processus, stdin fermé, sans modèle ni réseau.
