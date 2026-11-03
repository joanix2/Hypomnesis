# Bilan MVP — état au 2026-11-03

Confrontation de l'état réel aux critères d'acceptation du §16.4 du
[cahier des charges](specification/cahier-des-charges-v0.2.md). Chaque ligne renvoie à ce qui
l'établit : une commande à lancer, un test ou un théorème.

| # | Critère (§16.4) | État | Preuve |
|---|---|---|---|
| 1 | Un domaine métier peut être défini sans modifier le noyau | ✅ | domaines `plaque` et `ventilation` (`src/hypomnesis/demos/*/domaine.hyp`) : règles et constantes en Hypomnesis, plugins et contrats à côté ; aucune modification du compilateur ni du runtime |
| 2 | Les programmes valides sont typés et exécutés | ✅ | 141 tests, exemples, `hypomnesis run` |
| 3 | Les erreurs de types sont détectées avant exécution | ✅ | tests ; **prouvé** en Lean pour le fragment (P1) ; certificats revérifiés (`hypomnesis-check`) |
| 4 | Deux plugins substituables derrière la même interface | ✅ | `--estimateur regle|abaque` : même programme, estimations différentes (`test_swapping_the_estimator_keeps_the_program`) |
| 5 | Messages externes validés par leurs JSON Schema | ✅ | relevés du capteur (enveloppe puis contenu), commandes, réponses des actionneurs |
| 6 | Commande invalide rejetée avant tout appel d'actionneur | ✅ | `test_invalid_command_is_rejected_by_contract` (contrat et contraintes métier) |
| 7 | Action non autorisée impossible | ✅ | `--sans-permission` ; `test_unauthorised_command_never_reaches_the_actuator` |
| 8 | Les résultats des estimateurs conservent leur provenance | ✅ | provenance en semi-anneau : modèle, version, confiance ; la validité hérite du support « estimé » |
| 9 | Une nouvelle observation peut réviser une hypothèse | ✅ | `--mesure 5` : 4 conclusions invalidées puis recalculées ; `demo ventilation --panne` : hypothèse réfutée et retirée |
| 10 | Un solveur externe est appelé à partir de la Problem IR | ✅ | Z3 ; solution **revérifiée** en rationnels exacts, indépendamment de Z3 |
| 11 | Les commandes d'actionneurs produisent des résultats contrôlés | ✅ | automate d'états, validation des réponses ; modes simulate, dry-run et production |
| 12 | Un programme fonctionne avec des périphériques simulés | ✅ | `demo ventilation` : capteur et ventilateur simulés, rétroaction bornée |
| 13 | Une trace permet de suivre les principales étapes | 🟡 | arbre de spans aux noms du §12.3, exporté dans `rapport.json` ; **pas encore** d'export OpenTelemetry/OTLP (HYP-070) |
| 14 | Les métriques essentielles sont visibles dans Grafana | ❌ | non commencé (HYP-071 à HYP-074) |
| 15 | Une transcription LLM peut être validée avant exécution | 🟡 | la transcription produit un programme Hypomnesis **typé avant tout effet**, mais par des règles déterministes : aucun LLM branché (pas de clé API ; HYP-081) |

**Bilan : 12 critères démontrés, 2 partiels, 1 absent.**

Au-delà du §16.4 : une partie du compilateur est **certifiée**. Un programme du fragment est
revérifié par un vérificateur Lean prouvé correct, et la sémantique Lean recalcule les mêmes
valeurs que l'interpréteur Python (HYP-020 à HYP-026).

## Sur la bonne voie ?

**Ce que la démonstration confirme.**

- **H3, composition hybride.** Règles symboliques (Hypomnesis), estimation, solveur, validation et
  effets se composent autour d'un même modèle de connaissances, sans code spécifique de
  couplage dans le noyau.
- **H4, révision.** La provenance en semi-anneau rend la révision exacte et locale. C'est
  démontré en Lean et observé dans les deux démonstrateurs.
- **H5, séparation des effets.** Le DSL décide, le dispatcher seul exécute, et aucun chemin ne
  contourne contrat ni permission.
- **H2, fiabilité.** Le typage, puis la certification, attrapent des erreurs avant toute
  exécution. Un certificat altéré à la main est rejeté.

**Les écarts à résorber pour que l'architecture tienne sa promesse.**

1. **L'orchestration est en Python.** Les deux pipelines enchaînent les étapes en Python. Selon
   le cahier des charges, une procédure doit être un programme Hypomnesis dont les effets sont des
   valeurs interprétées par le runtime (§10, HYP-060). C'est l'écart principal.
2. **La Problem IR est écrite à la main.** Elle est construite en Python à partir des constantes
   du DSL. Il faut la dériver des règles du domaine elles-mêmes (HYP-051).
3. **Le fragment certifié est étroit.** Flottants, chaînes, records et polymorphisme local en
   sont exclus. Or le domaine `plaque` utilise des flottants : il n'est pas certifiable
   aujourd'hui (HYP-021, HYP-023).
4. **Pas de LLM réel.** L'hypothèse H2, « réduit les erreurs par rapport à la génération directe
   de code par LLM », n'est pas encore mesurée (HYP-081, HYP-083).
5. **Observabilité standard absente.** Ni OTLP ni Grafana (HYP-070 à HYP-074).

## Prochaines itérations proposées

| Ordre | Itération | Pourquoi |
|---|---|---|
| 1 | Effets comme valeurs dans le langage : un `'a effect`, et le pipeline plaque réécrit en Hypomnesis | ferme l'écart 1, cœur de la promesse (§10) |
| 2 | Transcription par Claude avec boucle de diagnostics du compilateur, sur un jeu de demandes | mesure H2, ferme le critère 15 |
| 3 | Problem IR générée depuis des contraintes déclarées dans le DSL | ferme l'écart 2 |
| 4 | Export OTLP et stack Grafana | critères 13 et 14 |
| 5 | Flottants et records dans le fragment Lean | rend le domaine `plaque` certifiable |
