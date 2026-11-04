---
title: "HYP-015 · TODO"
lane: qa
created: 2026-11-04T15:00:00+01:00
updated: 2026-11-04T18:19:29+01:00
description: "Checklist de HYP-015"
priority: P1
tags: [dette, observabilite, python]
---

# Iteration 1

État des lieux (vérifié) : `observability/trace.py` (84 lignes) définit `Span` (nom, `span_id`, `parent_id`, début, fin, statut, attributs) et `Tracer` (`trace_id`, `spans`, `span()` gestionnaire de contexte, `tree()` texte, `export()` JSON). Un seul consommateur : `engine/procedure.py` (import L35 ; `ProcedureReport.tracer` L87 ; `export()` dans `to_json` L117 ; `tracer.span(...)` L136, 158, 173, 181, 192 ; `report.tracer.tree()` L280). Noms de spans actuels : `language.typecheck`, `hypomnesis.run`, `observer.read`, `actuator.execute`, … Le test `tests/integration/test_languages.py` (L39) lit `saved["trace"]["spans"][i]["name"]`. Il n'y a aucun `trace_context` dans le code (il n'existe que dans le schéma d'enveloppe). OpenTelemetry n'est **pas** installé.

Décision : conserver la classe `Tracer` comme **façade** (`span`, `tree`, `export`, `trace_id`, `spans`) au-dessus de `opentelemetry-sdk` avec un `InMemorySpanExporter`. Ainsi `procedure.py` n'est pas modifié, ce qui évite tout conflit avec HYP-008 (qui y ajoute l'export du graphe de provenance).

Fichiers : `src/hypomnesis/observability/trace.py`, `tests/unit/test_trace.py` (nouveau). Ne PAS toucher `pyproject.toml` (Lot 0 : `opentelemetry-api`, `opentelemetry-sdk` en dépendances) ni `procedure.py`.

Risques : (1) un `TracerProvider` global partagé entre tests mélangerait les spans : un fournisseur **par instance** de `Tracer`, jamais `set_tracer_provider` ; (2) les identifiants OpenTelemetry sont des entiers : les exporter en hexadécimal (32 et 16 caractères) pour garder le format JSON actuel ; (3) la télémétrie ne doit jamais influer sur le raisonnement (ADR 0005).

- [x] Test de caractérisation avant migration : `Tracer.export()` d'un petit scénario (spans imbriqués, une exception) — clés `trace_id`, `spans[].name/span_id/parent_id/duration_ms/status/attributes`, statut `error` après exception, `tree()` indenté
- [x] Réimplémenter `Tracer.span` avec `provider.get_tracer("hypomnesis").start_as_current_span(name, attributes=…)` et un `SimpleSpanProcessor(InMemorySpanExporter())` propre à l'instance
- [x] Attributs : valeurs converties en types acceptés par OTel (str, bool, int, float) ; les autres en `repr` ; mêmes noms qu'aujourd'hui
- [x] Statut : exception → `StatusCode.ERROR` et statut JSON `"error"`, relevée à la sortie du bloc puis relancée
- [x] `export()` et `tree()` reconstruits depuis `exporter.get_finished_spans()` : mêmes clés, durées en ms arrondies à 2 décimales, `trace_id` en hexadécimal
- [x] Fonction `trace_context(tracer) -> dict` : identifiants de trace et de span courants au format attendu par l'enveloppe (§9.6, schéma `envelope-1.0.0.json`) ; test de conformité par `SchemaRegistry`
- [x] Test : un run avec et sans télémétrie donne les mêmes connaissances (utiliser un `Tracer` désactivé = `NoOpTracerProvider`, ou `KnowledgeBase` comparées après un même run)
- [x] `tests/integration/test_languages.py` et les rapports M0 inchangés (arbre de spans toujours présent)
- [x] `TECHNICAL.md` : section Observabilité (SDK, exportateur mémoire, OTLP préparé pour HYP-070)
- [x] `./scripts/validate.sh rapide`, puis `complet` ; commit en français, mettre la tâche en `qa`
