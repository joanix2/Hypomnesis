# HYPOMNESIS
## Cahier des charges, architecture et plan d'implémentation

**Version :** 0.2  
**Date :** 3 novembre 2026  
**Statut :** Spécification technique initiale  
**Nature :** Métalangage fonctionnel, symbolique, épistémique et extensible

**Devise :** *A language for programmable knowledge and reasoning.*

---

# 1. Vision du projet

## 1.1 Présentation

Hypomnesis est un métalangage permettant de définir des langages spécifiques à un domaine (DSL) pour représenter des systèmes, leurs connaissances, leurs règles, leurs contraintes et leurs capacités d'action.

Il constitue une couche intermédiaire entre :

- Le langage naturel utilisé par les humains et les LLM.
- Les représentations symboliques propres aux domaines métiers.
- Les bibliothèques scientifiques et moteurs informatiques existants.
- Les systèmes physiques ou numériques accessibles par des capteurs et des actionneurs.

Hypomnesis ne vise pas à remplacer Python, les solveurs de contraintes, les bibliothèques de machine learning ou les moteurs de simulation.

Il vise à fournir un langage commun permettant de les décrire, de les composer et de contrôler leurs interactions.

## 1.2 Philosophie

Le langage reprend plusieurs principes :

| Inspiration | Caractéristique conservée |
|---|---|
| OCaml | Syntaxe, modules, typage inféré et types algébriques |
| Haskell | Pureté fonctionnelle, immutabilité, séparation des effets |
| Lua | Runtime léger et intégration dans des applications |
| Lisp | Métaprogrammation et définition de DSL |
| ATL | Transformation de modèles et règles déclaratives |
| Systèmes experts | Connaissances, inférence et règles symboliques |
| Programmation par contraintes | Définition d'objectifs et résolution par solveurs |

La priorité est de conserver un noyau minimal et d'implémenter les fonctionnalités spécialisées sous forme de bibliothèques et d'extensions.

## 1.3 Objectif principal

Permettre de définir un système métier en déclarant :

- Ce qui existe : concepts, types, objets, relations.
- Ce qui est connu : faits, observations, bases de connaissances.
- Ce qui est inconnu : variables, hypothèses, propriétés manquantes.
- Ce qui est possible : opérations, règles, transformations, transitions.
- Ce qui est souhaité : contraintes, préférences et objectifs.
- Ce qui est disponible : générateurs, estimateurs, solveurs, validateurs.
- Ce qui peut être observé : capteurs et sources externes.
- Ce qui peut être exécuté : actionneurs et opérations autorisées.
- Ce qui doit être conservé : preuves, provenance et historique de raisonnement.

Le langage doit permettre de construire des systèmes procéduraux, déclaratifs ou hybrides.

---

# 2. Objectifs fonctionnels

## OBJ-01 — Langage fonctionnel minimal

Développer un langage à syntaxe OCaml-like avec inférence de types, fonctions de première classe, immutabilité, modules et composition fonctionnelle.

## OBJ-02 — Métamodélisation

Permettre de définir des DSL métiers au moyen de concepts, relations, types, règles et opérations.

## OBJ-03 — Extensibilité

Permettre de connecter des bibliothèques externes sans modifier le compilateur ni réimplémenter leurs algorithmes.

## OBJ-04 — Raisonnement épistémique

Représenter les observations, connaissances, hypothèses, estimations, validations, réfutations et révisions.

## OBJ-05 — Résolution hybride

Combiner les procédures impératives au sens de l'orchestration, les fonctions pures, les règles déclaratives, les contraintes et les solveurs.

## OBJ-06 — Compatibilité LLM

Permettre aux modèles de langage de transcrire une intention humaine en programme symbolique typé.

## OBJ-07 — Interopérabilité JSON

Standardiser les échanges avec les composants externes au moyen de messages JSON et de contrats JSON Schema versionnés.

## OBJ-08 — Capteurs et actionneurs

Permettre l'acquisition de données externes et l'exécution contrôlée d'actions, sans compromettre la pureté du langage.

## OBJ-09 — Observabilité

Tracer et mesurer chaque étape du raisonnement, de l'exécution, de la validation et des interactions avec le monde extérieur.

## OBJ-10 — Indépendance métier

Permettre l'implémentation de nouveaux domaines sans modification du noyau d'Hypomnesis.

---

# 3. Architecture générale

Hypomnesis est organisé autour de sept couches.

```text
┌─────────────────────────────────────────┐
│            INTERFACES                   │
│       Humain / LLM / Application        │
└───────────────────┬─────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│         LANGAGE HYPOMNESIS              │
│  Syntaxe OCaml / Types / Modules / DSL   │
└───────────────────┬─────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│         IR SYMBOLIQUE TYPÉE             │
│  Concepts / Connaissances / Contraintes │
│         Règles / Transitions            │
└───────────────────┬─────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│        MOTEUR ÉPISTÉMIQUE               │
│                                         │
│  Observer       Generator               │
│  Estimator      Transpiler              │
│  Solver         Validator               │
│  KnowledgeBase  Resolver                │
│                                         │
│       Procédures et règles              │
└───────────────────┬─────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│           RUNTIME D'EFFETS              │
│  Permissions / JSON Schema / Exécution  │
└────────────┬────────────────┬───────────┘
             │                │
             ▼                ▼
       ┌───────────┐    ┌───────────────┐
       │ Capteurs  │    │ Actionneurs   │
       │ JSON IN   │    │ JSON OUT      │
       └───────────┘    └───────────────┘

       ADAPTATEURS PYTHON / API / MATÉRIEL

═══════════════════════════════════════════
  OBSERVABILITÉ TRANSVERSALE
  OpenTelemetry / Logs / Metrics / Traces
═══════════════════════════════════════════
```

