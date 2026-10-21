# Note methodologique - Groupe 3 : cantine

## Perimetre

Jeu attribue au groupe 3 : repas servis et referentiels des convives, menus et etablissements. La question est de comparer les repas consommes, annules et non recuperes par region, famille de menu et mois. Les donnees sont synthetiques et couvrent 2023-2024.

## Sources et diagnostic

- `repas_servis.csv` : 18 683 lignes brutes ; 220 doublons stricts (1,18 %).
- 377 dates manquantes ou invalides (2,02 % du brut). Apres retrait des doublons, 369 lignes sans date sont exclues de l'analyse datee.
- 2 050 grammages absents dans le brut (10,97 %). Dans le jeu conserve, 1 997 restent manquants.
- Les statuts et regimes ont des variantes de casse et d'espaces.
- Portions nulles et quantites superieures a 10 sont signalees comme atypiques ; aucune regle metier ne justifie leur suppression.
- Aucun convive, menu ou etablissement orphelin dans les sources brutes.

## Traitements

Les statuts et regimes sont normalises (espaces et casse). Les dates et champs numeriques sont convertis ; les couts avec suffixe EUR ou virgule decimale sont interpretes. Les doublons exacts sont retires et les dates invalides sont exclues des analyses par mois apres comptage. Les grammages manquants sont conserves. Les portions atypiques sont signalees mais ne sont ni supprimees ni plafonnees. Les referentiels sont joints a gauche avec cardinalite `many-to-one` controlee.

Les indicateurs distinguent `consomme`, `annule` et `non_recupere`. Le cout presente est la somme des montants declares dans les evenements consommes. La source ne documente pas si ce montant est un cout unitaire ; il n'est donc pas multiplie par le nombre de portions.

## Resultats recalcules

Le jeu nettoye final contient **18 094 evenements** : **12 051 consommes (66,60 %)**, **3 129 annules (17,29 %)** et **2 914 non recuperes (16,11 %)**. Les evenements consommes totalisent **30 652 portions** et **55 466,54 EUR de cout declare** (somme des valeurs d'evenement, sans multiplication). Il reste 77 evenements avec quantite atypique dans le jeu final.

L'Occitanie rassemble le plus grand volume dans les groupes region/famille : la famille B y totalise 482 evenements consommes, suivie par les familles A (434), C (431), D (418) et E (409). Les tableaux, le jeu Parquet et la figure sont generes dans `reports/artifacts/` et `reports/figures/`.

## PySpark

`src/canteen_pipeline.py` reproduit les conversions, la normalisation, la suppression des doublons exacts, les jointures gauches et l'ecriture Parquet partitionnee par annee. PySpark et le moteur Docker n'etaient pas disponibles lors de la verification ; aucune duree Spark n'est annoncee.

Apres demarrage de Docker Desktop :

```powershell
docker compose up -d
docker compose exec pyspark spark-submit src/canteen_pipeline.py
```

## Limites

- Les donnees synthetiques ne permettent pas de conclure sur une vraie cantine.
- Le statut enregistre n'est pas une verification independante de la consommation physique.
- La granularite des couts n'est pas documentee ; aucun cout par portion n'est deduit.
- Les grammages manquants ne sont pas imputes.
- Le seuil de plus de 10 portions est un indicateur exploratoire, pas une regle de rejet.
- Le traitement Spark local ne demontrerait pas a lui seul un gain de vitesse.
