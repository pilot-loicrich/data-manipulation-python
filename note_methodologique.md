# Note méthodologique — Activité du groupe 1 : bibliothèque

## Question

Quels sites et familles d’ouvrages concentrent l’activité, les retards et les pertes,
et comment ces indicateurs évoluent-ils par mois ?

## Sources

Le jeu attribué au groupe 1 se trouve dans
`data/groupe_01_bibliotheque/groupe_01_bibliotheque/` :

- `emprunts.csv` : événements avec dates, identifiants, durée, valeur déclarée, mode et statut ;
- `ouvrages.csv` : familles, sous-familles et coût de référence ;
- `sites.csv` : localisation et région ;
- `adherents.csv` : segment, ville, âge et date de création.

Le fichier d’emprunts contient 20 563 lignes ; les référentiels contiennent 2 650 adhérents,
420 ouvrages et 11 sites. Les sources sont synthétiques et comportent des anomalies
volontaires.

## Diagnostic

Le CSV brut contient 412 dates absentes, 1 841 durées absentes et 180 occurrences
supplémentaires d’identifiants d’emprunt réutilisés. Les statuts sont enregistrés avec des
variations d’espaces et de casse : après normalisation, les valeurs observées sont rendu,
en_retard et perdu. Le notebook recalcule également les doublons exacts, les valeurs non
convertibles et les clés de faits sans référentiel. Un identifiant répété ne signifie pas
automatiquement un doublon : le statut peut avoir changé.

## Traitements et décisions

1. Les dates sont analysées avec les formats explicitement rencontrés. Les dates vides ou
   non reconnues sont exclues de l’analyse temporelle et leur nombre est rapporté.
2. La durée, le nombre de prolongations et les valeurs en euros sont convertis en types
   numériques ; une valeur non interprétable devient manquante.
3. Les champs descriptifs sont normalisés pour regrouper casse, espaces et accents. Les
   identifiants ne sont pas modifiés.
4. Seules les lignes strictement identiques sont supprimées. Les lignes qui partagent un
   `id_emprunt` mais divergent sont conservées et signalées pour validation métier.
5. Les durées manquantes restent manquantes ; elles sont ignorées par la moyenne de durée,
   mais gardées dans les comptages. Les durées négatives sont écartées.
6. Les référentiels sont joints en gauche et en `many-to-one`. Les lignes orphelines restent
   visibles afin de mesurer les pertes de couverture.
7. Les âges manquants sont imputés par la médiane de leur segment. Les coûts de référence
   manquants sont imputés par la médiane de sous-famille.
8. Un événement est en retard si son statut normalisé vaut `en_retard`. La valeur perdue
   est la valeur déclarée pour un événement dont le statut vaut `perdu` ; c’est une
   estimation de remplacement et non une perte comptable auditée.

## Composant PySpark

`src/library_pipeline.py` charge les sources avec un schéma explicite pour la table de
faits, nettoie les événements, diffuse les trois petits référentiels et écrit un jeu Parquet
partitionné par année dans `data/processed/bibliotheque_projet_spark/`. Les temps et RSS
observés par le notebook sont propres à la machine ; le RSS Python n’inclut pas la mémoire
du processus JVM de Spark.

## Résultats

Le notebook présente les emprunts, retards, pertes, durées moyennes et valeurs déclarées
perdues par région et famille, puis l’évolution mensuelle. Les agrégats sont calculés à
l’exécution afin d’éviter de figer des chiffres qui ne seraient plus à jour après un
changement de source.

## Limites

- Les données synthétiques ne permettent pas de conclure sur une bibliothèque réelle.
- Les statuts sont un état enregistré ; les identifiants répétés n’ont pas d’historique
  garanti et nécessitent une validation métier avant toute déduplication par identifiant.
- Les valeurs déclarées perdues ne sont pas des coûts de remplacement confirmés.
- Les événements sans dimension référencée ne peuvent pas être attribués à une région,
  une famille ou un segment.
- Le test PySpark est local ; il ne démontre pas un gain de vitesse par rapport à Pandas
  pour ce volume.
