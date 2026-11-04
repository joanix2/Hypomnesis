# Démonstrations

Ces projets illustrent le moteur générique ; ils ne font pas partie de son implémentation.
Les tests automatisés les réutilisent sans dépendance du moteur vers les domaines.

| Dossier | Contenu |
|---|---|
| `languages/` | couches M2 : booléen, arithmétique, contraintes, compositions, mécanique et ventilation |
| `programs/` | programmes M1 écrits dans ces langages |
| `examples/` | exemples du métalangage et fragment certifiable par Lean |
| `sortie/` | résultats M0 générés, ignorés dans Git, supprimables et reproductibles |

Depuis la racine du dépôt :

```bash
hypomnesis run demo/examples/basics/tour.hyp
hypomnesis lancer demo/languages/mecanique demo/programs/mecanique/plaque_120x80.hyp
hypomnesis lancer demo/languages/ventilation demo/programs/ventilation/salle_serveurs.hyp
hypomnesis layers demo/languages/composition_a
hypomnesis check demo/languages/composition_a/langage.hyp demo/programs/composition_a/exemple.hyp
```

Chaque couche se déclare dans `langage.hyp` (pas de manifeste JSON). Les bibliothèques
`booleen` et `arithmetique` sont partagées par `contraintes`, `composition_a` et
`composition_b`. La configuration `imports` définit leur DAG ; `layers` en affiche les
générations topologiques. Les I/O des démonstrations mécanique et ventilation portent des
décorateurs Python dans leurs modules d'adaptateurs explicitement déclarés.

Les résultats sont écrits par défaut dans `demo/sortie/`. Utiliser `--sortie DOSSIER`
pour choisir une autre destination. Ne pas versionner les rapports, figures et fichiers
produits par une exécution. Les tests utilisent leurs propres dossiers temporaires.

VS Code détecte automatiquement le contexte d'un programme à partir de la paire
`programs/<nom>/` et `languages/<nom>/`, y compris quand seul `demo/` est ouvert.
