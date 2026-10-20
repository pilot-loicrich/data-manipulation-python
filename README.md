# Module PMD — Préparation et Manipulation de Données (M1)

Ce projet rassemble les ateliers pratiques et pipelines de données du module PMD.

## Description
Le projet vise à explorer, nettoyer et transformer des jeux de données de ventes et de capteurs présentant des anomalies intentionnelles (valeurs manquantes, formats hétérogènes, doublons, casse instable).

## Installation
1. Cloner ou ouvrir le projet dans votre terminal.
2. Créer l'environnement virtuel : `python -m venv .venv`
3. Activer l'environnement :
   - Windows : `.\.venv\Scripts\Activate.ps1`
   - Linux/macOS : `source .venv/bin/activate`
4. Installer les dépendances : `pip install -r requirements.txt`

## Données
- Données brutes : `data/raw/` (lecture seule, générées via `python src/generate_data.py`).
- Données transformées : `data/processed/` (formats Parquet et CSV prêts pour l'analyse).
- Code réutilisable : `src/` (`generate_data.py`, `exploration.py`).

## PySpark avec Docker

Une image Jupyter avec PySpark est définie dans `compose.yml` et `docker/Dockerfile`.
Depuis la racine du projet :

```powershell
docker compose up -d
docker compose logs pyspark
```

Ouvrir `http://localhost:8888/lab` dans le navigateur. Le jeton d'accès est affiché dans les logs Jupyter. Le dossier du projet est monté dans `/workspace`.

Le notebook de la séance 7 utilise `data/raw/ventes_brutes.csv` par défaut. Pour le benchmark sur plusieurs millions de lignes, générer l'entrée facultative :

```powershell
python src/generate_data.py --big 5000000
```

Le fichier `data/raw/ventes_volumineux.csv` reste local et n'est pas versionné. Le pipeline de ventes de la séance 7 s'exécute avec :

```powershell
docker compose exec pyspark spark-submit src/spark_pipeline.py
```

Il produit un jeu Parquet partitionné par année sous `data/processed/ventes_projet_spark/`.

## Projet du groupe 1 — Bibliothèque

Les sources attribuées se trouvent dans `data/groupe_01_bibliotheque/groupe_01_bibliotheque/`.
Le pipeline de projet nettoie les événements et les enrichit avec les référentiels adhérents,
ouvrages et sites :

```powershell
docker compose exec pyspark spark-submit src/library_pipeline.py
```

Il écrit `data/processed/bibliotheque_projet_spark/`, en Parquet partitionné par année.
