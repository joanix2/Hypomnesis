# Démonstrations

Ces projets illustrent le moteur générique ; ils ne font pas partie de son implémentation.
Les tests automatisés les réutilisent sans dépendance du moteur vers les domaines.

| Dossier | Contenu |
|---|---|
| `languages/` | langages métier M2 : mécanique et ventilation, contrats et adaptateurs |
| `programs/` | programmes M1 écrits dans ces langages |
| `examples/` | exemples du métalangage et fragment certifiable par Lean |
| `sortie/` | résultats M0 générés, ignorés dans Git, supprimables et reproductibles |

Depuis la racine du dépôt :

```bash
hypomnesis run demo/examples/basics/tour.hyp
hypomnesis lancer demo/languages/mecanique demo/programs/mecanique/plaque_120x80.hyp
hypomnesis lancer demo/languages/ventilation demo/programs/ventilation/salle_serveurs.hyp
```

Les résultats sont écrits par défaut dans `demo/sortie/`. Utiliser `--sortie DOSSIER`
pour choisir une autre destination. Ne pas versionner les rapports, figures et fichiers
produits par une exécution. Les tests utilisent leurs propres dossiers temporaires.

VS Code détecte automatiquement le contexte d'un programme à partir de la paire
`programs/<nom>/` et `languages/<nom>/`, y compris quand seul `demo/` est ouvert.