Les flèches représentent les responsabilités architecturales, pas nécessairement un ordre d'exécution fixe.

Les observations peuvent être acquises pendant la résolution. Les actionneurs ne sont déclenchés que lorsqu'une procédure autorisée atteint une étape d'exécution réelle.

---

# 4. Spécification du langage

## 4.1 Sémantique fondamentale

Le langage doit supporter :

- Évaluation stricte.
- Fonctions pures.
- Closures lexicales.
- Immutabilité.
- Récursion.
- Polymorphisme paramétrique.
- Types algébriques.
- Records et listes.
- Pattern matching.
- Modules et imports.
- Inférence Hindley-Milner.
- Composition fonctionnelle.

Les types dimensionnels, les connaissances et les contraintes sont fournis par des bibliothèques.

## 4.2 Syntaxe

La syntaxe doit rester proche d'OCaml.

Exemple :

```ocaml
module Mechanics = struct

  type plate = {
    width : Length.t;
    height : Length.t;
    thickness : Length.t option;
  }

  let area p =
    Length.multiply p.width p.height

  let volume p thickness =
    Area.multiply_length (area p) thickness

end
```

Le compilateur infère les types des fonctions lorsque les signatures des opérations appelées sont connues.

## 4.3 Modules

Les modules permettent d'organiser les DSL.

Exemples :

- `Mechanics`
- `Robotics`
- `Finance`
- `Logistics`
- `Knowledge`
- `Constraints`

Les domaines ne doivent pas nécessiter de nouveaux mots-clés fondamentaux.

## 4.4 Métaprogrammation

Le langage doit permettre, progressivement :

- La définition de nouveaux opérateurs.
- La composition de nouvelles abstractions.
- La manipulation d'AST.
- Les macros hygiéniques.
- La construction de syntaxes métiers.
- La génération de programmes.

Les macros avancées sont hors du périmètre du premier MVP.

---

# 5. Métamodèle symbolique

Un domaine doit pouvoir déclarer plusieurs familles d'objets.

## 5.1 Concepts

Un concept représente une entité métier.

Exemples :

- `Plate`
- `Material`
- `Length`
- `Motor`
- `Robot`
- `Invoice`

## 5.2 Relations

Une relation représente un lien entre concepts.

Exemples :

- `has_material`
- `has_thickness`
- `connected_to`
- `depends_on`
- `located_at`

## 5.3 Unités et dimensions

Les unités doivent appartenir aux bibliothèques métiers.

Le noyau ne doit pas contenir de connaissances particulières sur les mètres, les kilogrammes ou les degrés.

Une bibliothèque pourra déclarer les unités et leurs conversions.

Les opérations doivent conserver leur cohérence dimensionnelle.

## 5.4 Règles symboliques

Le métalangage doit permettre de définir :

- Des règles de déduction.
- Des règles de transformation.
- Des règles par défaut.
- Des règles conditionnelles.
- Des invariants.
- Des contraintes.
- Des transitions entre états.

## 5.5 Objectifs

Les objectifs peuvent représenter :

- Une condition à satisfaire.
- Une variable à déterminer.
- Une quantité à minimiser.
- Une quantité à maximiser.
- Un état à atteindre.
- Une hypothèse à tester.

---

# 6. Interfaces d'extensions

Le cœur d'Hypomnesis expose plusieurs abstractions génériques.

| Interface | Responsabilité |
|---|---|
| `Observer` | Acquérir des observations |
| `Generator` | Générer des candidats, structures ou programmes |
| `Estimator` | Proposer des valeurs inconnues |
| `Transpiler` | Transformer une représentation |
| `Solver` | Rechercher une solution |
| `Validator` | Vérifier une proposition |
| `KnowledgeBase` | Interroger et conserver des connaissances |
| `Actuator` | Déclencher une opération extérieure autorisée |
| `Resolver` | Orchestrer les capacités pour atteindre un objectif |

## 6.1 Contrat d'extension

Chaque extension doit exposer :

- Un identifiant unique.
- Une version.
- Un rôle sémantique.
- Une signature d'entrée.
- Une signature de sortie.
- Un JSON Schema d'entrée.
- Un JSON Schema de sortie.
- Ses préconditions.
- Ses dépendances.
- Ses capacités.
- Ses permissions.
- Son backend.
- Ses garanties et limitations.
- Sa politique de gestion des erreurs.

Les extensions doivent pouvoir être découvertes et inspectées sans exécuter leur code métier.

## 6.2 Backends

Le premier backend est Python.

Les adaptateurs peuvent connecter :

- scikit-learn.
- PyMC.
- PyTorch.
- Z3.
- OR-Tools.
- SciPy.
- Pint.
- RDFLib.
- Des logiciels de CAO.
- Des simulateurs.
- Des API.
- Du matériel physique.

