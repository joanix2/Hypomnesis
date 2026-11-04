# Scénario mécanique reproductible (HYP-090)

```bash
pip install -e '.[dev,sklearn]' -e packages/codegen
python -m examples.mechanics.mvp --output demo/sortie/mvp-mecanique
pytest tests/optional/test_mvp_mechanics.py
```

Le client `RecordedClient` renvoie une fixture Hypomnesis figée pour la demande
§16.2. Aucun réseau ni modèle réel, aucune mesure d'inférence prétendue.
La compilation réelle, le modèle sklearn entraîné/validé, le solveur Z3,
le checker M2, le dispatcher et les écritures de fichiers sont exécutés.
Le test est optionnel parce qu'il exige **Codegen et sklearn**, jamais installés
par le job du noyau seul.

## Les dix étapes

| Étape | Span effectif | Preuve dans le rapport |
|---|---|---|
| 1. Transcrire | llm.transcribe | transcription.program, source fixture |
| 2. Compiler | language.typecheck | compilation.typed |
| 3. Normaliser | dimensions.normalize | normalisee, entrées et trou typés |
| 4. Estimer | estimator.predict | epaisseur.estimation, modèle/version/RMSE |
| 5. Résoudre | solver.solve | modèle rationnel revérifié, demande.epaisseur |
| 6. Valider | validator.validate | demande.valide, témoin rejouable |
| 7. Commander | command.dispatch | commande.export, contrôles et états |
| 8. Exporter | actuator.execute | fichier réel, export.result |
| 9. Renvoyer JSON | result.encode | result.json |
| 10. Enregistrer métriques/traces | metrics.record | metrics et trace |

`rapport_mvp.json` contient les dix liens, le résultat, les connaissances et
leur graphe de provenance, le journal, les spans et les mesures. Les métriques
ne sont pas des prémisses de raisonnement (ADR 0005). Le transport JSONL
enregistre commande et réponse validées sous un identifiant de trace unique.
Un refus ou une panne laisse un rapport explicitement failed, pas un succès
de secours ; la panne est aussi propagée à l'appelant.

## Frontières et résultat attendu

- M1 fournit seulement la demande. Ses définitions sont compilées avant
  matérialisation des données pures ; sa procédure d'effets n'est pas exécutée.
- Le codec et les fonctions de confiance viennent d'une **autre session M2**.
  Remplacer `Plaque.verifier_proposition` dans le candidat ne peut donc pas
  modifier le checker utilisé par l'hôte.
- Normalisation, petit côté, contraintes, validation et contenu de la commande
  restent dans `plaque.hyp`, pas dans des formules Python.
- `source_unit` est une indication **explicite de l'hôte**, mm par défaut,
  cm/m disponibles. Ne pas convertir deux fois une réponse déjà en mm.
  Une unité inconnue est refusée.
- L'épaisseur doit rester absente dans la réponse à cette demande : une valeur
  inventée est refusée avant estimation/export. Les autres littéraux restent
  Hypothesis, même s'ils ressemblent à une donnée fournie par l'utilisateur.
- L'estimation synthétique vaut environ 3,214 mm ; le solveur choisit le standard
  3 mm sous les contraintes M2. Le trou conserve les deux propositions ;
  la seconde est choisie explicitement. La divergence reste visible comme
  conflit de propositions, elle n'est pas effacée ou présentée comme un accord.
- Les dimensions finales sont 120 × 80 × 3 mm. La réponse logicielle après
  export est Observed ; la validité issue d'entrées non vérifiées reste
  Hypothesis. Un certificat de validation relatif à M2 et un modèle vérifié
  ne prouvent ni l'intention humaine ni une sûreté mécanique réelle.
- RMSE = erreur empirique hors entraînement, pas intervalle calibré ou garantie
  physique. Z3 revérifié ne signifie pas preuve Lean d'optimalité.

Ce démonstrateur n'étend pas le fragment Lean (HYP-027 reste ouvert), ni
OTLP/Grafana. Il assemble les composants existants sans règle métier dans M3.
