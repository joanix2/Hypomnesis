---
title: "HYP-042 · Correspondance types Hypomnesis ↔ JSON Schema"
lane: todo
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P0 · L · Phase 3 — Extensions et contrats · dépend de HYP-041"
---

## Conversation

### user

**Ticket** HYP-042 · **Priorité** P0 · **Taille** L · **Epic** Phase 3 — Extensions et contrats · **Dépend de** HYP-041 · **Labels** python, contrats

#### Contexte

§13.4 : les signatures des extensions doivent permettre de générer ou de vérifier les contrats JSON Schema ; les correspondances entre types statiques, types JSON et concepts sont explicites.

#### Tâches proposées

- Définir la correspondance (ADR) : int, float, string, bool, unit, records, variants (objet étiqueté), listes, option.
- Générer un schéma depuis un type et vérifier la compatibilité entre une signature et un schéma déclaré.
- Encodage et décodage valeur ↔ JSON.

#### Critères d'acceptation

- Pour tout type supporté : `decode(encode(v)) == v` et `encode(v)` est conforme au schéma généré (test Hypothesis).
- Une signature incompatible avec le schéma du manifeste est refusée avant toute exécution.
- ADR rédigée.

#### Fichiers concernés

- `src/hypomnesis/contracts/`
- `docs/adr/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`

### agent

Plan approuvé le 2026-11-04 : génération Draft 2020-12 et codec typé réversible,
contrôle conservateur et directionnel des contrats (entrée : type inclus dans contrat ;
sortie : contrat inclus dans type), sans chargement de backend. Le sous-ensemble non
vérifiable sera refusé explicitement. Les options deviennent des objets étiquetés ; les
ponts existants et leurs consommateurs seront migrés, conformément au choix explicite
de l'utilisateur. Les grands entiers resteront exacts, y compris via `Json.t`.

Prise en charge : scalaires finis, unit, tuples, records, variants, listes, options,
alias, paramètres concrets et récursion régulière. Fonctions et types ouverts refusés.
ADR, tests Hypothesis et validations Python/Lean avant publication. Aucune nouvelle
fonctionnalité LLM. Le couloir reste inchangé.

Le sous-agent d'implémentation n'avait pas accès aux outils et n'a rien modifié :
reprise directe par l'agent principal sur `hyp-042-types-json-schema`.

### user

### agent

**HYP-042 implémentée et vérifiée — revue humaine attendue ; couloir inchangé.**

Livraison (commit `91b1629`) :

- ADR 0010 acceptée : représentation structurelle unique, limites et migration.
- `contracts/codec.py` : `TypeCodec(checker, signature_ou_type)`, `schema`, `encode`, `decode`.
  Types clos, alias, instanciations, records nominaux, variants, tuples, listes et récursion
  régulière ; refus des fonctions, inconnues et récursions non régulières. Schémas locaux
  `$defs`/`$ref`, contrôle de forme et erreurs avec chemin JSON. L'environnement n'est pas muté.
- `contracts/compatibility.py` : inclusion structurelle directionnelle conservatrice.
  Entrées : encodages du type inclus dans le contrat. Sorties : contrat inclus dans le type.
  Mots-clés hors sous-ensemble refusés explicitement, références locales ou ressources déjà
  enregistrées uniquement ; aucun téléchargement ni backend importé.
- `ExtensionRegistry.prepare` rend `PreparedExtension` avec métadonnées copiées, codecs et
  méthodes `encode_input`/`decode_output` qui valident aussi les contrats concrets. L'inspection
  `plugins list|show` n'exige toujours pas les schémas installés. HYP-044 devra utiliser cette
  préparation avant le chargement effectif des extensions ; ce chargement n'est pas anticipé ici.
- `parse_type` et `Checker.resolve_type` réutilisent grammaire et résolution du compilateur.
  `SchemaRegistry.schema` rend une copie ; l'enregistrement possède aussi sa propre copie.
- `runtime/json.py` partage les conversions avec les ponts moteur et la primitive native :
  options étiquetées ; `Json.Int of int` préserve les grands entiers ; `Json.Num` et les
  flottants restent flottants. `Json.int` lit sans perte ; `Json.num` convertit explicitement.
  NaN, infinis, clés invalides/dupliquées et listes mal formées refusés.
- Migration des attentes JSON du banc mécanique et des explications numériques.
  Les contrats M2 capteurs/actionneurs n'exposaient pas d'option : leurs schémas/adaptateurs
  ne sont pas modifiés artificiellement. Aucun développement de fonctionnalité LLM.
- Documentation technique, référence du langage et frontière formelle mises à jour.
  Aucune modification de la Core IR ni des règles de l'interpréteur : `Json.Int` est un
  constructeur de bibliothèque. `core.to_json` et les codecs restent hors du fragment Lean
  des primitives entières ; aucune preuve JSON nouvelle revendiquée (HYP-043 reste distincte).

Vérifications :

- Sélection codec/compatibilité/effets/langages/provenance/consommateurs : **137 tests passent**.
- Suite totale : **647 tests**, contre 555 avant HYP-042 (92 cas supplémentaires).
- `./scripts/validate.sh rapide` : vert, y compris Ruff, format, Kanban et suite complète.
- `./scripts/validate.sh complet` : vert après indexation des nouveaux fichiers ; tous les
  hooks, Pyright, schémas, compilation Lean, audit des axiomes et vérificateur de certificats.
  Certificat de 121 définitions, fragment monomorphisé de 29 définitions accepté.
- Hypothesis : aller-retour via véritable texte JSON (`allow_nan=False`), validation contre
  le schéma, accord des ponts, compositions, arbres récursifs et `Json.t` lui-même.
  Régressions sur options unit/imbriquées, bool/int, tokens entiers `1.0`, ±grands entiers,
  flottants finis, champs/constructeurs/listes invalides, mutations et préparation sans import.
  Les deux langages M2 enregistrent et restituent aussi une option et un grand entier sans perte.
- `git diff --check` vert ; aucun changement automatique restant des validateurs.

Limites documentées : inclusion suffisante, pas décision de tout JSON Schema ; objets ouverts,
`pattern`, `format`, conditions et contraintes non prises en charge refusés. Un contrat de
sortie `number` non borné n'est pas garanti décodable en `float` ; une entrée `int` non raffinée
ne garantit pas `minimum: 0`. Les références relatives et ressources `$id` imbriquées sont
refusées plutôt qu'interprétées approximativement.

`./scripts/validate.sh graphe` a été exécuté : **échec connu HYP-144**, garde-fou refusant
l'écrasement car `kanban_path_src_hypomnesis_engine_registry_py` manquerait au nouveau graphe.
Le graphe précédent est préservé ; ni contournement ni correction hors périmètre. Ce résultat
ne doit pas être confondu avec les validations rapide/complet, toutes deux vertes.

Publication préparée par fusion en avance rapide dans `main`, selon le workflow confirmé.
La tâche n'est pas passée en `done` ; la décision de couloir reste à l'utilisateur/l'extension.

### user