Les interfaces doivent rester indépendantes du backend.

---

# 7. Modèle épistémique

## 7.1 Types de connaissances

Le système doit distinguer :

| Statut | Signification |
|---|---|
| `Observed` | Information issue d'une observation ou source |
| `Derived` | Résultat d'une règle exacte |
| `Estimated` | Résultat d'un modèle d'estimation |
| `Defaulted` | Valeur proposée par une règle de repli |
| `Hypothesis` | Proposition non confirmée |
| `Unknown` | Valeur inconnue |
| `Conflict` | Informations incompatibles |

## 7.2 Provenance

Chaque connaissance doit pouvoir conserver :

- Son identifiant.
- Sa valeur.
- Son type.
- Sa source.
- La méthode employée.
- Les dépendances utilisées.
- L'incertitude éventuelle.
- Le modèle et sa version.
- Les validations réalisées.
- Son historique.

## 7.3 Révision

Lorsqu'une observation change, le moteur doit :

1. Identifier les connaissances dépendantes.
2. Invalider les conclusions concernées.
3. Recalculer les résultats nécessaires.
4. Conserver les anciennes hypothèses dans l'historique.
5. Signaler les contradictions.

## 7.4 Stockage

Le MVP utilisera :

- Des structures immuables en mémoire.
- Un journal d'événements.
- SQLite pour la persistance.
- JSON pour l'importation, l'exportation et les échanges.

Le stockage RDF ou des bases de connaissances plus avancées pourra être ajouté sous forme d'extension.

---

# 8. Programmation procédurale, déclarative et hybride

## 8.1 Programmation procédurale

Une procédure exprime une séquence d'opérations.

Elle peut appeler des fonctions, estimateurs, solveurs et validateurs.

## 8.2 Programmation déclarative

Un problème est défini par :

- Des variables.
- Des domaines de valeurs.
- Des contraintes.
- Des préférences.
- Des objectifs.

Un solveur sélectionné recherche une solution.

## 8.3 Transitions

Une transition contient :

- Un état initial.
- Des préconditions.
- Une action possible.
- Des effets attendus.
- Un état résultant.

Le système doit permettre la planification sans exécuter immédiatement les actions.

## 8.4 Composition hybride

Une procédure doit pouvoir :

- Déclencher des observations.
- Construire des hypothèses.
- Appeler un estimateur.
- Construire un problème.
- Appeler un solveur.
- Vérifier la solution.
- Produire une commande d'actionneur.
- Contrôler le résultat de l'action.

Toutes ces opérations utilisent les mêmes concepts métiers.

---

# 9. Capteurs, actionneurs et gestion des effets

## 9.1 Principe

Le noyau fonctionnel ne doit pas interagir directement avec le monde extérieur.

Les capteurs et actionneurs constituent une frontière explicite entre le langage pur et les opérations à effets.

Le système doit conserver la possibilité de représenter les effets sous forme de valeurs immuables.

Le runtime est seul responsable de leur exécution.

## 9.2 Modèle des capteurs

Un capteur produit une observation structurée.

Le fonctionnement est :

**Backend Python → JSON → JSON Schema → Observation typée → KnowledgeBase**

Un capteur peut représenter :

- Un capteur physique.
- Une caméra.
- Un système OCR.
- Une réponse HTTP.
- Une lecture de fichier.
- Une requête de base de données.
- Une sortie de simulateur.

Chaque capteur doit disposer d'un schéma de sortie.

Une requête de lecture peut également être associée à un schéma d'entrée.

## 9.3 Modèle des actionneurs

Un actionneur reçoit une commande structurée.

Le fonctionnement est :

**Programme symbolique → Commande JSON → Validation JSON Schema → Autorisation → Adaptateur Python → Action**

L'actionneur retourne un message de résultat.

Les actions possibles comprennent :

- Déplacer un moteur.
- Modifier un fichier.
- Envoyer un message.
- Appeler une API.
- Commander un robot.
- Déclencher une opération dans un logiciel de CAO.
- Effectuer une opération métier autorisée.

Chaque actionneur doit posséder un schéma de commande et un schéma de réponse.

## 9.4 Contrats JSON Schema

La version initiale cible JSON Schema Draft 2020-12.

Les schémas doivent être versionnés et identifiables par leur `$id`.

Exemple de commande d'actionneur :

```json
{
  "command_id": "cmd-42",
  "motor_id": "motor_1",
  "position_deg": 90,
  "speed_deg_s": 20
}
```

