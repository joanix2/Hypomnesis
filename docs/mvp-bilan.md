# Bilan MVP — état au 2026-11-03

> Tableau historique ci-dessous. Complément HYP-090 : le scénario mécanique
> reproductible possède maintenant dix étapes effectives, une réponse figée
> de test, sklearn versionné, Z3 typé, validateur rejouable et export JSONL/fichier.
> Voir le [guide](architecture/scenario-mecanique.md) et
> `tests/optional/test_mvp_mechanics.py`. Ce test ne revendique ni appel LLM
> réel ni mesure de H2 ; OTLP/Grafana et la couverture Lean totale restent ouverts.

Confrontation de l'état réel aux critères d'acceptation du §16.4 du
[cahier des charges](specification/cahier-des-charges-v0.2.md). Chaque ligne renvoie à ce qui
l'établit : une commande à lancer, un test ou un théorème.

| # | Critère (§16.4) | État | Preuve |
|---|---|---|---|
| 1 | Un domaine métier peut être défini sans modifier le noyau | ✅ | langages M2 `demo/languages/mecanique` et `demo/languages/ventilation` : toute la logique métier en Hypomnesis, adaptateurs Python limités au monde extérieur ; le moteur n'en connaît aucun (`test_engine_contains_no_domain`, ADR 0008) |
| 2 | Les programmes valides sont typés et exécutés | ✅ | 141 tests, exemples, `hypomnesis run` |
| 3 | Les erreurs de types sont détectées avant exécution | ✅ | tests ; **prouvé** en Lean pour le fragment (P1) ; certificats revérifiés (`hypomnesis-check`) |
| 4 | Deux plugins substituables derrière la même interface | ✅ | `--estimateur regle|abaque` : même programme, estimations différentes (`test_swapping_the_estimator_keeps_the_program`) |
| 5 | Messages externes validés par leurs JSON Schema | ✅ | relevés du capteur (enveloppe puis contenu), commandes, réponses des actionneurs |
| 6 | Commande invalide rejetée avant tout appel d'actionneur | ✅ | `test_invalid_command_is_rejected_by_contract` (contrat et contraintes métier) |
| 7 | Action non autorisée impossible | ✅ | `--sans-permission` ; `test_unauthorised_command_never_reaches_the_actuator` |
| 8 | Les résultats des estimateurs conservent leur provenance | ✅ | provenance en semi-anneau : modèle, version, confiance ; la validité hérite du support « estimé » |
| 9 | Une nouvelle observation peut réviser une hypothèse | ✅ | `--observer epaisseur=5` : 4 conclusions invalidées puis recalculées ; `lancer demo/languages/ventilation … --env panne=1` : hypothèse réfutée et retirée |
| 10 | Un solveur externe est appelé à partir de la Problem IR | ✅ | Z3 ; solution **revérifiée** en rationnels exacts, indépendamment de Z3 |
| 11 | Les commandes d'actionneurs produisent des résultats contrôlés | ✅ | automate d'états, validation des réponses ; modes simulate, dry-run et production |
| 12 | Un programme fonctionne avec des périphériques simulés | ✅ | langage `ventilation` : capteur et ventilateur simulés, rétroaction bornée |
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

1. ✅ **Résorbé (HYP-060) : les procédures sont des programmes.** Une procédure est une valeur
   Hypomnesis de type `'a Effect.t`, écrite dans le langage M2 ou le programme M1, que seul le
   moteur interprète (§10). Conception de plaque, révision par mesure et régulation de température
   sont écrites ainsi ; le moteur n'a plus aucune procédure figée.
2. ✅ **Résorbé : contraintes déclarées dans le langage.** Elles sont écrites en Hypomnesis avec le
   type `Problem.problem` de la bibliothèque standard, puis traduites par le moteur en Problem IR.
3. **Le fragment certifié est étroit.** Flottants, chaînes, records et polymorphisme local en
   sont exclus. Or le domaine `plaque` utilise des flottants : il n'est pas certifiable
   aujourd'hui (HYP-021, HYP-023).
4. **Pas de LLM réel.** L'hypothèse H2, « réduit les erreurs par rapport à la génération directe
   de code par LLM », n'est pas encore mesurée (HYP-081, HYP-083).
5. **Observabilité standard absente.** Ni OTLP ni Grafana (HYP-070 à HYP-074).

## Prochaines itérations proposées

| Ordre | Itération | Pourquoi |
|---|---|---|
| 2 | Transcription par Claude avec boucle de diagnostics du compilateur, sur un jeu de demandes | mesure H2, ferme le critère 15 |
| 4 | Export OTLP et stack Grafana | critères 13 et 14 |
| 5 | Flottants et records dans le fragment Lean | rend le domaine `plaque` certifiable |
