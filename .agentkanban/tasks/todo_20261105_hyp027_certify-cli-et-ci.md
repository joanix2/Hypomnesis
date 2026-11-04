---
title: "TODO HYP-027 · Certification CLI sans faux succès"
lane: qa
created: 2026-11-05T00:20:00+01:00
updated: 2026-11-05T00:20:00+01:00
description: "Checker Lean réel, diagnostics atomiques et couverture honnête des exemples"
priority: P0
tags: [certification, ci, compilateur, outillage, python]
---

# Itération 1

- [x] Ajouter --certify, découverte du checker, délai et refus explicites.
- [x] Conserver le certificat demandé et nettoyer les temporaires.
- [x] Garantir une unique sortie JSON finale et la session réellement compilée.
- [x] Tester refus d'une élaboration falsifiée avec le vrai checker.
- [x] Intégrer le pont en CI et préciser P3 sans élargir les preuves.
- [x] Certifier tous les exemples ou documenter précisément les formes encore bloquantes.
- [x] Valider et proposer seulement le périmètre réellement terminé.

# Itération 2 — couverture globale encore ouverte

- [x] Certifier effectivement tous les exemples après extensions formelles
  HYP-021/HYP-150 et traitement des autres formes bloquantes rencontrées.

# Itération 3 — dernier obstacle mesuré

- [x] Traduire les alternatives racines en case, signatures de slots compatibles.
- [x] Tester gardes sans réessai, permutations et mutations incompatibles.
- [x] Exiger six acceptations Lean et CLI réelles en CI/validateur.
- [x] Actualiser couverture et limites ; validations complète/rapide/graphe.
