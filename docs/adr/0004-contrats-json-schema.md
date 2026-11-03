# ADR 0004 — Contrats JSON Schema 2020-12 et enveloppe indépendante du transport

- **Statut :** acceptée
- **Date :** 2026-11-03

## Contexte

Les §6.1 et §9.4–9.7 exigent des contrats versionnés pour chaque extension, capteur et
actionneur, et séparent le contrat du transport.

## Décision

- Tous les contrats sont des schémas **JSON Schema Draft 2020-12** identifiés par un `$id`
  terminé par la version sémantique (`.../motor.move/1.0.0`).
- Deux schémas sont fournis par le noyau (`src/hypomnesis/contracts/schemas/`) :
  - `envelope/1.0.0` : enveloppe de message (§9.6) — `message_id`, `schema_id`,
    `schema_version`, `timestamp`, `correlation_id`, `trace_context` (W3C), `payload` ;
  - `extension-manifest/1.0.0` : manifeste d'extension (§6.1), inspectable sans exécuter le code
    de l'extension. Une extension non idempotente doit déclarer `max_attempts = 1` (§9.7).
- `SchemaRegistry` valide chaque schéma contre le métaschéma à l'enregistrement, refuse un
  `$id` réenregistré avec un contenu différent, et valide un message en deux temps :
  enveloppe, puis `payload` contre le schéma désigné, en vérifiant la cohérence
  `schema_id`/`schema_version`.
- Les formats (`date-time`, `uri`) sont vérifiés (`jsonschema[format-nongpl]`).
- Les exemples de domaine utilisent le domaine réservé `schemas.example.org` tant qu'aucun
  domaine définitif n'est choisi.

## Conséquences

- Un JSON Schema valide la **structure** ; il ne garantit pas la sécurité physique d'une
  commande (§9.4). Permissions, contraintes métier et règles de sécurité restent des étapes
  distinctes du pipeline de validation des effets (§9.8).
- La correspondance types Hypomnesis ↔ JSON (§13.4) est l'objet de la phase 3.