Exemple de JSON Schema associé :

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://schemas.example.org/hypomnesis/motor.move/1.0.0",
  "title": "MotorMoveCommand",
  "type": "object",
  "properties": {
    "command_id": {
      "type": "string",
      "minLength": 1
    },
    "motor_id": {
      "type": "string",
      "minLength": 1
    },
    "position_deg": {
      "type": "number",
      "minimum": 0,
      "maximum": 180
    },
    "speed_deg_s": {
      "type": "number",
      "exclusiveMinimum": 0
    }
  },
  "required": [
    "command_id",
    "motor_id",
    "position_deg",
    "speed_deg_s"
  ],
  "additionalProperties": false
}
```

La plage 0–180° est propre à cet exemple d'actionneur, et non à tous les moteurs.

Un JSON Schema ne garantit pas la sécurité physique d'une commande. Les limites dynamiques, les collisions, les permissions et les contraintes matérielles doivent être vérifiées séparément.

## 9.5 Transport

Pour le MVP, les échanges pourront utiliser des fichiers JSON.

Cela facilite :

- La simulation de capteurs.
- Les tests de reproductibilité.
- L'inspection des messages.
- L'enregistrement des scénarios.
- L'intégration de programmes externes.

L'architecture doit cependant séparer le contrat JSON du transport.

Les transports futurs pourront inclure :

- Appels en mémoire.
- Fichiers.
- HTTP.
- WebSocket.
- Files de messages.
- Processus locaux.
- Communications réseau.

## 9.6 Enveloppe de message

Les échanges doivent pouvoir inclure :

```text
message_id
schema_id
schema_version
timestamp
correlation_id
trace_context
payload
```

Le contenu `payload` est validé par le JSON Schema de l'opération.

Les métadonnées de corrélation servent à l'exécution et à l'observabilité.

## 9.7 États des commandes

Une commande peut passer par les états :

- `Created`
- `Validated`
- `Authorized`
- `Dispatched`
- `Accepted`
- `Completed`
- `Rejected`
- `Failed`
- `TimedOut`
- `UnknownOutcome`

L'acceptation d'une commande ne garantit pas l'achèvement de l'action.

Le runtime doit prendre en charge des identifiants de commande, des délais d'expiration et des politiques de nouvelle tentative.

Les nouvelles tentatives doivent éviter les doubles exécutions lorsque l'action n'est pas idempotente.

## 9.8 Validation des effets

Avant une opération externe :

1. Valider la structure JSON.
2. Vérifier la signature et la version du contrat.
3. Vérifier les permissions.
4. Appliquer les contraintes métiers.
5. Vérifier les règles de sécurité.
6. Exécuter l'adaptateur autorisé.
7. Valider sa réponse.
8. Enregistrer le résultat.
9. Observer les effets réels lorsque nécessaire.

L'application hôte doit pouvoir imposer une validation humaine avant certaines actions.

---

# 10. Gestion fonctionnelle des effets

## 10.1 Objectif

Permettre la composition d'opérations externes sans introduire de mutation arbitraire dans le langage.

## 10.2 Représentation

Une opération à effet est représentée comme une valeur typée.

API conceptuelle :

```ocaml
type 'a effect

val return : 'a -> 'a effect

val bind :
  'a effect ->
  ('a -> 'b effect) ->
  'b effect
