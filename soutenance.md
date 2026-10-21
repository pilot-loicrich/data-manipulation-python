# Support de soutenance - Groupe 3 : cantine

**A completer avant depot : noms des membres et date de passage.** Duree visee : 15 minutes de presentation puis 10 minutes de questions.

## Deroule

1. **Contexte et question (2 min).** Comparer les repas consommes, annules et non recuperes par etablissement, famille de menu et mois.
2. **Diagnostic (3 min).** Les 18 683 lignes brutes incluent 220 doublons exacts, 377 dates manquantes ou invalides et 2 050 grammages manquants. Aucun identifiant de convive, menu ou etablissement n'est orphelin.
3. **Traitements (5 min).** Normalisation des statuts et regimes, conversion du cout (virgules et suffixes EUR), retrait des doublons exacts et des dates non exploitables pour l'analyse temporelle. Les grammages manquants et portions atypiques sont conserves et signales.
4. **PySpark (2 min).** Presenter `src/canteen_pipeline.py`, les jointures gauches et le broadcast des referentiels. Le pipeline Spark est fourni, mais aucune mesure locale n'a ete possible dans l'environnement de preparation.
5. **Resultats et limites (3 min).** Le jeu final contient 18 094 evenements : 12 051 consommes (66,60 %), 3 129 annules (17,29 %) et 2 914 non recuperes (16,11 %). Les evenements consommes totalisent 30 652 portions et 55 466,54 EUR de cout declare, sans extrapolation par portion.

## Questions probables

- **Pourquoi les doublons exacts sont-ils retires ?** Ce sont des copies identiques ; un identifiant reutilise avec des champs divergents devra etre examine avant toute suppression.
- **Pourquoi garder les portions atypiques ?** Le seuil de 10 est un signal pour investigation, pas une regle metier confirmee.
- **Pourquoi garder les grammages manquants ?** Aucune autre colonne ne permet de les reconstruire.
- **Comment le taux de consommation est-il calcule ?** Nombre de lignes au statut normalise `consomme` divise par le nombre d'evenements conserves.
- **Pourquoi ne pas multiplier le cout par les portions ?** La granularite du cout source n'est pas documentee.
- **Pourquoi les jointures gauches ?** Pour garder les evenements et pouvoir mesurer la couverture des referentiels.

Avant depot, renseigner les noms et la date dans le notebook et ce support.