```

Les fonctions du langage construisent et composent des descriptions d'opérations.

Seul le runtime peut interpréter ces effets.

## 10.3 Exécution

Trois modes doivent être envisagés :

- **Simulation** : effets remplacés par des réponses fictives.
- **Dry-run** : préparation et validation des commandes sans exécution.
- **Production** : opérations exécutées avec permissions et surveillance.

Un même programme doit pouvoir utiliser ces modes sans modification de sa logique métier.

---

# 11. Pipeline épistémologique complet

Hypomnesis doit pouvoir représenter le cycle :

**Observer → Formaliser → Générer → Estimer → Résoudre → Valider → Décider → Agir → Observer**

## 11.1 Observation

Acquisition d'informations par les capteurs ou les sources externes.

## 11.2 Formalisation

Transformation des données observées en connaissances symboliques typées.

## 11.3 Génération

Production de candidats, hypothèses, modèles, programmes ou solutions.

## 11.4 Estimation

Complétion des propriétés inconnues au moyen de modèles locaux.

## 11.5 Résolution

Recherche de solutions respectant les contraintes définies.

## 11.6 Validation

Vérification des résultats et production éventuelle de contre-exemples.

## 11.7 Décision

Sélection d'une proposition selon les règles, les objectifs, les risques et les permissions.

## 11.8 Action

Construction puis exécution contrôlée d'une commande JSON par un actionneur.

## 11.9 Rétroaction

Observation de l'état obtenu après l'action.

Les nouvelles observations peuvent :

- Confirmer les effets attendus.
- Détecter un échec.
- Réfuter une hypothèse.
- Déclencher une nouvelle estimation.
- Modifier un plan.
- Relancer une résolution.

La boucle doit posséder des budgets de calcul, des limites d'itération et des critères d'arrêt.

---

# 12. Observabilité et instrumentation

## 12.1 Objectif

Hypomnesis doit permettre de comprendre :

- Quelle demande a déclenché une exécution.
- Quel programme ou DSL a été utilisé.
- Quelles connaissances ont été consultées.
- Quelles hypothèses ont été produites.
- Quels estimateurs et solveurs ont été appelés.
- Quels validateurs ont accepté ou rejeté des résultats.
- Quelles actions ont été demandées.
- Quelles actions ont effectivement réussi.
- Où se produisent les erreurs et les ralentissements.
- Quel est le coût des opérations, notamment des appels LLM.

## 12.2 Standards

OpenTelemetry constitue le standard principal d'instrumentation.

La solution doit produire :

- Des traces distribuées.
- Des métriques.
- Des logs structurés.
- Des informations de corrélation.

Les données d'observabilité doivent pouvoir être exportées via OTLP.

## 12.3 Traces

Chaque pipeline doit posséder un identifiant d'exécution.

Les étapes importantes produisent des spans :

```text
hypomnesis.run
├── llm.transcribe
├── language.parse
├── language.typecheck
├── observer.read
├── knowledge.resolve
├── estimator.predict
├── solver.solve
├── validator.check
├── actuator.authorize
├── actuator.execute
└── observer.verify
```

Les spans doivent pouvoir contenir :

- Le nom de l'opération.
- Son statut.
- Sa durée.
- L'identifiant du plugin.
- Sa version.
- Le domaine métier.
- Le résultat de validation.
- L'identifiant du schéma.
- Les informations de corrélation non sensibles.

## 12.4 Métriques

Les métriques initiales doivent couvrir :

| Métrique | Description |
|---|---|
| `hypomnesis_runs_total` | Nombre d'exécutions |
| `hypomnesis_run_duration_seconds` | Durée des pipelines |
| `hypomnesis_plugin_calls_total` | Appels aux plugins |
| `hypomnesis_plugin_duration_seconds` | Latence des plugins |
| `hypomnesis_schema_validation_total` | Résultats des validations JSON |
| `hypomnesis_solver_duration_seconds` | Temps de résolution |
| `hypomnesis_estimator_calls_total` | Nombre d'estimations |
| `hypomnesis_validator_rejections_total` | Rejets des validateurs |
| `hypomnesis_actuator_commands_total` | Commandes d'actionneurs |
| `hypomnesis_actuator_failures_total` | Échecs des actionneurs |
| `hypomnesis_llm_tokens_total` | Consommation de tokens, si disponible |

Les labels devront éviter les valeurs à forte cardinalité, notamment les identifiants individuels de messages, de traces et de connaissances.

## 12.5 Logs

Les logs devront être structurés et corrélables aux traces.

Exemple :

```json
{
  "level": "INFO",
  "event": "actuator.command.accepted",
  "run_id": "run-001",
  "plugin": "motor.move",
  "command_id": "cmd-42",
  "schema_version": "1.0.0",
  "status": "accepted"
}
```

Les messages ne devront pas contenir systématiquement les données brutes des capteurs, les prompts LLM ou les informations personnelles.

Les données sensibles devront être filtrées ou expurgées.

## 12.6 Stack d'observabilité

| Composant | Utilisation |
|---|---|
| OpenTelemetry SDK | Instrumentation |
| OpenTelemetry Collector | Réception et export des signaux |
| Prometheus | Métriques |
| Grafana | Tableaux de bord |
| Jaeger ou Grafana Tempo | Visualisation des traces |
| Grafana Loki | Agrégation des logs, optionnelle |
| JSON Logs | Journalisation structurée |

## 12.7 Tableaux de bord

Le MVP devra fournir au minimum :

**Dashboard Runtime**

- Nombre d'exécutions.
- Durées d'exécution.
- Erreurs.
- Consommation de ressources.

**Dashboard Plugins**

- Appels par catégorie.
- Latences.
- Taux d'échec.
- Validations JSON rejetées.

**Dashboard Epistemic**

- Hypothèses produites.
- Estimations effectuées.
- Conflits détectés.
- Validations réussies ou échouées.
- Révisions de connaissances.

**Dashboard Actuators**

- Commandes créées.
- Commandes autorisées.
- Commandes exécutées.
- Échecs et expirations.
- Latences.
- Écarts entre effets attendus et observés.

## 12.8 Traçabilité épistémique et observabilité

Les deux systèmes sont complémentaires et doivent rester distincts.

La provenance épistémique décrit les raisons et dépendances d'une conclusion.

L'observabilité décrit comment une opération informatique s'est déroulée.

Une trace OpenTelemetry ne constitue donc pas une preuve logique.

Le système doit cependant pouvoir relier une trace d'exécution à la connaissance, à l'hypothèse ou à la commande concernée.

---

# 13. Architecture du compilateur

## 13.1 Frontend

Responsabilités :

- Lexer.
- Parser.
- Construction de l'AST.
- Résolution des noms.
- Gestion des modules.
- Diagnostics.
- Macros dans les versions ultérieures.

Technologie initiale : Lark.

## 13.2 Système de types

Responsabilités :

- Inférence Hindley-Milner.
- Unification.
- Polymorphisme.
- Vérification des fonctions.
- Compatibilité des signatures.
- Vérification statique des interfaces externes.

Les contraintes dimensionnelles et métiers sont traitées par des systèmes complémentaires.

## 13.3 Représentations intermédiaires

### Core IR

Représente les expressions fonctionnelles :

- Literal.
- Variable.
- Lambda.
- Apply.
- Let.
- Match.
- Record.
- Constructor.

### Domain IR

Représente :

- Concept.
- Relation.
- Knowledge.
- Hypothesis.
- Rule.
- Constraint.
- Provenance.
- Capability.

### Problem IR

Représente :

- Variables.
- Domaines.
- Contraintes.
- Objectifs.
- États.
- Actions.
- Transitions.

### Effect IR

Représente :

- Lecture d'une source.
- Invocation d'un plugin.
- Construction d'une commande.
- Appel à un actionneur.
- Attente d'un résultat.
- Vérification de l'état observé.

## 13.4 Compilation des contrats

Les signatures des extensions doivent permettre de générer ou de vérifier les contrats JSON Schema.

Les correspondances entre types statiques, types JSON et concepts métiers doivent être définies explicitement.

Le système doit détecter les incompatibilités de schéma avant l'exécution lorsque cela est possible.

Une validation JSON doit également être effectuée à chaque frontière externe.

## 13.5 Runtime

Pour la V0 :

- Interpréteur Python.
- Évaluation fonctionnelle.
- Registre de plugins.
- Gestionnaire d'effets.
- Validation JSON Schema.
- Politiques de permissions.
- Journal d'exécution.
- Instrumentation OpenTelemetry.

L'exécution de code Python arbitraire généré par LLM est interdite.

---

# 14. Compatibilité LLM

## 14.1 Rôle

Le LLM sert principalement de transcripteur entre langage naturel et langage symbolique.

Il peut proposer :

- Des concepts.
- Des relations.
- Des programmes candidats.
- Des objectifs.
- Des contraintes.
- Des hypothèses à examiner.

## 14.2 Génération contrôlée

La génération doit s'appuyer sur :

- Les descriptions de domaines.
- Les signatures de fonctions.
- Les grammaires.
- Les types.
- Les catalogues de plugins.
- Les contraintes de permissions.

## 14.3 Validation

La sortie du LLM doit être :

1. Analysée.
2. Typée.
3. Résolue symboliquement.
4. Validée.
5. Autorisée avant tout effet externe.

## 14.4 Incertitudes

Les informations manquantes doivent rester explicites.

Le moteur doit pouvoir utiliser les estimateurs métiers, plutôt que laisser le LLM inventer directement les valeurs.

## 14.5 Explicabilité

Le système doit pouvoir reformuler :

- Ce qu'il a compris.
- Les informations utilisées.
- Les hypothèses proposées.
- Les règles appliquées.
- Les résultats des validateurs.
- Les actions qui seront exécutées.

---

# 15. Architecture logicielle

## 15.1 Stack technique

| Fonction | Technologie initiale |
|---|---|
| Compilateur prototype | Python |
| Parsing | Lark |
| Types et contrats | Dataclasses, Pydantic |
| JSON Schema | jsonschema |
| Règles et graphes | Implémentation dédiée, NetworkX |
| Solveur initial | Z3 |
| Estimateur initial | scikit-learn |
| Gestion des unités | Pint |
| Stockage | SQLite, JSON |
| Tests | pytest, Hypothesis |
| Qualité Python | Ruff, Pyright |
| Observabilité | OpenTelemetry |
| Métriques | Prometheus |
| Visualisation | Grafana |
| Traces | Jaeger ou Tempo |
| CI/CD | GitHub Actions |
| Packaging | pyproject.toml |

## 15.2 Organisation du dépôt

```text
hypomnesis/
├── docs/
│   ├── specification/
│   ├── architecture/
│   └── adr/
│
├── src/hypomnesis/
│   ├── language/
│   │   ├── grammar/
│   │   ├── parser.py
│   │   ├── ast.py
│   │   ├── resolver.py
│   │   └── typesystem/
│   │
│   ├── ir/
│   │   ├── core.py
│   │   ├── domain.py
│   │   ├── problem.py
│   │   └── effect.py
│   │
│   ├── epistemics/
│   │   ├── knowledge.py
│   │   ├── hypotheses.py
│   │   ├── provenance.py
│   │   └── revision.py
│   │
│   ├── capabilities/
│   │   ├── observer.py
│   │   ├── generator.py
│   │   ├── estimator.py
│   │   ├── transpiler.py
│   │   ├── solver.py
│   │   ├── validator.py
│   │   ├── knowledge_base.py
│   │   └── actuator.py
│   │
│   ├── engine/
│   │   ├── registry.py
│   │   ├── rules.py
│   │   ├── resolver.py
│   │   ├── workflow.py
│   │   └── executor.py
│   │
│   ├── effects/
│   │   ├── commands.py
│   │   ├── permissions.py
│   │   ├── dispatcher.py
│   │   └── transports/
│   │
│   ├── contracts/
│   │   ├── schemas/
│   │   ├── registry.py
│   │   ├── validation.py
│   │   └── serialization.py
│   │
│   ├── backends/
│   │   ├── python/
│   │   ├── sklearn/
│   │   └── z3/
│   │
│   ├── observability/
│   │   ├── tracing.py
│   │   ├── metrics.py
│   │   └── logging.py
│   │
│   ├── llm/
│   │   ├── transcription.py
│   │   └── diagnostics.py
│   │
│   └── cli.py
│
├── examples/
│   ├── mechanics/
│   ├── robotics/
│   └── workflows/
│
├── monitoring/
│   ├── otel/
│   ├── prometheus/
│   └── grafana/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── contracts/
│   ├── property/
│   └── benchmarks/
│
└── pyproject.toml
```

---

# 16. MVP : démonstrateur de bout en bout

## 16.1 Objectif

Prouver qu'un DSL métier peut relier langage naturel, connaissances, estimation, résolution, validation et action extérieure, avec contrôle JSON Schema et traçabilité.

## 16.2 Scénario principal : mécanique

Demande utilisateur :

« Crée une plaque de 120 × 80 mm, estime son épaisseur, vérifie sa validité et exporte sa géométrie. »

Pipeline :

1. Le LLM reconnaît le concept `Plate`.
2. Le programme symbolique est compilé.
3. Les dimensions sont normalisées.
4. L'épaisseur manquante est estimée.
5. Un solveur vérifie les contraintes déclarées.
6. Un validateur examine la solution.
7. Un actionneur logiciel reçoit une commande JSON d'export.
8. Le backend Python génère le fichier demandé.
9. Le résultat est renvoyé sous forme JSON.
10. Les traces et métriques sont enregistrées.

## 16.3 Scénario secondaire : capteur et actionneur simulés

Un capteur simulé retourne une température JSON.

Le programme applique une règle métier et produit une commande de ventilateur.

L'actionneur simulé accepte la commande.

Un second capteur confirme ou réfute l'effet attendu.

Ce scénario vérifie la frontière entre le noyau pur et les effets externes.

## 16.4 Critères d'acceptation

Le MVP sera accepté si :

- Un domaine métier peut être défini sans modifier le noyau.
- Les programmes valides du sous-ensemble de langage sont typés et exécutés.
- Les erreurs de types sont détectées avant exécution.
- Deux plugins Python peuvent être substitués derrière la même interface.
- Les messages externes sont validés par leurs JSON Schema.
- Une commande invalide est rejetée avant tout appel d'actionneur.
- Une action non autorisée ne peut pas être exécutée.
- Les résultats des estimateurs conservent leur provenance.
- Une nouvelle observation peut réviser une hypothèse.
- Un solveur externe est appelé à partir de la Problem IR.
- Les commandes d'actionneurs produisent des résultats contrôlés.
- Un programme fonctionne avec des périphériques simulés.
- Une trace permet de suivre les principales étapes d'une exécution.
- Les métriques essentielles sont visibles dans Grafana.
- Une transcription LLM peut être validée avant exécution.

---

# 17. Plan d'implémentation

Les estimations suivantes correspondent à un développeur expérimenté utilisant des bibliothèques existantes et une assistance IA. Elles restent indicatives.

| Phase | Durée estimée | Livrable |
|---|---|---|
| 0. Fondations | 1 semaine | Contrats, ADR, CI et architecture |
| 1. Langage minimal | 2–3 semaines | Parser, AST, types, interpréteur |
| 2. Métamodèle épistémique | 2 semaines | Concepts, connaissances, provenance |
| 3. Plugins et JSON Schema | 2 semaines | Interfaces, registre, adaptateurs |
| 4. Raisonnement hybride | 2–3 semaines | Règles, estimateurs, Z3 |
| 5. Effets et actionneurs | 2 semaines | Sensor/Actuator, runtime contrôlé |
| 6. Observabilité | 1 semaine | Traces, métriques, dashboards |
| 7. Intégration LLM | 2 semaines | Transcription et validation |
| 8. Stabilisation | 1–2 semaines | Tests, documentation, benchmark |

**Enveloppe indicative : 15 à 18 semaines pour un MVP complet.**

L'instrumentation élémentaire et la validation des contrats doivent commencer dès les premières phases, même si les dashboards complets arrivent plus tard.

## Phase 0 — Fondations

- Créer le dépôt.
- Définir les conventions de développement.
- Mettre en place la CI.
- Rédiger les ADR.
- Spécifier les différentes IR.
- Spécifier les contrats JSON Schema.
- Définir les interfaces des extensions.

## Phase 1 — Langage minimal

- Implémenter le parser avec Lark.
- Construire l'AST.
- Ajouter les fonctions et closures.
- Implémenter l'inférence HM de base.
- Ajouter les records et types algébriques.
- Implémenter l'interpréteur.

## Phase 2 — Métamodèle

- Définir les concepts et relations.
- Définir les connaissances.
- Gérer les hypothèses et la provenance.
- Construire le graphe de dépendances.
- Implémenter la révision des connaissances.

## Phase 3 — Extensions et contrats

- Implémenter les interfaces standard.
- Créer le registre des capacités.
- Ajouter les adaptateurs Python.
- Implémenter la validation JSON Schema.
- Ajouter les versions des schémas.
- Définir les conversions entre types et JSON.

## Phase 4 — Raisonnement

- Implémenter les règles.
- Construire le moteur de résolution.
- Intégrer les estimateurs.
- Intégrer Z3.
- Ajouter les validateurs.
- Implémenter les procédures hybrides.

## Phase 5 — Effets

- Construire l'Effect IR.
- Implémenter les transports JSON.
- Ajouter les capteurs simulés.
- Ajouter les actionneurs simulés.
- Implémenter les permissions.
- Ajouter les réponses d'exécution.
- Tester les nouvelles tentatives et les échecs.

## Phase 6 — Observabilité

- Instrumenter les étapes importantes.
- Déployer un Collector OpenTelemetry.
- Exposer les métriques.
- Configurer Prometheus.
- Configurer Grafana.
- Ajouter une visualisation des traces.
- Construire les dashboards initiaux.

## Phase 7 — LLM

- Publier les descriptions des DSL.
- Implémenter la transcription.
- Valider les programmes générés.
- Détecter les informations manquantes.
- Produire des diagnostics.
- Tester les demandes ambiguës.

## Phase 8 — Stabilisation

- Réaliser les tests de bout en bout.
- Ajouter les benchmarks.
- Vérifier les contrats de plugins.
- Documenter la création de domaines.
- Publier un SDK expérimental.

---

# 18. Feuille de route après le MVP

## Version 0.2 — Raisonnement avancé

- Plusieurs estimateurs concurrents.
- Inférence bayésienne.
- Contraintes souples.
- Comparaison des modèles.
- Raisonnement non monotone.
- Révision avancée des connaissances.

## Version 0.3 — Métaprogrammation

- Macros hygiéniques.
- DSL syntaxiquement extensibles.
- Génération guidée par les types.
- Générateurs de programmes.
- Optimisation des IR.

## Version 0.4 — Planification et synthèse

- Règles de transition avancées.
- Planificateurs externes.
- Synthèse inductive.
- Boucles CEGIS.
- Recherche de stratégies.
- Simulation de systèmes.

## Version 1.0 — Runtime embarquable

- Backend Rust.
- VM ou bytecode autonome.
- API C pour intégration native.
- Communication entre processus.
- Gestion avancée des permissions.
- Isolation des extensions.
- Compatibilité avec des appareils embarqués.

---

# 19. Risques et contraintes

| Risque | Mesure prévue |
|---|---|
| Langage trop complexe | Noyau réduit, extensions spécialisées |
| Incompatibilité des plugins | Contrats JSON Schema versionnés |
| Types et JSON divergents | Signatures canoniques et vérification croisée |
| Erreurs d'estimation | Conditions de validité, provenance et validateurs |
| Règles contradictoires | Détection de conflits et politiques de résolution |
| Solveurs incompatibles | Registre des capacités et validation des problèmes |
| Actions dangereuses | Permissions et validation métier |
| Doubles commandes | Identifiants et gestion de l'idempotence |
| Mauvaises observations | Validation structurelle et tests de cohérence |
| Génération LLM incorrecte | Parsing, typage, validation et autorisation |
| Surcharge d'observabilité | Échantillonnage, agrégation et limites de cardinalité |
| Données sensibles dans les logs | Filtrage et contrôle de la rétention |
| Dépendance à Python | IR et contrats indépendants du backend |

---

# 20. Hypothèses de recherche

**H1 — Extensibilité**

Un même métalangage permet de décrire plusieurs systèmes métiers sans modifier son noyau.

**H2 — Fiabilité**

Le passage par une représentation symbolique typée et validée réduit les erreurs non détectées par rapport à la génération directe de code par LLM.

**H3 — Composition hybride**

Les règles symboliques, estimateurs, solveurs et procédures peuvent être combinés au moyen d'une interface commune.

**H4 — Révision épistémique**

Les conclusions peuvent être révisées automatiquement lorsque les observations ou hypothèses dont elles dépendent changent.

**H5 — Séparation des effets**

Un système fonctionnel peut décrire des actions externes sans les exécuter directement.

**H6 — Interopérabilité**

Des contrats JSON Schema permettent de remplacer les capteurs, actionneurs et bibliothèques externes sans modifier les programmes métiers.

**H7 — Traçabilité**

La combinaison de la provenance épistémique et de l'observabilité technique permet d'expliquer les décisions et de diagnostiquer les opérations.

Ces hypothèses devront être testées indépendamment, avec des expériences reproductibles.

---

# 21. Critères de réussite du projet

Hypomnesis devra démontrer qu'il est possible de :

1. Créer un DSL métier à partir d'un métalangage fonctionnel.
2. Décrire les concepts, règles, contraintes et transitions d'un système.
3. Connecter les bibliothèques Python existantes.
4. Acquérir des observations via des messages JSON validés.
5. Produire des hypothèses et des estimations justifiées.
6. Construire et résoudre des problèmes déclaratifs.
7. Orchestrer des procédures.
8. Valider des propositions et gérer les contre-exemples.
9. Commander des actionneurs avec des contrats JSON Schema.
10. Vérifier les effets réels par rétroaction.
11. Observer toute la chaîne avec des outils standards.
12. Utiliser un LLM comme interface de transcription vers le DSL.
13. Réutiliser le noyau dans plusieurs domaines indépendants.

---

# 22. Principe architectural final

Hypomnesis repose sur quatre fondations.

**Un langage fonctionnel minimal** pour exprimer des programmes et des modèles de façon structurée.

**Un métalangage symbolique** pour décrire les connaissances, capacités, règles et objectifs de chaque domaine.

**Un runtime d'extensions à effets contrôlés** pour connecter les moteurs existants, les capteurs et les actionneurs par des contrats JSON.

**Un moteur épistémique observable** pour organiser les observations, les hypothèses, les déductions, les estimations, les validations et les décisions.

La séparation entre ces fondations doit rester explicite.

La philosophie du projet est la suivante :

> Hypomnesis ne remplace pas les algorithmes, les logiciels ou les systèmes physiques. Il fournit un langage pour décrire leurs connaissances, leurs capacités et leurs interactions, afin que des systèmes intelligents puissent les composer, les vérifier et les utiliser de manière contrôlée.

**La finalité est de permettre la construction de systèmes métiers intelligents, explicables et extensibles, où le langage naturel devient une interface vers un raisonnement symbolique et des actions vérifiables.**
